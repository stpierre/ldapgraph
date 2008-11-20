Fedora DS Graph is a graphing tool for Fedora Directory Server.  It
should work with both FDS 1.0.x and 1.1.x.

Ideally, after installing, you should just have to run:

# service httpd restart

To get the Apache configs in place; it will automatically start
analyzing your logs.

The web interface can be found at
http://yourhost.example.com/fedora-ds-graph/cgi-bin/ds-graph.cgi

Fedora DS Graph assumes by default that you have an FDS instanced
named after the shortname of your server (i.e., config files for your
instance are in /etc/dirsrv/slapd-`hostname -s`).  If this isn't the
case, change the value of INSTANCE in /etc/sysconfig/ds-graph.

Fedora DS Graph does not currently support graphing data from more
than one FDS instance.

$Id$
