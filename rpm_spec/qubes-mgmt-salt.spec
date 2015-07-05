%{!?version: %define version %(cat version)}
%{!?rel: %define rel %(cat rel)}

Name:      qubes-mgmt-salt
Version:   %{version}
Release:   %{rel}%{?dist}
Summary:   Configuration files for SaltStack's Salt Infrastructure automation and management system
License:   GPL 2.0
URL:	   http://www.qubes-os.org/

Group:     System administration tools
BuildArch: noarch
Requires:  salt
Requires:  salt-minion
Requires:  ca-certificates
Requires:  redhat-lsb
Requires:  python-gnupg
Requires:  qubes-mgmt-salt-config
Requires:  qubes-mgmt-salt-base
Requires(post): /usr/bin/salt-call

%define _builddir %(pwd)

%description
Qubes Management base configuration for SaltStack's Salt Infrastructure automation and management system.

%package config
Summary:   Qubes+Salt Management base configuration for SaltStack's Salt Infrastructure automation and management system.
Group:     System administration tools
BuildArch: noarch
Requires:  salt
Requires:  salt-minion

%description config
Qubes+Salt Management base configuration for SaltStack's Salt Infrastructure automation and management system.

%package dom0
Summary:   Qubes+Salt Management dom0 dependencies.
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-config
Requires:  qubes-mgmt-salt-base
Requires:  qubes-mgmt-salt-dom0-qvm
Requires:  qubes-mgmt-salt-dom0-update
Requires:  qubes-mgmt-salt-dom0-virtual-machines
Requires:  qubes-mgmt-salt-dom0-policy-qubesbuilder
Requires:  qubes-mgmt-salt-dom0-fix-permissions
Requires:  qubes-mgmt-salt-dom0-template-upgrade
Requires(post): /usr/bin/salt-call

%description dom0
Qubes+Salt Management dom0 dependencies.

%package vm
Summary:   Qubes+Salt Management vm dependencies.
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-config
Requires:  qubes-mgmt-salt-base
Requires:  git
Requires:  python-dulwich
Requires:  python-pip
Requires:  qubes-mgmt-salt-vm-python-pip
Requires(post): /usr/bin/salt-call

%description vm
Qubes+Salt Management vm dependencies.

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
# TODO:
# - Add formula path to file_roots
# - Add formula to salt top.sls
# - Add formula to pillar top.sls if contains pillar data
salt-call --local saltutil.sync_all -l quiet --out quiet > /dev/null || true
salt-call --local state.sls salt.standalone-config -l quiet --out quiet > /dev/null || true

%post dom0
salt-call --local saltutil.sync_all -l quiet --out quiet > /dev/null || true
salt-call --local state.sls salt.standalone-config -l quiet --out quiet > /dev/null || true

%post vm
salt-call --local saltutil.sync_all -l quiet --out quiet > /dev/null || true
salt-call --local state.sls salt.standalone-config -l quiet --out quiet > /dev/null || true

%files
%defattr(-,root,root)

%files dom0
%defattr(-,root,root)

%files vm
%defattr(-,root,root)

%files config
%defattr(-,root,root)
%attr(750, root, root) %dir /etc/salt/minion.d
%attr(750, root, root) %dir /srv/formulas
%attr(750, root, root) %dir /srv/pillar
%attr(750, root, root) %dir /srv/reactor
%attr(750, root, root) %dir /srv/salt
%{_bindir}/qubesctl
%{_sysconfdir}/salt/minion.d/*
/srv/formulas/.gitignore
/srv/pillar/*
/srv/salt/*
/srv/reactor/*

%changelog
