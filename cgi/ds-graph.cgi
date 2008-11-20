#!/usr/bin/perl -w

# $Id$

# fedora-ds-graph -- An rrdtool-based graphing tool for Fedora DS statistics
# copyright (c) 2006-2008 Chris St. Pierre <stpierre@nebrwesleyan.edu>
# based on mailgraph copyright (c) 2000-2005 David Schweikert <dws@ee.ethz.ch>
# released under the GNU General Public License

use RRDs;
use POSIX qw(uname);

my $host = (POSIX::uname())[1];
my $scriptname = 'ds-graph.cgi';
my $xpoints = 540;
my $points_per_sample = 3;
my $ypoints = 300;
# where the RRD databases live
chomp(my $rrd_dir = `source /etc/sysconfig/ds-graph && echo \$RRD_DIR`);
my $ops_rrd = "$rrd_dir/fds_ops.rrd";
my $connxn_rrd = "$rrd_dir/fds_connxn.rrd";
my $tmp_dir = '/tmp/fedora-ds-graph'; # temporary directory to store the images

# TODO: make changeable by end user
my $aggregated = 1;

my @graphs = (
	      { title => 'Four Hour Graphs', seconds => 3600 * 4,            },
	      { title => 'Day Graphs',       seconds => 3600 * 24,           },
	      { title => 'Week Graphs',      seconds => 3600 * 24 * 7,       },
	      { title => 'Month Graphs',     seconds => 3600 * 24 * 31,      },
	      { title => 'Year Graphs',      seconds => 3600 * 24 * 365,     },
	      { title => 'Five-Year Graphs', seconds => 3600 * 24 * 365 * 5, },
	      );

my %color = (add    => '00B',
	     srch   => 'B00',
	     bind   => '0B0',
	     mod    => 'B0B',
	     del    => '0BB',
	     ext    => 'BB0',
	     cmp    => '880',
	     modrdn => '808',

	     # connections
	     plain  => 'B00',
	     ssl    => '0B0',
	     tls    => '00B',
	     sasl   => 'B0B',
	     );

sub rrd_graph(@) {
    my ($range, $file, $ypoints, $unit, @rrdargs) = @_;
    my $step = $range * $points_per_sample / $xpoints;
    # choose carefully the end otherwise rrd will maybe pick the wrong RRA:
    my $end = time;
    $end -= $end % $step;
    my $date = localtime(time);
    $date =~ s|:|\\:|g;

    my ($graphret, $xs, $ys) =
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
		    '--slope-mode',

		    @rrdargs,
		    
		    'COMMENT:['.$date.']\r',
		    );

    my $ERR=RRDs::error;
    die "ERROR: $ERR\n" if $ERR;
}

sub graph_ops($$) {
    my ($range, $file) = @_;
    my $step = $range * $points_per_sample / $xpoints;

    my (@areas, @lines);
    my @ops = qw(srch ext bind mod add del cmp modrdn);

    foreach my $op (@ops) {
	push(@areas,
	     "DEF:$op=$ops_rrd:$op:AVERAGE",
	     "DEF:m$op=$ops_rrd:$op:MAX",
	     "CDEF:d$op=$op,UN,0,$op,IF,$step,*",
	     "CDEF:s$op=PREV,UN,d$op,PREV,IF,d$op,+",
	     "AREA:$op#" . $color{$op} . ":" . substr(uc("$op    "), 0, 4) . ($aggregated ? ":STACK" : ""),
	     "GPRINT:s$op:MAX:\\t%12.0lf",
	     "GPRINT:$op:AVERAGE:\\t%6.2lf",
	     "GPRINT:m$op:MAX:\\t%6.0lf\\l",
	     );
    }

    rrd_graph($range, $file, $ypoints, "ops",
	      'COMMENT:\t\t\t    TOTAL\t\tAVERAGE\t\tMAX\l',
	      @areas,
	      @lines,

	      "CDEF:stotalr=ssrch,sbind,sext,+,+",
	      "CDEF:totalr=srch,bind,ext,+,+",
	      "CDEF:mtotalr=msrch,mbind,mext,+,+",
	      'COMMENT:  Read Ops',
	      'GPRINT:stotalr:MAX:  %12.0lf',
	      'GPRINT:totalr:AVERAGE:\t%6.2lf',
	      'GPRINT:mtotalr:MAX:\t%6.0lf\l',

	      "CDEF:stotalw=smod,sadd,sdel,+,+",
	      "CDEF:totalw=mod,add,del,+,+",
	      "CDEF:mtotalw=mmod,madd,mdel,+,+",
	      'COMMENT:  Write Ops',
	      'GPRINT:stotalw:MAX: %12.0lf',
	      'GPRINT:totalw:AVERAGE:\t%6.2lf',
	      'GPRINT:mtotalw:MAX:\t%6.0lf\l',

	      "CDEF:stotal=stotalr,stotalw,+",
	      "CDEF:total=totalr,totalw,+",
	      "CDEF:mtotal=mtotalr,mtotalw,+",
	      'COMMENT:  Total Ops',
	      'GPRINT:stotal:MAX: %12.0lf',
	      'GPRINT:total:AVERAGE:\t%6.2lf',
	      'GPRINT:mtotal:MAX:\t%6.0lf\l',
	      );
}

