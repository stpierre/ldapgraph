#!/usr/bin/perl -w

# fdsgraph -- An rrdtool-based graphing tool for Fedora DS statistics
# copyright (c) 2006-2007 Chris St. Pierre <stpierre@nebrwesleyan.edu>
# based on mailgraph copyright (c) 2000-2005 David Schweikert <dws@ee.ethz.ch>
# released under the GNU General Public License

use RRDs;
use POSIX qw(uname);

my $host = (POSIX::uname())[1];
my $scriptname = 'fdsgraph.cgi';
my $xpoints = 540;
my $points_per_sample = 3;
my $ypoints = 160;
# where the RRD databases live
my $ops_rrd = '/var/lib/fdsgraph/fds_ops.rrd';
my $connxn_rrd = '/var/lib/fdsgraph/fds_connxn.rrd';
my $tmp_dir = '/tmp/fdsgraph'; # temporary directory where to store the images

my @graphs = (
	      { title => 'Day Graphs',   seconds => 3600*24,        },
	      { title => 'Week Graphs',  seconds => 3600*24*7,      },
	      { title => 'Month Graphs', seconds => 3600*24*31,     },
	      { title => 'Year Graphs',  seconds => 3600*24*365, },
	      );

my %color = (add    => '0000AA',
	     srch   => 'AA0000',
	     bind   => '00AA00',
	     mod    => 'AA00AA',
	     del    => '00AAAA',
	     ext    => 'AAAA00',
	     connxn => 'AA0000',
	     ssl    => '00AA00',
	     tls    => '0000AA',
	     );

sub rrd_graph(@) {
    my ($range, $file, $ypoints, $unit, @rrdargs) = @_;
    my $step = $range*$points_per_sample/$xpoints;
    # choose carefully the end otherwise rrd will maybe pick the wrong RRA:
    my $end  = time; $end -= $end % $step;
    my $date = localtime(time);
    $date =~ s|:|\\:|g unless $RRDs::VERSION < 1.199908;

    my ($graphret,$xs,$ys) =
	RRDs::graph($file,
		    '--imgformat', 'PNG',
		    '--width', $xpoints,
		    '--height', $ypoints,
		    '--start', "-$range",
		    '--end', $end,
		    '--vertical-label', $unit . '/min',
		    '--lower-limit', 0,
		    '--units-exponent', 0, # don't show milli-messages/s
		    '--lazy',
		    '--color', 'SHADEA#ffffff',
		    '--color', 'SHADEB#ffffff',
		    '--color', 'BACK#ffffff',
		    
		    $RRDs::VERSION < 1.2002 ? () : (
						    '--slope-mode'
						    ),
		    
		    @rrdargs,
		    
		    'COMMENT:['.$date.']\r',
		    );

    my $ERR=RRDs::error;
    die "ERROR: $ERR\n" if $ERR;
}

