# $Id$

%define apacheconfdir %{_sysconfdir}/httpd/conf.d

Summary:   Fedora DS Graph
Name:      fedora-ds-graph
Version:   1.0.9
Release:   2
License:   GPLv2
Group:     System Environment/Daemons
Packager:  Chris St. Pierre <stpierre@nebrwesleyan.edu>
BuildArch: noarch

Provides:  fedora-ds-graph
Provides:  fdsgraph = %{version}
Obsoletes: fdsgraph < 0.3.0

Requires:  perl, rrdtool-perl, httpd

Source:    http://www.stpierreconsulting.com/files/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root

%description
fedora-ds-graph is a utility for graphing connections and operations
from Fedora Directory Server.

%prep
%setup

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

# cgis
mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}
install -m 755 -o root -g apache ds-graph.cgi $RPM_BUILD_ROOT%{_datadir}/%{name}/ds-graph.cgi

# httpd config
mkdir -p $RPM_BUILD_ROOT%{apacheconfdir}
install -m 644 -o root -g root fedora-ds-graph.conf $RPM_BUILD_ROOT%{apacheconfdir}/fedora-ds-graph.conf

# documentation
mkdir -p $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
install -m 644 -o root -g root ChangeLog $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}/ChangeLog
install -m 644 -o root -g root COPYING $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}/COPYING

%post
/sbin/chkconfig --add ds-graph

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/ds-graphd
%{_initrddir}/ds-graph
%{_localstatedir}/lib/%{name}
%attr(-,root,apache) %{_datadir}/%{name}/ds-graph.cgi

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
