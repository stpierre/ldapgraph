#!/usr/bin/perl

package Parse::FDSlog;

use strict;
use warnings;
use Carp;
use Symbol;
use Time::Local;

my %months_map = (
    'jan' => 0, 'feb' => 1, 'mar' => 2,
    'apr' => 3, 'may' => 4, 'jun' => 5,
    'jul' => 6, 'aug' => 7, 'sep' => 8,
    'oct' => 9, 'nov' =>10, 'dec' =>11,
    );

# year-increment algorithm: if in january, if december is seen, decrement year
my $enable_year_decrement = 1;

# fast timelocal, cache minute's timestamp
# don't cache more than minute because of daylight saving time switch
my @str2time_last_minute;
my $str2time_last_minute_timestamp;
# 0: sec, 1: min, 2: h, 3: day, 4: month, 5: year

sub str2time {
    my ($sec, $min, $hour, $day, $mon, $year, $GMT) = @_;
    if (defined($str2time_last_minute[4]) and
	$str2time_last_minute[0] == $min and
	$str2time_last_minute[1] == $hour and
	$str2time_last_minute[2] == $day and
	$str2time_last_minute[3] == $mon and
	$str2time_last_minute[4] == $year) {
        return $str2time_last_minute_timestamp + $sec;
    }
    my $time;
    if ($GMT) {
        $time = timegm($sec, $min, $hour, $day, $mon, $year);
    } else {
        $time = timelocal($sec, $min, $hour, $day, $mon, $year);
    }
    @str2time_last_minute = ($min, $hour, $day, $mon, $year);
    $str2time_last_minute_timestamp = $time - $sec;
    return $time;
}

sub new {
    my ($class, $file, %data) = @_;
    carp("Parse::FDSlog is deprecated in favor of Parse::389Log");
    croak "new() requires one argument: file" unless defined $file;
    %data = () unless %data;
    if (not defined($data{'year'})) {
        $data{'year'} = (localtime())[5] + 1900;
    }
    if (ref $file eq 'File::Tail') {
        $data{'filetail'} = 1;
        $data{'file'} = $file;
    } else {
        $data{'file'} = Symbol::gensym();
        open($data{'file'}, "<", $file) or croak "can't open $file: $!";
    }
    return bless(\%data, $class);
}

sub _year_increment {
    my ($self, $mon) = @_;
    # year change
    if ($mon == 0) {
        $self->{'year'}++
	    if defined($self->{'_last_mon'}) and $self->{'_last_mon'} == 11;
        $enable_year_decrement = 1;
    } elsif($mon == 11) {
        if($enable_year_decrement) {
            $self->{'year'}--
		if defined($self->{'_last_mon'}) and $self->{'_last_mon'} != 11;
        }
    } else {
        $enable_year_decrement = 0;
    }
    $self->{'_last_mon'} = $mon;
    return;
}

sub _next_line {
    my $self = shift;
    my $f = $self->{'file'};
    if(defined $self->{'filetail'}) {
        return $f->read();
    } else {
        return <$f>;
    }
}

sub nextline {
    my ($self) = @_;
  line: while(my $str = $self->_next_line()) {
      # when FDS starts up, it generates three lines at the top of its logs
      # that aren't in the same format as the rest of the logs.  The first
      # two start with whitespace, and the third is blank.
      next if $str =~ /^\s+/;
      next if $str =~ /^$/;

      $str =~ /^
	  \[(\d+)\/(\S+)\/\d+  # date - 1, 2
	  \:
	  (\d+)\:(\d+)\:(\d+)\s+[\-\+]\d+\]  # time - 3, 4, 5
	  \s+conn=\d+\s
	  (?:(?:op|fd)=-?\d+\s)?
	  (?:(?:fd|slot)=-?\d+\s)?
	  ([A-Z]*)              # operation - 6
	  \s?
	  (.*)                  # text - 7
	  $/x
	  or do {
	      warn "WARNING: line not in FDS log format: $str";
	      next line;
      };
      my $mon = $months_map{lc($2)};
      croak "unknown month $1\n" unless defined($mon);
      $self->_year_increment($mon);

      # convert to unix time
      my $time = str2time($5, $4, $3, $1, $mon, $self->{'year'} - 1900,
			  $self->{'GMT'});
      # accept maximum one day in the present future
      if($time - time > 86400) {
	  warn "WARNING: ignoring future date in log line: $str\n";
	  next line;
      }
      my ($op, $text) = ($6, $7);
      $self->{'_last_data'}{$op} = [$time, $op, $text];
      return $self->{'_last_data'}{$op};
  }
    return;
}

1;
