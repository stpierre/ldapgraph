#!/usr/bin/perl

# ldapgraph -- An rrdtool-based graphing tool for LDAP server statistics
# copyright (c) 2006-2011 Chris St. Pierre <chris.a.st.pierre@gmail.com>
# based on mailgraph copyright (c) 2000-2005 David Schweikert <dws@ee.ethz.ch>
# released under the GNU General Public License

use warnings;
use strict;
use RRDs;
use POSIX qw(uname);
use CGI::Pretty;

my $host = (POSIX::uname())[1];
my $scriptname = 'ldapgraph.cgi';
my $xpoints = 540;
my $points_per_sample = 3;
my $ypoints = 300;
# where the RRD databases live
chomp(my $rrd_dir = `source /etc/sysconfig/ldapgraph && echo \$RRD_DIR`);
my $ops_rrd = "$rrd_dir/fds_ops.rrd";
my $connxn_rrd = "$rrd_dir/fds_connxn.rrd";
my $tmp_dir = '/tmp/ldapgraph'; # temporary directory to store the images

my %graphs = (3600 * 4            => 'Four-Hour Graphs',
	      3600 * 24           => 'Day Graphs',
	      3600 * 24 * 7       => 'Week Graphs',
	      3600 * 24 * 31      => 'Month Graphs',
	      3600 * 24 * 365     => 'Year Graphs',
	      3600 * 24 * 365 * 5 => 'Five-Year Graphs');

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


my $uri = $ENV{'REQUEST_URI'} || '';
$uri =~ s/\/[^\/]+$//;
$uri =~ s/\//,/g;
$uri =~ s/(\~|\%7E)/tilde,/g;
mkdir $tmp_dir, 0777 unless -d $tmp_dir;
mkdir "$tmp_dir/$uri", 0777 unless -d "$tmp_dir/$uri";

my $cgi = new CGI();

