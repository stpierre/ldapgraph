#!/usr/bin/perl

package Parse::OpenLDAPLog;

use strict;
use warnings;
use Carp;
use base qw(Parse::Syslog);

sub nextline {
    my ($self) = @_;
  LINE: while (my $line = $self->next()) {
      $line->[4] =~ /^conn=\d+\s
	  (?:(?:op|fd)=-?\d+\s)?
	  (SEARCH RESULT|[A-Z]*)              # operation - 1
	  \s?
	  (.*)                  # text - 2
	  $/x
	  or next LINE;
      my ($op, $text) = ($1, $2);
      $self->{'_last_data'}{$op} = [$line->[0], $op, $text];
      return $self->{'_last_data'}{$op};
  }
    return;
}

1;