sub graph_connxn($$) {
    my ($range, $file) = @_;
    my $step = $range * $points_per_sample / $xpoints;

    my (@areas, @lines);
    my %types = (tls    => "TLS      ",
		 ssl    => "SSL      ",
		 sasl   => "SASL     ",
		 );

    foreach my $type (keys(%types)) {
	push(@areas,
	     "DEF:$type=$connxn_rrd:$type:AVERAGE",
	     "DEF:m$type=$connxn_rrd:$type:MAX",
	     "CDEF:d$type=$type,UN,0,$type,IF,$step,*",
	     "CDEF:s$type=PREV,UN,d$type,PREV,IF,d$type,+",
	     "AREA:$type#" . $color{$type} . ":" . $types{$type} . ($aggregated ? ":STACK" : ""),
	     "GPRINT:s$type:MAX:\\t%12.0lf",
	     "GPRINT:$type:AVERAGE:\\t%6.2lf",
	     "GPRINT:m$type:MAX:\\t%6.0lf\\l",
	     );

	push(@lines,
	     "CDEF:n$type=$type,-1,*",
	     "LINE2:n$type#" . $color{$type},
	     );
    }

    push(@areas,
	 "DEF:connxn=$connxn_rrd:connxn:AVERAGE",
	 "DEF:mconnxn=$connxn_rrd:connxn:MAX",
	 "CDEF:dconnxn=connxn,UN,0,connxn,IF,$step,*",
	 "CDEF:sconnxn=PREV,UN,dconnxn,PREV,IF,dconnxn,+",

	 "CDEF:plain=connxn,tls,sasl,-,-",
	 "CDEF:mplain=mconnxn,mtls,sasl,-,-",
	 "CDEF:dplain=dconnxn,dtls,sasl,-,-",
	 "CDEF:splain=sconnxn,stls,sasl,-,-",

	 "AREA:plain#" . $color{plain} . ":Plaintext:" . ($aggregated ? "STACK" : ""),
	 "GPRINT:splain:MAX:\\t%12.0lf",
	 "GPRINT:plain:AVERAGE:\\t%6.2lf",
	 "GPRINT:mplain:MAX:\\t%6.0lf\\l",
	 );

	push(@lines,
	     "CDEF:nplain=plain,-1,*",
	     "LINE2:nplain#" . $color{'plain'},
	     );

    rrd_graph($range, $file, $ypoints, "connections",
	      'COMMENT:\t\t\t\t   TOTAL\t\tAVERAGE\t\tMAX\l',
	      @areas,
	      @lines,

	      "CDEF:stotals=stls,sssl,+",
	      "CDEF:totals=tls,ssl,+",
	      "CDEF:mtotals=mtls,mssl,+",
	      'COMMENT:  Total Secure',
	      'GPRINT:stotals:MAX:   %12.0lf',
	      'GPRINT:totals:AVERAGE:\t%6.2lf',
	      'GPRINT:mtotals:MAX:\t%6.0lf\l',

	      "CDEF:stotal=stotals,splain,+",
	      "CDEF:total=totals,plain,+",
	      "CDEF:mtotal=mtotals,mplain,+",
	      'COMMENT:  Total Conns',
	      'GPRINT:stotal:MAX:    %12.0lf',
	      'GPRINT:total:AVERAGE:\t%6.2lf',
	      'GPRINT:mtotal:MAX:\t%6.0lf\l',

	      );
}

sub print_html() {
    print "Content-Type: text/html\n\n";

    print <<HEADER;
<!doctype html public "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
<html>
  <head>
    <title>LDAP Statistics for $host</title>
    <meta http-equiv="Refresh" content="300" />
    <meta http-equiv="Pragma" content="no-cache" />
    <link rel="stylesheet" href="./ds-graph.css" type="text/css" />
    <script language="JavaScript"><!--
      function toggle(id) {
         var obj = document.getElementById(id);
	 if (obj.style.display == 'inline') {
	    obj.style.display = 'none';
	 } else {
	    obj.style.display = 'inline';
         }
      }
    //--></script>
  </head>
  <body>
    <div class="header">LDAP Statistics for $host</div>
HEADER
;
    my $id = 0;
    for my $n (0..$#graphs) {
	print "<div class='graph-box'>\n";
	print "<div class='graph-header'>" . $graphs[$n]{'title'} . "</div>\n";
	print "<div class='show-hide'><a href='javascript: toggle(" . $id .
	    "); toggle(" . ($id + 1) . ");'>Show/hide</a></div>\n";
	print "<img src='" . $scriptname . "?" . $n . "-n' id='" . $id++ .
	    "' border='0' class='graph-image' />\n";
	print "<img src='" . $scriptname . "?" . $n . "-e' id='" . $id++ .
	    "' border='0' class='graph-image' />\n";
	print "</div>\n";
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