sub graph_ops($$) {
    my ($range, $file) = @_;
    my $step = $range * $points_per_sample / $xpoints;
    rrd_graph($range, $file, $ypoints, "ops",
	      "DEF:srch=$ops_rrd:srch:AVERAGE",
	      "DEF:msrch=$ops_rrd:srch:MAX",
	      "CDEF:dsrch=srch,UN,0,srch,IF,$step,*",
	      "CDEF:ssrch=PREV,UN,dsrch,PREV,IF,dsrch,+",
	      "LINE2:srch#$color{srch}:SRCH",
	      'GPRINT:ssrch:MAX:total\: %8.0lf ops',
	      'GPRINT:srch:AVERAGE:avg\: %5.2lf ops/min',
	      'GPRINT:msrch:MAX:max\: %4.0lf ops/min\l',

	      "DEF:bind=$ops_rrd:bind:AVERAGE",
	      "DEF:mbind=$ops_rrd:bind:MAX",
	      "CDEF:dbind=bind,UN,0,bind,IF,$step,*",
	      "CDEF:sbind=PREV,UN,dbind,PREV,IF,dbind,+",
	      "LINE2:bind#$color{bind}:BIND",
	      'GPRINT:sbind:MAX:total\: %8.0lf ops',
	      'GPRINT:bind:AVERAGE:avg\: %5.2lf ops/min',
	      'GPRINT:mbind:MAX:max\: %4.0lf ops/min\l',

	      "DEF:ext=$ops_rrd:ext:AVERAGE",
	      "DEF:mext=$ops_rrd:ext:MAX",
	      "CDEF:dext=ext,UN,0,ext,IF,$step,*",
	      "CDEF:sext=PREV,UN,dext,PREV,IF,dext,+",
	      "LINE2:ext#$color{ext}:EXT ",
	      'GPRINT:sext:MAX:total\: %8.0lf ops',
	      'GPRINT:ext:AVERAGE:avg\: %5.2lf ops/min',
	      'GPRINT:mext:MAX:max\: %4.0lf ops/min\l',

	      "DEF:mod=$ops_rrd:mod:AVERAGE",
	      "DEF:mmod=$ops_rrd:mod:MAX",
	      "CDEF:dmod=mod,UN,0,mod,IF,$step,*",
	      "CDEF:smod=PREV,UN,dmod,PREV,IF,dmod,+",
	      "LINE2:mod#$color{mod}:MOD ",
	      'GPRINT:smod:MAX:total\: %8.0lf ops',
	      'GPRINT:mod:AVERAGE:avg\: %5.2lf ops/min',
	      'GPRINT:mmod:MAX:max\: %4.0lf ops/min\l',

	      "DEF:add=$ops_rrd:add:AVERAGE",
	      "DEF:madd=$ops_rrd:add:MAX",
	      "CDEF:dadd=add,UN,0,add,IF,$step,*",
	      "CDEF:sadd=PREV,UN,dadd,PREV,IF,dadd,+",
	      "LINE2:add#$color{add}:ADD ",
	      'GPRINT:sadd:MAX:total\: %8.0lf ops',
	      'GPRINT:add:AVERAGE:avg\: %5.2lf ops/min',
	      'GPRINT:madd:MAX:max\: %4.0lf ops/min\l',

	      "DEF:del=$ops_rrd:del:AVERAGE",
	      "DEF:mdel=$ops_rrd:del:MAX",
	      "CDEF:ddel=del,UN,0,del,IF,$step,*",
	      "CDEF:sdel=PREV,UN,ddel,PREV,IF,ddel,+",
	      "LINE2:del#$color{del}:DEL ",
	      'GPRINT:sdel:MAX:total\: %8.0lf ops',
	      'GPRINT:del:AVERAGE:avg\: %5.2lf ops/min',
	      'GPRINT:mdel:MAX:max\: %4.0lf ops/min\l',
	      );
}

sub graph_connxn($$) {
    my ($range, $file) = @_;
    my $step = $range * $points_per_sample / $xpoints;
    rrd_graph($range, $file, $ypoints, "connections",
	      "DEF:connxn=$connxn_rrd:connxn:AVERAGE",
	      "DEF:mconnxn=$connxn_rrd:connxn:MAX",
	      "CDEF:dconnxn=connxn,UN,0,connxn,IF,$step,*",
	      "CDEF:sconnxn=PREV,UN,dconnxn,PREV,IF,dconnxn,+",
	      "LINE2:connxn#$color{connxn}:Plaintext Conns",
	      'GPRINT:sconnxn:MAX:total\: %8.0lf conns',
	      'GPRINT:connxn:AVERAGE:avg\: %5.2lf conns/min',
	      'GPRINT:mconnxn:MAX:max\: %4.0lf conns/min\l',

	      "DEF:ssl=$connxn_rrd:ssl:AVERAGE",
	      "DEF:mssl=$connxn_rrd:ssl:MAX",
	      "CDEF:dssl=ssl,UN,0,ssl,IF,$step,*",
	      "CDEF:sssl=PREV,UN,dssl,PREV,IF,dssl,+",
	      "LINE2:ssl#$color{ssl}:SSL Conns  ",
	      'GPRINT:sssl:MAX:total\: %8.0lf conns',
	      'GPRINT:ssl:AVERAGE:avg\: %5.2lf conns/min',
	      'GPRINT:mssl:MAX:max\: %4.0lf conns/min\l',

	      "DEF:tls=$connxn_rrd:tls:AVERAGE",
	      "DEF:mtls=$connxn_rrd:tls:MAX",
	      "CDEF:dtls=tls,UN,0,tls,IF,$step,*",
	      "CDEF:stls=PREV,UN,dtls,PREV,IF,dtls,+",
	      "LINE2:tls#$color{tls}:TLS Conns  ",
	      'GPRINT:stls:MAX:total\: %8.0lf conns',
	      'GPRINT:tls:AVERAGE:avg\: %5.2lf conns/min',
	      'GPRINT:mtls:MAX:max\: %4.0lf conns/min\l'
	      );
}

