# $Id$

%define apacheconfdir %{_sysconfdir}/httpd/conf.d

Summary:   Fedora DS Graph
Name:      fedora-ds-graph
Version:   1.0.99
Release:   4%{dist}
License:   GPLv2
Group:     System Environment/Daemons
BuildArch: noarch

Provides:  fdsgraph = %{version}
Obsoletes: fdsgraph < 0.3.0

Requires:  perl, rrdtool-perl > 1.2, httpd

Source:    http://www.stpierreconsulting.com/files/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root

%description
fedora-ds-graph is a utility for graphing connections and operations
from Fedora Directory Server.

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT

# binary
mkdir -p $RPM_BUILD_ROOT%{_bindir}
install -m 755 -o root -g root ds-graphd $RPM_BUILD_ROOT%{_bindir}/ds-graphd

# init script, etc.
mkdir -p $RPM_BUILD_ROOT%{_initrddir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig
install -m 755 -o root -g root ds-graph $RPM_BUILD_ROOT%{_initrddir}/ds-graph
install -m 644 -o root -g root ds-graph-sysconfig $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/ds-graph

# data dir
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}

# web stuff
mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}/cgi-bin
install -m 755 -o root -g apache www/ds-graph.cgi $RPM_BUILD_ROOT%{_datadir}/%{name}/cgi-bin/ds-graph.cgi
install -m 755 -o root -g apache www/ds-graph.css $RPM_BUILD_ROOT%{_datadir}/%{name}/ds-graph.css
install -m 755 -o root -g apache www/rrdtool.png $RPM_BUILD_ROOT%{_datadir}/%{name}/rrdtool.png

# httpd config
mkdir -p $RPM_BUILD_ROOT%{apacheconfdir}
install -m 644 -o root -g root fedora-ds-graph.conf $RPM_BUILD_ROOT%{apacheconfdir}/fedora-ds-graph.conf

# documentation
mkdir -p $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
install -m 644 -o root -g root doc/* $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}

%post
/sbin/chkconfig --add ds-graph
/sbin/service ds-graph start

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/ds-graphd
%{_initrddir}/ds-graph
%{_localstatedir}/lib/%{name}
%attr(-,root,apache) %{_datadir}/%{name}

%config(noreplace) %{_sysconfdir}/sysconfig/ds-graph
%config(noreplace) %{apacheconfdir}/fedora-ds-graph.conf

%doc %{_docdir}/%{name}-%{version}

%package selinux
Summary:   Fedora DS Graph
Group:     System Environment/Daemons
Requires: %name = %version-%release
Requires(post): policycoreutils
Requires(postun): policycoreutils

%description selinux
fedora-ds-graph-selinux provides selinux policies for fedora-ds-graph.

%post selinux
semanage fcontext -a -t httpd_sys_script_exec_t \
   %{_datadir}/%{name}/ds-graph.cgi 2>/dev/null || :
restorecon -R %{_datadir}/%{name}/ds-graph.cgi || :

%postun selinux
if [ $1 -eq 0 ] ; then  # final removal
   semanage fcontext -d -t httpd_sys_script_exec_t \
      %{_datadir}/%{name}/ds-graph.cgi 2>/dev/null || :
fi

%changelog
* Thu Nov 20 2008 Chris St. Pierre <stpierre@NebrWesleyan.edu> - 
- Added selinux package

* Thu Aug 14 2008 Chris St. Pierre <stpierre@NebrWesleyan.edu> - 
- Substantially edited to conform closer to Fedora packaging guidelines

* Thu Feb 28 2008 Chris St. Pierre <stpierre@NebrWesleyan.edu> - 
- Created
