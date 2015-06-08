%{!?version: %define version %(cat version)}

Name: qubes-salt-config
Version: %{version}
Release: 1%{?dist}
Summary: Configuration files for SaltStack's Salt Infrastructure automation and management system

Group:   System Environment/Daemons
License: GPL 2.0
URL:	 http://www.qubes-os.org/

BuildArch: noarch
Requires: salt >= 2014.7.2
Requires: salt-minion >= 2014.7.2
Requires: vim
Requires: git
Requires: ca-certificates
Requires: redhat-lsb
Requires: rsync
Requires: python-dulwich
Requires: python-pip
Requires: python-gnupg

%define _builddir %(pwd)

%description
Configuration files for SaltStack's Salt Infrastructure automation and management system.

%prep
# we operate on the current directory, so no need to unpack anything
# symlink is to generate useful debuginfo packages
rm -f %{name}-%{version}
ln -sf . %{name}-%{version}
%setup -T -D

%build

%install
make install DESTDIR=%{buildroot} LIBDIR=%{_libdir} BINDIR=%{_bindir} SBINDIR=%{_sbindir} SYSCONFDIR=%{_sysconfdir}

%post
# Don't want or need minion or master services running
systemctl --no-reload disable salt-master.service > /dev/null 2>&1 || true
systemctl --no-reload disable salt-minion.service > /dev/null 2>&1 || true
systemctl stop salt-master.service > /dev/null 2>&1 || true
systemctl stop salt-minion.service > /dev/null 2>&1 || true

%preun
# Don't want or need minion or master services running
systemctl --no-reload disable salt-master.service > /dev/null 2>&1 || true
systemctl --no-reload disable salt-minion.service > /dev/null 2>&1 || true
systemctl stop salt-master.service > /dev/null 2>&1 || true
systemctl stop salt-minion.service > /dev/null 2>&1 || true

%files
%defattr(-,root,root)
%attr(750, root, root) %dir /etc/salt/minion.d
%attr(750, root, root) %dir /srv/_debug
%attr(750, root, root) %dir /srv/formulas
%attr(750, root, root) %dir /srv/pillar
%attr(750, root, root) %dir /srv/reactor
%attr(750, root, root) %dir /srv/salt
%{_bindir}/qubesctl
%{_sysconfdir}/salt/minion.d/*
/srv/_debug/*
/srv/formulas/*
/srv/pillar/*
/srv/salt/*
/srv/reactor/*

%changelog

