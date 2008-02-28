# $Id$

%define cgidir  /var/www/cgi-bin
%define initdir %{_sysconfdir}/rc.d/init.d

Summary:   Fedora DS Graph
Name:      fdsgraph
Version:   0.8.2
Release:   1
License:   GPL
Group:     System Environment/Daemons
Packager:  Chris St. Pierre <stpierre@nebrwesleyan.edu>
BuildArch: noarch
Provides:  fdsgraph
Source:    http://www.stpierreconsulting.com/files/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root

%description
fdsgraph is a utility for graphing connections and operations from Fedora Directory Server.

%prep
%setup

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{cgidir}
mkdir -p $RPM_BUILD_ROOT%{initdir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig

install -m 755 -o root -g root fdsgraph.pl $RPM_BUILD_ROOT%{_bindir}/fdsgraph.pl
install -m 755 -o root -g apache fdsgraph.cgi $RPM_BUILD_ROOT%{cgidir}/fdsgraph.cgi
install -m 755 -o root -g root fdsgraph $RPM_BUILD_ROOT${initdir}/fdsgraph
install -m 755 -o root -g root fdsgraph-sysconfig $RPM_BUILD_ROOT${_sysconfdir}/sysconfig/fdsgraph

%post
/sbin/chkconfig --add fdsgraph

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_bindir}/fdsgraph.pl
/var/www/cgi-bin/fdsgraph.cgi
%{initdir}/fdsgraph

%config(noreplace) %{_sysconfdir}/sysconfig/fdsgraph

%changelog
* Thu Feb 28 2008 Chris St. Pierre <stpierre@NebrWesleyan.edu> - 
- Created
