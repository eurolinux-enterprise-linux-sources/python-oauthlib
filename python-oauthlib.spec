%if 0%{?fedora}
%global with_python3 1
%endif

%if 0%{?rhel} && 0%{?rhel} <= 7
%{!?__python2:        %global __python2 /usr/bin/python2}
%{!?python2_sitelib:  %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%{!?py2_build:        %global py2_build %{__python2} setup.py build --executable="%{__python2} -s" %{?*}}
%{!?py2_install:      %global py2_install %{__python2} setup.py install --skip-build --root %{buildroot} %{?*}}
%endif

# commit corresponds to v2.0.1 tag
%global commit 3eb6fe934c8c8d6c34e22b4e4fc1bd01d0266df6
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global checkout 20150520git%{shortcommit}

%global gh_owner idan
%global gh_project oauthlib

%global modname oauthlib

Name:               python-oauthlib
Version:            2.0.1
Release:            8%{?dist}
Summary:            An implementation of the OAuth request-signing logic

Group:              Development/Libraries
License:            BSD
URL:                http://pypi.python.org/pypi/oauthlib
Source0:            http://pypi.python.org/packages/source/o/%{modname}/%{modname}-%{version}.tar.gz
#Source0:            https://github.com/%{gh_owner}/%{gh_project}/archive/%{commit}/%{gh_project}-%{commit}.tar.gz

BuildArch:          noarch

Patch0: jwcrypto.patch


%description
OAuthLib is a generic utility which implements the logic of OAuth without
assuming a specific HTTP request object or web framework. Use it to graft
OAuth client support onto your favorite HTTP library, or provider support
onto your favourite web framework. If you're a maintainer of such a
library, write a thin veneer on top of OAuthLib and get OAuth support for
very little effort.

%package -n python2-oauthlib
%if 0%{?python_provide:1}
%python_provide python2-oauthlib
%else
Provides:           python-oauthlib = %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:          python-oauthlib < %{?epoch:%{epoch}:}%{version}-%{release}
%endif

Summary:            An implementation of the OAuth request-signing logic
Group:              Development/Libraries

BuildRequires:      python2-devel
BuildRequires:      python2-setuptools

BuildRequires:      python2-nose
BuildRequires:      python-mock
BuildRequires:      python-blinker

BuildRequires:      python-jwcrypto
BuildRequires:      python2-cryptography

Requires:           python-jwcrypto
Requires:           python2-cryptography >= 0.8.1

%description -n python2-oauthlib
OAuthLib is a generic utility which implements the logic of OAuth without
assuming a specific HTTP request object or web framework. Use it to graft
OAuth client support onto your favorite HTTP library, or provider support
onto your favourite web framework. If you're a maintainer of such a
library, write a thin veneer on top of OAuthLib and get OAuth support for
very little effort.

%if 0%{?with_python3}
%package -n python3-oauthlib
%{?python_provide:%python_provide python3-oauthlib}
Summary:            An implementation of the OAuth request-signing logic
Group:              Development/Libraries

BuildRequires:      python3-devel
BuildRequires:      python3-setuptools

BuildRequires:      python3-nose
BuildRequires:      python3-blinker

BuildRequires:      python3-jwcrypto
BuildRequires:      python3-cryptography

Requires:           python3-jwcrypto
Requires:           python3-cryptography >= 0.8.1

%description -n python3-oauthlib
OAuthLib is a generic utility which implements the logic of OAuth without
assuming a specific HTTP request object or web framework. Use it to graft
OAuth client support onto your favorite HTTP library, or provider support
onto your favourite web framework. If you're a maintainer of such a
library, write a thin veneer on top of OAuthLib and get OAuth support for
very little effort.
%endif

%prep
%setup -q -n %{modname}-%{version}
#%%setup -q -n %{gh_project}-%{commit}
%patch0 -p1

# python-unittest2 is now provided by "python" package and python-unittest is retired
#  adapt setup.py to reflect this fact downstream
sed -i "s/'unittest2', //" setup.py

# Remove bundled egg-info in case it exists
rm -rf %{modname}.egg-info

%build
%py2_build
%if 0%{?with_python3}
%py3_build
%endif

%install
%py2_install
%if 0%{?with_python3}
%py3_install
%endif

%check
%{__python2} setup.py test
%if 0%{?with_python3}
%{__python3} setup.py test
%endif

%files -n python2-oauthlib
%doc README.rst
%license LICENSE
%{python2_sitelib}/%{modname}/
%{python2_sitelib}/%{modname}-%{version}*

%if 0%{?with_python3}
%files -n python3-oauthlib
%doc README.rst
%license LICENSE
%{python3_sitelib}/%{modname}/
%{python3_sitelib}/%{modname}-%{version}-*
%endif

%changelog
* Mon Apr 24 2017 John Dennis <jdennis@redhat.com> - 2.0.1-8
- add missing Obsoletes for prior python-oauthlib package,
  replaced by python2-oauthlib
  Resolves: rhbz#1401784

* Thu Apr  6 2017 John Dennis <jdennis@redhat.com> - 2.0.1-7
- fix usage of python-provide macro
  Resolves: rhbz#1401784

* Thu Apr  6 2017 John Dennis <jdennis@redhat.com> - 2.0.1-6
- add spaces around python-cryptography version operator
  Resolves: rhbz#1401784

* Tue Apr  4 2017 John Dennis <jdennis@redhat.com> - 2.0.1-5
- change Requires: python-cryptography to python2-cryptography
  Resolves: rhbz#1401784

* Mon Apr  3 2017 John Dennis <jdennis@redhat.com> - 2.0.1-4
- Add Provides: python-oauthlib=version
  Resolves: rhbz#1401784

* Mon Apr  3 2017 John Dennis <jdennis@redhat.com> - 2.0.1-3
- Add Provides: python-oauthlib
  Resolves: rhbz#1401784

* Wed Mar 29 2017 John Dennis <jdennis@redhat.com> - 2.0.1-2
- Add missing Requires
  Resolves: rhbz#1401784

* Thu Mar 16 2017 John Dennis <jdennis@redhat.com> - 2.0.1-1
- Upgrade to upstream 2.0.1 and port from jwt to jwcrypto
  Resolves: rhbz#1401784

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Dec 13 2016 Stratakis Charalampos <cstratak@redhat.com> - 1.0.3-4
- Rebuild for Python 3.6

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.3-3
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Tue Jun 28 2016 Ralph Bean <rbean@redhat.com> - 1.0.3-2
- Modernize python macros.

* Sun Apr 10 2016 Kevin Fenzi <kevin@scrye.com> - 1.0.3-1
- Update to 1.0.3
- Add python2 provides (fixes bug #1313235 and #1314349)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.2-5.20150520git514cad7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Nov 10 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.2-4.20150520git514cad7
- Rebuilt for https://fedoraproject.org/wiki/Changes/python3.5

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.2-3.20150520git514cad7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Feb 18 2015 Ralph Bean <rbean@redhat.com> - 0.7.2-2.20150520git514cad7
- new version, from a git checkout
- Replace our patch with a sed statement.

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed May 14 2014 Bohuslav Kabrda <bkabrda@redhat.com> - 0.6.0-5
- Rebuilt for https://fedoraproject.org/wiki/Changes/Python_3.4

* Fri Apr 11 2014 Ralph Bean <rbean@redhat.com> - 0.6.0-4
- Use forward-compat python-crypto2.6 package for el6.

* Tue Jan 21 2014 Ralph Bean <rbean@redhat.com> - 0.6.0-3
- Compat macros for el6.

* Fri Nov 01 2013 Ralph Bean <rbean@redhat.com> - 0.6.0-2
- Modernized python2 rpmmacros.

* Thu Oct 31 2013 Ralph Bean <rbean@redhat.com> - 0.6.0-1
- Initial package for Fedora