if ($cgi->param('type') && $cgi->param('time') &&
    defined($graphs{$cgi->param('time')})) {
    my %graphopts;
    $graphopts{'stacked'} = ($cgi->cookie('graphtype') eq 'Stacked' ? 1 : 0);
    $graphopts{'logarithmic'} = ($cgi->cookie('graphscale') eq 'Logarithmic' ? 1 : 0);

    my $file = "$tmp_dir/$uri/fds_" . $cgi->param('type') . '_' .
	$cgi->param('time') . '_' . $graphopts{'stacked'} . $graphopts{'logarithmic'} . ".png";
    graph($cgi->param('type'), $cgi->param('time'), $file, \%graphopts);
    send_image($file);
} else {
    my @cookies;
    if ($cgi->param('submit')) { # options were submitted
	if (my $type = $cgi->param('type')) {
	    push(@cookies, $cgi->cookie(-name => 'graphtype',
					-value => $type));
	}
	
	if (my $scale = $cgi->param('scale')) {
	    push(@cookies, $cgi->cookie(-name => 'graphscale',
					-value => $scale));
	}
	
	if (my @display = $cgi->param('display')) {
	    my %display;
	    foreach my $d (@display) {
		$display{$d} = 1;
	    }
	    
	    push(@cookies, $cgi->cookie(-name => 'graphdisplay',
					-value => \%display));
	}
    }

    my $jstoggle = <<EOJS;
    function toggle(id) {
	var obj = document.getElementById(id);
	var disp = (id == 'opts' ? 'block' : 'inline');
	if (obj.style.display == disp) {
	    obj.style.display = 'none';
	} else {
	    obj.style.display = disp;
	}
    }
EOJS

    print $cgi->header(-cookie => [@cookies]);
    print $cgi->start_html(-title  => "LDAP Statistics for $host",
			   -style  => {src => "../ldapgraph.css"},
			   -script => $jstoggle,
			   -head   => [$cgi->meta({-http_equiv => 'Refresh',
						   -content    => '300'}),
				       $cgi->meta({-http_equiv => 'Pragma',
						   -content    => 'no-cache'})]);
    print $cgi->div({-class => 'header'},
		    "LDAP Statistics for $host" .
		    $cgi->div({-class => "options-link"},
			      $cgi->a({-href => "javascript: toggle('opts');"},
				      "Options")));

    my %display = $cgi->cookie('graphdisplay');
    my $id = 0;
    foreach my $seconds (sort { $a <=> $b } keys(%graphs)) {
	print $cgi->div({-class => 'graph-box'},
			$cgi->div({-class => 'graph-header'},
				  $graphs{$seconds}),
			$cgi->div({-class => 'show-hide'},
				  $cgi->a({-href => "javascript: toggle(" . $id . "); toggle(" . ($id + 1) . ");"},
					  "Show/hide")),
			$cgi->img({-src    => $scriptname . "?type=ops&time=" . $seconds,
				   -id     => $id++,
				   -border => 0,
				   -class  => "graph-image",
				   -style  => ($display{$seconds} ? "display: inline;" : '')}),
			$cgi->img({-src    => $scriptname . "?type=connxn&time=" . $seconds,
				   -id     => $id++,
				   -border => 0,
				   -class  => "graph-image",
				   -style  => ($display{$seconds} ? "display: inline;" : '')}));
    }

    print $cgi->a({-href => "http://oss.oetiker.ch/rrdtool/"},
		  $cgi->img({-src => "../rrdtool.png",
			     -border => 0,
			     -width => 128,
			     -height => 48}));

    print $cgi->div({-class => 'options',
		     -id    => 'opts'},
		    $cgi->div({-class => 'header'},
			      "Options" .
			      $cgi->div({-class => "options-link"},
					$cgi->a({-href => "javascript: toggle('opts');"},
						"Close"))) .
		    $cgi->start_form(-method   => 'POST',
				     -action   => $scriptname,
				     -encoding => CGI::URL_ENCODED()) .
		    $cgi->label({-for => 'type'}, "Graph Type") .
		    $cgi->popup_menu(-name    => 'type',
				     -values  => [qw(Stacked Unstacked)],
				     -default => 'Stacked') .
		    $cgi->label({-for => 'scale'}, "Graph Scale") .
		    $cgi->popup_menu(-name    => 'scale',
				     -values  => [qw(Logarithmic Linear)],
				     -default => 'Logarithmic') .
		    $cgi->label({-for => 'display'}, "Default Display") .
		    $cgi->scrolling_list(-name     => 'display',
					 -values   => [sort { $a <=> $b } keys(%graphs)],
					 -labels   => \%graphs,
					 -default  => 3600 * 4,
					 -size     => scalar(keys(%graphs)),
					 -multiple => 'true') .
		    $cgi->submit(-name  => 'submit',
				 -class => 'button',
				 -value => 'Save Options') .
		    $cgi->endform());

    print $cgi->end_html();
;
}

##################################################

sub rrd_graph {
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
		    '--lower-limit', 1,
		    '--units-exponent', 0, # don't show milli-messages/s
		    '--units=si',
		    '--lazy',
		    '--color', 'SHADEA#ffffff',
		    '--color', 'SHADEB#ffffff',
		    '--color', 'BACK#ffffff',
		    ($RRDs::VERSION >= 1.3 ? '--full-size-mode' : ()),

		    @rrdargs,
		    
		    'COMMENT:['.$date.']\r',
		    );

    die "ERROR: " . RRDs::error() . "\n" if RRDs::error();
    return;
}

sub graph {
    my ($type, $range, $file, $opts) = @_;
    if ($type eq 'ops') {
	return graph_ops($range, $file, $opts);
    } elsif ($type eq 'connxn') {
	return graph_connxn($range, $file, $opts);
    } else {
	die "Error: Invalid graph type $type\n";
    }
}

