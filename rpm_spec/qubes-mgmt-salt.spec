%{!?version: %define version %(cat version)}

Name:      qubes-mgmt-salt
Version:   %{version}
Release:   1%{?dist}
Summary:   Installs salts configuration files, directory layout and qubesctl
License:   GPL 2.0
URL:	   http://www.qubes-os.org/

Group:     System administration tools
BuildArch: noarch
Requires:  salt >= 2015.5
Requires:  salt-minion
Requires:  qubes-mgmt-salt-base
BuildRequires: PyYAML
BuildRequires: tree
BuildRequires: pandoc

%define _builddir %(pwd)

%description
Installs salts configuration files, directory layout and qubesctl

- qubes-mgmt-salt:
    Installs salt and base configuration and modules

- qubes-mgmt-salt-dom0:
    qubes-mgmt-salt + dom0 depends

- qubes-mgmt-salt-dom0-formulas:
    All dom0 formulas

- qubes-mgmt-salt-vm:
    qubes-mgmt-salt + VM depends

- qubes-mgmt-salt-vm-formulas:
    All VM formulas

- qubes-mgmt-salt-extra-formulas:
    All extra formulas (qubes-mgmt-all-*)

%package config
Summary:   Qubes+Salt Management base configuration for SaltStack's Salt Infrastructure automation and management system.
Group:     System administration tools
Requires:  salt
Requires:  salt-minion
BuildRequires: PyYAML
BuildArch: noarch

%description config
Qubes+Salt Management base configuration for SaltStack's Salt Infrastructure automation and management system.

%package shared-formulas
Summary:   All Qubes+Salt Management shared (qubes-mgmt-all-*) formulas
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt

%description shared-formulas
Qubes+Salt Management shared (qubes-mgmt-all-*) formulas.

%package admin-tools
Summary:    Management tools integrating dom0 and VM management
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt

%description admin-tools
Tools to integrate dom0 and VM management into a single qubesctl tool.

%prep
# we operate on the current directory, so no need to unpack anything
# symlink is to generate useful debuginfo packages
rm -f %{name}-%{version}
ln -sf . %{name}-%{version}
%setup -T -D

%build

%install
make install DESTDIR=%{buildroot} LIBDIR=%{_libdir} BINDIR=%{_bindir} SBINDIR=%{_sbindir} SYSCONFDIR=%{_sysconfdir}
make install-dom0 DESTDIR=%{buildroot}

%files
%defattr(-,root,root)
%attr(766, root, root)
%{_mandir}/man1/qubesctl.1*


%files config
%defattr(-,root,root)
%config(noreplace) /etc/salt/minion.d/f_defaults.conf
/etc/salt/minion.dist
/etc/salt/minion.dom0.conf
/etc/salt/minion.vm.conf
/etc/salt/spm
/etc/salt/spm.repos.d/local.repo

%attr(750, root, root) %dir /srv/formulas
/srv/formulas/.gitignore

%attr(750, root, root) %dir /srv/pillar
%config(noreplace) /srv/pillar/top.sls
/srv/pillar/top.sls.old

%attr(750, root, root) %dir /srv/reactor
/srv/reactor/import_keys
/srv/reactor/sync_all.sls

%attr(750, root, root) %dir /srv/salt
%config(noreplace) /srv/salt/top.sls
/srv/salt/top.jinja
/srv/salt/top.sls.old

%files admin-tools
/usr/bin/qubesctl
%dir %{python_sitelib}/qubessalt-*egg-info
%{python_sitelib}/qubessalt-*egg-info/*
%dir %{python_sitelib}/qubessalt
%{python_sitelib}/qubessalt/__init__.py*


%files shared-formulas
%defattr(-,root,root)

%changelog
