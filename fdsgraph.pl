#!/usr/bin/perl -w

# fdsgraph -- an rrdtool frontend for Fedora DS statistics

######## Parse::FDSlog 0.1b ########
package Parse::FDSlog;
use Carp;
use Symbol;
use Time::Local;
use strict;
use vars qw($VERSION);
my %months_map = (
		  'Jan' => 0, 'Feb' => 1, 'Mar' => 2,
		  'Apr' => 3, 'May' => 4, 'Jun' => 5,
		  'Jul' => 6, 'Aug' => 7, 'Sep' => 8,
		  'Oct' => 9, 'Nov' =>10, 'Dec' =>11,
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

sub str2time($$$$$$$) {
    my $GMT = pop @_;
    if(defined $str2time_last_minute[4] and
       $str2time_last_minute[0] == $_[1] and
       $str2time_last_minute[1] == $_[2] and
       $str2time_last_minute[2] == $_[3] and
       $str2time_last_minute[3] == $_[4] and
       $str2time_last_minute[4] == $_[5])
    {
        return $str2time_last_minute_timestamp + $_[0];
    }
    my $time;
    if($GMT) {
        $time = timegm(@_);
    }
    else {
        $time = timelocal(@_);
    }
    @str2time_last_minute = @_[1..5];
    $str2time_last_minute_timestamp = $time-$_[0];
    return $time;
}

sub _use_locale($) {
    use POSIX qw(locale_h strftime);
    my $old_locale = setlocale(LC_TIME);
    for my $locale (@_) {
        croak "new(): wrong 'locale' value: '$locale'" unless setlocale(LC_TIME, $locale);
        for my $month (0..11) {
            $months_map{strftime("%b", 0, 0, 0, 1, $month, 96)} = $month;
        }
    }
    setlocale(LC_TIME, $old_locale);
}

sub new($$;%) {
    my ($class, $file, %data) = @_;
    croak "new() requires one argument: file" unless defined $file;
    %data = () unless %data;
    if(not defined $data{year}) {
        $data{year} = (localtime(time))[5]+1900;
    }
    $data{type} = 'syslog' unless defined $data{type};
    $data{_repeat} = 0;
    if(ref $file eq 'File::Tail') {
        $data{filetail} = 1;
        $data{file} = $file;
    }
    else {
        $data{file}=gensym;
        open($data{file}, "<$file") or croak "can't open $file: $!";
    }
    if(defined $data{locale}) {
        if(ref $data{locale} eq 'ARRAY') {
            _use_locale @{$data{locale}};
        }
        elsif(ref $data{locale} eq '') {
            _use_locale $data{locale};
        }
        else {
            croak "'locale' parameter must be scalar or array of scalars";
        }
    }
    return bless \%data, $class;
}

sub _year_increment($$) {
    my ($self, $mon) = @_;
    # year change
    if($mon==0) {
        $self->{year}++ if defined $self->{_last_mon} and $self->{_last_mon} == 11;
        $enable_year_decrement = 1;
    }
    elsif($mon == 11) {
        if($enable_year_decrement) {
            $self->{year}-- if defined $self->{_last_mon} and $self->{_last_mon} != 11;
        }
    }
    else {
        $enable_year_decrement = 0;
    }
    $self->{_last_mon} = $mon;
}

sub _next_line($) {
    my $self = shift;
    my $f = $self->{file};
    if(defined $self->{filetail}) {
        return $f->read;
    }
    else {
        return <$f>;
    }
}

sub next($) {
    my ($self) = @_;
    while($self->{_repeat}>0) {
        $self->{_repeat}--;
        return $self->{_repeat_data};
    }
  line: while(my $str = $self->_next_line()) {
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
	  $/x or do
      {
	  warn "WARNING: line not in FDS log format: $str";
	  next line;
      };
      my $mon = $months_map{$2};
      defined $mon or croak "unknown month $1\n";
      $self->_year_increment($mon);
      # convert to unix time
      my $time = str2time($5, $4, $3, $1, $mon, $self->{year}-1900,
			  $self->{GMT});
      if (not $self->{allow_future}) {
	  # accept maximum one day in the present future
	  if($time - time > 86400) {
	      warn "WARNING: ignoring future date in log line: $str";
	      next line;
	  }
      }
      my ($op, $text) = ($6, $7);
      if($self->{arrayref}) {
	  $self->{_last_data}{$op} = [
				      $time,  # 0: timestamp 
				      $op,    # 1: op
				      $text,  # 2: text
				      ];
      } else {
	  $self->{_last_data}{$op} = {
	      timestamp => $time,
	      op        => $op,
	      text      => $text,
	  };
      }
      return $self->{_last_data}{$op};
  }
    return undef;
}

#####################################################################
#####################################################################
#####################################################################

use RRDs;

use strict;
use File::Tail;
use Getopt::Long;
use POSIX 'setsid';
use Sys::Hostname;

my $VERSION = "1.12";

# config
my $rrdstep = 60;
my $xpoints = 540;
my $points_per_sample = 3;

my $daemon_logfile = '/var/log/fdsgraph.log';
my $daemon_pidfile = '/var/run/fdsgraph.pid';
my $daemon_rrd_dir = '/var/log';

# global variables
my $hostname = (split(/\./, hostname()))[0];
my $logfile = "/opt/fedora-ds/slapd-$hostname/logs/access";
my $ops_rrd = "fds_ops.rrd";
my $connxn_rrd = "fds_connxn.rrd";
my $year;
my $this_minute;
my %sum = ( add => 0, srch => 0, bind => 0, mod => 0, del => 0, ext => 0,
	    connxn => 0, ssl => 0);
my $rrd_inited=0;

my %opt = ();

# prototypes
sub daemonize();
sub process_line($);
sub init_rrd($);
sub update($);

sub usage {
    print "usage: fdsgraph [*options*]\n\n";
    print "  -h, --help         display this help and exit\n";
    print "  -V, --version      output version information and exit\n";
    print "  -l, --logfile=FILE monitor FILE instead of $logfile\n";
    print "  -y, --year         starting year of the log file (default: current year)\n";
    print "  -d, --daemon       start in the background\n";
    print "  --daemon-pid=FILE  write PID to FILE instead of /var/run/fdsgraph.pid\n";
    print "  --daemon-rrd=DIR   write RRDs to DIR instead of .\n";
    print "  --daemon-log=FILE  write verbose-log to FILE instead of /var/log/fdsgraph.log\n";

    exit;
}

sub main {
    Getopt::Long::Configure('no_ignore_case');
    GetOptions(\%opt, 'help|h', 'logfile|l=s', 'year|y=i', 'daemon|d!',
	       'daemon_pid|daemon-pid=s', 'daemon_rrd|daemon-rrd=s',
	       'daemon_log|daemon-log=s'
	       ) or exit(1);
    usage() if $opt{help};
      
    $daemon_pidfile = $opt{daemon_pid} if defined $opt{daemon_pid};
      $daemon_logfile = $opt{daemon_log} if defined $opt{daemon_log};
      $daemon_rrd_dir = $opt{daemon_rrd} if defined $opt{daemon_rrd};

      if($opt{daemon} or $opt{daemon_rrd}) {
	  chdir $daemon_rrd_dir or die "fdsgraph: can't chdir to $daemon_rrd_dir: $!";
	  -w $daemon_rrd_dir or die "fdsgraph: can't write to $daemon_rrd_dir\n";
      }

      daemonize if $opt{daemon};

      $logfile = $opt{logfile} if $opt{logfile};
      my $file;
      $file = File::Tail->new(name => $logfile, tail => -1);
      my $parser = new Parse::FDSlog($file, year => $opt{year}, arrayref => 1);

      while(my $sl = $parser->next) {
	  process_line($sl);
      }
  }

sub daemonize() {
    open STDIN, '/dev/null' or die "fdsgraph: can't read /dev/null: $!";
    open STDOUT, '>/dev/null' or die "fdsgraph: can't write to /dev/null: $!";
    defined(my $pid = fork) or die "fdsgraph: can't fork: $!";
    if($pid) {
	# parent
	open PIDFILE, ">$daemon_pidfile"
	    or die "fdsgraph: can't write to $daemon_pidfile: $!\n";
	print PIDFILE "$pid\n";
	close(PIDFILE);
	exit;
    }
    # child
    setsid or die "fdsgraph: can't start a new session: $!";
    open STDERR, '>&STDOUT' or die "fdsgraph: can't dup stdout: $!";
}

sub init_rrd($) {
    my $m = shift;
    my $rows = $xpoints/$points_per_sample;
    my $realrows = int($rows*1.1); # ensure that the full range is covered
    my $day_steps = int(3600*24 / ($rrdstep*$rows));
    # use multiples, otherwise rrdtool could choose the wrong RRA
    my $week_steps = $day_steps*7;
    my $month_steps = $week_steps*5;
    my $year_steps = $month_steps*12;

    if(! -f $ops_rrd) {
	RRDs::create($ops_rrd, '--start', $m, '--step', $rrdstep,
		     'DS:add:GAUGE:' . ($rrdstep*2) . ':0:U',
		     'DS:srch:GAUGE:' . ($rrdstep*2) . ':0:U',
		     'DS:bind:GAUGE:' . ($rrdstep*2) . ':0:U',
		     'DS:mod:GAUGE:' . ($rrdstep*2) . ':0:U',
		     'DS:del:GAUGE:' . ($rrdstep*2) . ':0:U',
		     'DS:ext:GAUGE:' . ($rrdstep*2) . ':0:U',
		     "RRA:AVERAGE:0.5:$day_steps:$realrows",   # day
		     "RRA:AVERAGE:0.5:$week_steps:$realrows",  # week
		     "RRA:AVERAGE:0.5:$month_steps:$realrows", # month
		     "RRA:AVERAGE:0.5:$year_steps:$realrows",  # year
		     "RRA:MAX:0.5:$day_steps:$realrows",   # day
		     "RRA:MAX:0.5:$week_steps:$realrows",  # week
		     "RRA:MAX:0.5:$month_steps:$realrows", # month
		     "RRA:MAX:0.5:$year_steps:$realrows",  # year
		     );
	  my $err = RRDs::error;
	  warn "create of $ops_rrd failed: $err\n" if $err;
	  $this_minute = $m;
      } elsif(-f $ops_rrd) {
	  $this_minute = RRDs::last($ops_rrd) + $rrdstep;
      }    

    if(! -f $connxn_rrd) {
	RRDs::create($connxn_rrd, '--start', $m, '--step', $rrdstep,
		     'DS:connxn:GAUGE:' . ($rrdstep * 2) . ':0:U',
		     'DS:ssl:GAUGE:' . ($rrdstep * 2) . ':0:U',
		     "RRA:AVERAGE:0.5:$day_steps:$realrows",   # day
		     "RRA:AVERAGE:0.5:$week_steps:$realrows",  # week
		     "RRA:AVERAGE:0.5:$month_steps:$realrows", # month
		     "RRA:AVERAGE:0.5:$year_steps:$realrows",  # year
		     "RRA:MAX:0.5:$day_steps:$realrows",   # day
		     "RRA:MAX:0.5:$week_steps:$realrows",  # week
		     "RRA:MAX:0.5:$month_steps:$realrows", # month
		     "RRA:MAX:0.5:$year_steps:$realrows",  # year
		     );
	  my $err = RRDs::error;
	  warn "create of $connxn_rrd failed: $err\n" if $err;
	  $this_minute = $m;
      } elsif(-f $connxn_rrd) {
	  $this_minute = RRDs::last($connxn_rrd) + $rrdstep;
      }

    $rrd_inited = 1;
}

sub process_line($) {
    my $sl = shift;
    my $time = $sl->[0];
    my $op = $sl->[1];
    my $text = $sl->[2];

    if ($op) {
	if ($op =~ /^SSL|ADD|SRCH|BIND|MOD|DEL|EXT$/) {
	    event($time, lc($op));
	}
    } else { # either a connect or disconnect
	if ($text =~ /^connection from/) {
	    event($time, 'connxn');
	}
    }
}

sub event($$) {
    my ($t, $type) = @_;
    update($t) and $sum{$type}++;
}

# returns 1 if $sum should be updated
sub update($) {
    my $t = shift;
    my $m = $t - $t%$rrdstep;
    init_rrd($m) unless $rrd_inited;
    return 1 if $m == $this_minute;
    return 0 if $m < $this_minute;

    RRDs::update $ops_rrd, "$this_minute:$sum{add}:$sum{srch}:$sum{bind}:$sum{mod}:$sum{del}:$sum{ext}";
    my $err = RRDs::error;
    warn "update of $ops_rrd failed: $err\n" if $err;

    RRDs::update $connxn_rrd, "$this_minute:$sum{connxn}:$sum{ssl}";
    $err = RRDs::error;
    warn "update of $connxn_rrd failed: $err\n" if $err;

    if ($m > $this_minute+$rrdstep) {
	for(my $sm = $this_minute + $rrdstep; $sm < $m; $sm += $rrdstep) {
	    RRDs::update $ops_rrd, "$sm:0:0:0:0";
	      RRDs::update $connxn_rrd, "$sm:0:0";
	  }
    }
    $this_minute = $m;
    $sum{add} = 0;
    $sum{srch} = 0;
    $sum{bind} = 0;
    $sum{mod} = 0;
    $sum{del} = 0;
    $sum{ext} = 0;
    $sum{connxn} = 0;
    $sum{ssl} = 0;
    return 1;
}

main;