sub graph_ops {
    my ($range, $file, $opts) = @_;
    my $step = $range * $points_per_sample / $xpoints;

    my @plots;
    my @ops = qw(srch ext bind mod add del cmp modrdn);

    foreach my $op (@ops) {
	push(@plots,
	     "DEF:$op=$ops_rrd:$op:AVERAGE",
	     "DEF:m$op=$ops_rrd:$op:MAX",
	     "CDEF:d$op=$op,UN,0,$op,IF,$step,*",
	     "CDEF:s$op=PREV,UN,d$op,PREV,IF,d$op,+",
	     "AREA:$op#" . $color{$op} . ":" . substr(uc("$op    "), 0, 4) . ($opts->{'stacked'} ? ":STACK" : ""),
	     "GPRINT:s$op:MAX:\\t%12.0lf",
	     "GPRINT:$op:AVERAGE:\\t%6.2lf",
	     "GPRINT:m$op:MAX:\\t%6.0lf\\l",
	     );
    }

    rrd_graph($range, $file, $ypoints, "ops",
	      ($opts->{'logarithmic'} ? '--logarithmic' : ()),
	      'COMMENT:\t\t\t    TOTAL\t\tAVERAGE\t\tMAX\l',
	      @plots,

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

    return;
}

sub graph_connxn {
    my ($range, $file, $opts) = @_;
    my $step = $range * $points_per_sample / $xpoints;

    my @plots;
    my %types = (tls    => "TLS      ",
		 ssl    => "SSL      ",
		 sasl   => "SASL     ",
		 );

    foreach my $type (keys(%types)) {
	push(@plots,
	     "DEF:$type=$connxn_rrd:$type:AVERAGE",
	     "DEF:m$type=$connxn_rrd:$type:MAX",
	     "CDEF:d$type=$type,UN,0,$type,IF,$step,*",
	     "CDEF:s$type=PREV,UN,d$type,PREV,IF,d$type,+",
	     "AREA:$type#" . $color{$type} . ":" . $types{$type} . ($opts->{'stacked'} ? ":STACK" : ""),
	     "GPRINT:s$type:MAX:\\t%12.0lf",
	     "GPRINT:$type:AVERAGE:\\t%6.2lf",
	     "GPRINT:m$type:MAX:\\t%6.0lf\\l",
	     );

    }

    push(@plots,
	 "DEF:connxn=$connxn_rrd:connxn:AVERAGE",
	 "DEF:mconnxn=$connxn_rrd:connxn:MAX",
	 "CDEF:dconnxn=connxn,UN,0,connxn,IF,$step,*",
	 "CDEF:sconnxn=PREV,UN,dconnxn,PREV,IF,dconnxn,+",

	 "CDEF:plain=connxn,tls,sasl,-,-",
	 "CDEF:mplain=mconnxn,mtls,sasl,-,-",
	 "CDEF:dplain=dconnxn,dtls,sasl,-,-",
	 "CDEF:splain=sconnxn,stls,sasl,-,-",

	 "AREA:plain#" . $color{plain} . ":Plaintext:" . ($opts->{'stacked'} ? "STACK" : ""),
	 "GPRINT:splain:MAX:\\t%12.0lf",
	 "GPRINT:plain:AVERAGE:\\t%6.2lf",
	 "GPRINT:mplain:MAX:\\t%6.0lf\\l",
	 );

    rrd_graph($range, $file, $ypoints, "connections",
	      ($opts->{'logarithmic'} ? '--logarithmic' : ()),
	      'COMMENT:\t\t\t\t   TOTAL\t\tAVERAGE\t\tMAX\l',
	      @plots,

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

    return;
}

sub send_image {
    my $file = shift;

    if (!-r $file) {
	print "Content-type: text/plain\n\nERROR: can't find $file\n";
	exit 1;
    };

    print "Content-type: image/png\n";
    print "Content-length: " . ((stat($file))[7]) . "\n";
    print "\n";
    open(my $IMG, "<", $file) or die "Couldn't open $file: $!\n";
    my $data;
    print $data while read($IMG, $data, 16384) > 0;
    close($IMG);

    return;
}
