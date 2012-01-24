%define apacheconfdir %{_sysconfdir}/httpd/conf.d

Summary:   LDAP graphing tool
Name:      ldapgraph
Version:   1.2.0
Release:   1%{?dist}
License:   GPLv2
Group:     System Environment/Daemons
BuildArch: noarch

Obsoletes: fdsgraph < %{version}, fedora-ds-graph < %{version}
Obsoletes: 389-ds-graph < %{version}

BuildRequires: perl

Requires: perl, rrdtool-perl > 1.2, httpd
Requires: perl(Parse::389Log), perl(Parse::OpenLDAPLog)

URL:       https://github.com/stpierre/%{name}
Source0:   %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root

%description
LDAPGraph is a graphing tool for various LDAP servers.  It is known
to work with 389 Directory Server (formerly Fedora DS), and should
also work with Red Hat DS and Sun DS as well.  OpenLDAP support is
forthcoming.

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT

# perl lib                                                                  
mkdir -p -m 755 $RPM_BUILD_ROOT%{perl_vendorlib}/Parse
install -m 755 Parse/389Log.pm $RPM_BUILD_ROOT%{perl_vendorlib}/Parse/389Log.pm

# binary
mkdir -p $RPM_BUILD_ROOT%{_bindir}
install -m 755 ldapgraphd $RPM_BUILD_ROOT%{_bindir}/ldapgraphd

# init script, etc.
mkdir -p $RPM_BUILD_ROOT%{_initrddir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig
install -m 755 %{name} $RPM_BUILD_ROOT%{_initrddir}/%{name}
install -m 644 %{name}-sysconfig \
   $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/%{name}

# data dir
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}
ln -s -f %{_localstatedir}/lib/%{name} \
      $RPM_BUILD_ROOT%{_localstatedir}/lib/%{oldname}

# web stuff
mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}/cgi-bin
install -m 755 www/%{name}.cgi \
   $RPM_BUILD_ROOT%{_datadir}/%{name}/cgi-bin/%{name}.cgi
install -m 644 www/%{name}.css $RPM_BUILD_ROOT%{_datadir}/%{name}/%{name}.css
install -m 644 www/rrdtool.png $RPM_BUILD_ROOT%{_datadir}/%{name}/rrdtool.png

# httpd config
mkdir -p $RPM_BUILD_ROOT%{apacheconfdir}
install -m 644 %{name}.conf $RPM_BUILD_ROOT%{apacheconfdir}/%{name}.conf 

# documentation
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1
pod2man ldapgraphd | gzip -c > $RPM_BUILD_ROOT%{_mandir}/man1/ldapgraphd.1.gz

%pre
if [ -e %{_localstatedir}/lib/%{oldname} ]; then
   mv %{_localstatedir}/lib/%{oldname} %{_localstatedir}/lib/%{name}
fi

%preun
if [ $1 -eq 0 ] ; then
    /sbin/chkconfig --del %{name}
fi

%post
/sbin/chkconfig --add %{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/ldapgraphd
%{_initrddir}/%{name}
%{_localstatedir}/lib/%{name}
%{_localstatedir}/lib/%{oldname}
%attr(-,root,apache) %{_datadir}/%{name}

%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{apacheconfdir}/%{name}.conf

%{_mandir}/man1/%{name}.1.gz

%doc README
%doc doc/*

#################################################
#           PACKAGE perl-Parse-389Log           #
#################################################


%package -n perl-Parse-389Log
Summary:   389 DS Log Parser
Version:   0.3.0
Release:   1%{?dist}
License:   GPLv2
Group:     Development/Libraries
BuildArch: noarch

%description -n perl-Parse-389Log
Parse::389Log is a simple interface to parse logs generated by
389 Directory Server (formerly Fedora DS).

%files -n perl-Parse-389Log
%defattr(0755,root,root,-)
%{perl_vendorlib}/Parse/389Log.pm

#################################################
#        PACKAGE perl-Parse-OpenLDAPLog         #
#################################################

%package -n perl-Parse-OpenLDAPLog
Summary:   OpenLDAP Log Parser
Version:   0.1.0
Release:   1%{?dist}
License:   GPLv2
Group:     Development/Libraries
BuildArch: noarch

%description -n perl-Parse-OpenLDAPLog
Parse::OpenLDAPLog is a simple interface to parse logs generated by
OpenLDAP.

%files -n perl-Parse-OpenLDAPLog
%defattr(0755,root,root,-)
%{perl_vendorlib}/Parse/OpenLDAPLog.pm

#################################################
#           PACKAGE ldapgraph-selinux           #
#################################################

%package selinux
Summary:   LDAPGraph
Group:     System Environment/Daemons
Requires:  %name = %version-%release
Requires(post):   policycoreutils
Requires(postun): policycoreutils

%description selinux
ldapgraph-selinux provides selinux policies for ldapgraph.

%post selinux
semanage fcontext -a -t httpd_sys_script_exec_t \
   %{_datadir}/%{name}/ldapgraph.cgi 2>/dev/null || :
restorecon -R %{_datadir}/%{name}/ldapgraph.cgi || :

%postun selinux
if [ $1 -eq 0 ] ; then  # final removal
   semanage fcontext -d -t httpd_sys_script_exec_t \
      %{_datadir}/%{name}/ldapgraph.cgi 2>/dev/null || :
fi

%files selinux

%changelog
* Tue Nov 15 2011 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 1.2.0-1
- Change name to LDAPGraph

* Thu Jun 17 2010 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 1.1.3-1
- Renamed FDSlog to 389Log

* Tue Mar  2 2010 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 1.1.2-3
- Made selinux package actually build

* Wed Dec  2 2009 Chris St. Pierre <chris.a.st.pierre@gmail.com> - 1.1.2-2
- Misc. minor changes

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
