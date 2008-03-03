# $Id$

%define cgidir  /usr/share/fedora-ds-graph
%define initdir %{_sysconfdir}/rc.d/init.d

Summary:   Fedora DS Graph
Name:      fedora-ds-graph
Version:   1.0.0
Release:   1
License:   GPL
Group:     System Environment/Daemons
Packager:  Chris St. Pierre <stpierre@nebrwesleyan.edu>
BuildArch: noarch

Provides:  fedora-ds-graph
Provides:  fdsgraph = %{version}
Obsoletes: fdsgraph < 0.3.0

Source:    http://www.stpierreconsulting.com/files/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root

%description
fedora-ds-graph is a utility for graphing connections and operations from Fedora Directory Server.

%prep
%setup

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{cgidir}
mkdir -p $RPM_BUILD_ROOT%{initdir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig

install -m 755 -o root -g root ds-graphd $RPM_BUILD_ROOT%{_bindir}/ds-graphd
install -m 755 -o root -g apache ds-graph.cgi $RPM_BUILD_ROOT%{cgidir}/ds-graph.cgi
install -m 755 -o root -g root ds-graph $RPM_BUILD_ROOT%{initdir}/ds-graph
install -m 755 -o root -g root ds-graph-sysconfig $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/ds-graph

%post
/sbin/chkconfig --add ds-graph

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_bindir}/ds-graphd
%{cgidir}/ds-graph.cgi
%{initdir}/ds-graph

%config(noreplace) %{_sysconfdir}/sysconfig/ds-graph

%changelog
* Thu Feb 28 2008 Chris St. Pierre <stpierre@NebrWesleyan.edu> - 
- Created
