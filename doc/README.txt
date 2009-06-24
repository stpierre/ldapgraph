389 DS Graph is a graphing tool for 389 Directory Server.  It
has been tested with all versions of 389 DS and Fedora DS;
additionally, it should also work with Red Hat DS and possibly Sun DS
as well.

Ideally, after installing, you should just have to run:

# service ds-graph start
# service httpd graceful

The web interface can be found at
http://yourhost.example.com/389-ds-graph/cgi-bin/ds-graph.cgi

389 DS Graph assumes by default that you have an 389 DS instance named
after the shortname of your server (i.e., config files for your
instance are in /etc/dirsrv/slapd-`hostname -s`).  If this isn't the
case, change the value of INSTANCE in /etc/sysconfig/ds-graph.

389 DS Graph does not currently support graphing data from more
than one 389 DS instance.

$Id$
