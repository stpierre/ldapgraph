# $Id$

%define apacheconfdir %{_sysconfdir}/httpd/conf.d
%define oldname fedora-ds-graph

Summary:   389 DS Graph
Name:      389-ds-graph
Version:   1.1.2
Release:   1%{?dist}
License:   GPLv2
Group:     System Environment/Daemons
BuildArch: noarch

Provides:  389-ds-graph = %{version}
Obsoletes: fdsgraph, fedora-ds-graph

Requires:  perl, rrdtool-perl > 1.2, httpd, perl(Parse::FDSlog)

Source:    http://superb-east.dl.sourceforge.net/sourceforge/%{oldname}/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root

%description
389 DS Graph is a utility for graphing connections and operations
from 389 Directory Server/Fedora Directory Server

%prep
%setup -q

%build

%install
# perl lib                                                                  
mkdir -p -m 755 $RPM_BUILD_ROOT%{perl_vendorlib}/Parse
install -m 755 Parse/FDSlog.pm $RPM_BUILD_ROOT%{perl_vendorlib}/Parse/FDSlog.pm

# binary
mkdir -p $RPM_BUILD_ROOT%{_bindir}
install -m 755 ds-graphd $RPM_BUILD_ROOT%{_bindir}/ds-graphd

# init script, etc.
mkdir -p $RPM_BUILD_ROOT%{_initrddir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig
install -m 755 ds-graph $RPM_BUILD_ROOT%{_initrddir}/ds-graph
install -m 644 ds-graph-sysconfig \
   $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/ds-graph

# data dir
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}
ln -s -f %{_localstatedir}/lib/%{name} \
      $RPM_BUILD_ROOT%{_localstatedir}/lib/%{oldname}

# web stuff
mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}/cgi-bin
install -m 755 www/ds-graph.cgi \
   $RPM_BUILD_ROOT%{_datadir}/%{name}/cgi-bin/ds-graph.cgi
install -m 644 www/ds-graph.css $RPM_BUILD_ROOT%{_datadir}/%{name}/ds-graph.css
install -m 644 www/rrdtool.png $RPM_BUILD_ROOT%{_datadir}/%{name}/rrdtool.png

# httpd config
mkdir -p $RPM_BUILD_ROOT%{apacheconfdir}
install -m 644 %{name}.conf $RPM_BUILD_ROOT%{apacheconfdir}/%{name}.conf 

# documentation
mkdir -p $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
install -m 644 doc/* $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1
install -m 644 man/ds-graphd.1.gz $RPM_BUILD_ROOT%{_mandir}/man1/ds-graphd.1.gz

%pre
if [ -e $RPM_BUILD_ROOT%{_localstatedir}/lib/%{oldname} ]; then
   mv $RPM_BUILD_ROOT%{_localstatedir}/lib/%{oldname} \
      $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}
fi

%post
/sbin/chkconfig --add ds-graph

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/ds-graphd
%{_initrddir}/ds-graph
%{_localstatedir}/lib/%{name}
%{_localstatedir}/lib/%{oldname}
%attr(-,root,apache) %{_datadir}/%{name}

%config(noreplace) %{_sysconfdir}/sysconfig/ds-graph
%config(noreplace) %{apacheconfdir}/%{name}.conf

%doc %{_docdir}/%{name}-%{version}
%doc %{_mandir}/man1/ds-graphd.1.gz

#################################################
#           PACKAGE perl-Parse-FDSlog           #
#################################################


%package -n perl-Parse-FDSlog
Summary:   389 DS Log Parser
Version:   0.2.1
Release:   1%{?dist}
License:   GPLv2
Group:     Applications/CPAN
BuildArch: noarch

%description -n perl-Parse-FDSlog
Parse::FDSlog is a simple interface to parse logs generated by
389 Directory Server (formerly Fedora DS).

%files -n perl-Parse-FDSlog
%defattr(0755,root,root,-)
%{perl_vendorlib}/Parse/FDSlog.pm

#################################################
#          PACKAGE 389-ds-graph-selinux         #
#################################################

%package selinux
Summary:   389 DS Graph
Group:     System Environment/Daemons
Requires: %name = %version-%release
Requires(post): policycoreutils
Requires(postun): policycoreutils

%description selinux
389-ds-graph-selinux provides selinux policies for 389-ds-graph.

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
* Tue Jun 23 2009 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 1.1.2-1
- Changed name to 389 DS Graph

* Tue Dec  9 2008 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 1.1.0-1
- Split perl-Parse-FDSlog into separate package

* Thu Nov 20 2008 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 1.0.2-2
- Added selinux package

* Thu Aug 14 2008 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 1.0.2-1
- Substantially edited to conform closer to Fedora packaging guidelines

* Thu Feb 28 2008 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 0.3.0-1
- Created