sub print_html() {
    print "Content-Type: text/html\n\n";

    print <<HEADER;
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
	<HTML>
	<HEAD>
	<TITLE>LDAP Statistics for $host</TITLE>
	<META HTTP-EQUIV="Refresh" CONTENT="300">
	<META HTTP-EQUIV="Pragma" CONTENT="no-cache">
	</HEAD>
	<BODY BGCOLOR="#FFFFFF">
HEADER

	print "<H1>LDAP Statistics for $host</H1>\n";
    for my $n (0..$#graphs) {
	print '<div style="background: #dddddd; width: 632px">';
	print "<H2>$graphs[$n]{title}</H2>\n";
	print "</div>\n";
	print "<P><IMG BORDER=\"0\" SRC=\"$scriptname?${n}-n\" ALT=\"fdsgraph\">\n";
	print "<P><IMG BORDER=\"0\" SRC=\"$scriptname?${n}-e\" ALT=\"fdsgraph\">\n";
    }

    print <<FOOTER;
    <hr width="630" align="left" size="1" noshade>
	<table border="0" width="630" cellpadding="0" cellspacing="0" background="#dddddd"><tr><td align="left">
	<td ALIGN="right">
	<a HREF="http://people.ee.ethz.ch/~oetiker/webtools/rrdtool/"><img border="0" src="http://people.ethz.ch/~oetiker/webtools/rrdtool/.pics/rrdtool.gif" alt="" width="120" height="34"></a>
	</td></tr></table>
	</BODY></HTML>
FOOTER
    }

sub send_image($) {
    my ($file)= @_;

    -r $file or do {
	print "Content-type: text/plain\n\nERROR: can't find $file\n";
	exit 1;
    };

    print "Content-type: image/png\n";
    print "Content-length: ".((stat($file))[7])."\n";
    print "\n";
    open(IMG, $file) or die;
    my $data;
    print $data while read(IMG, $data, 16384)>0;
}

sub main() {
    my $uri = $ENV{REQUEST_URI} || '';
    $uri =~ s/\/[^\/]+$//;
    $uri =~ s/\//,/g;
    $uri =~ s/(\~|\%7E)/tilde,/g;
    mkdir $tmp_dir, 0777 unless -d $tmp_dir;
    mkdir "$tmp_dir/$uri", 0777 unless -d "$tmp_dir/$uri";

    my $img = $ENV{QUERY_STRING};
    if(defined $img and $img =~ /\S/) {
	if ($img =~ /^(\d+)-n$/) {
	    my $file = "$tmp_dir/$uri/fds_ops_$1.png";
	    graph_ops($graphs[$1]{seconds}, $file);
	    send_image($file);
	} elsif ($img =~ /^(\d+)-e$/) {
	    my $file = "$tmp_dir/$uri/fds_connxn_$1.png";
	    graph_connxn($graphs[$1]{seconds}, $file);
	    send_image($file);
	} else {
	    die "ERROR: invalid argument\n";
	}
    }
    else {
	print_html;
    }
}

main;
