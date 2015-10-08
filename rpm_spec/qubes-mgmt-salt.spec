%{!?version: %define version %(make get-version)}
%{!?rel: %define rel %(make get-release)}
%{!?package_name: %define package_name %(make get-package_name)}
%{!?package_summary: %define package_summary %(make get-summary)}
%{!?package_description: %define package_description %(make get-description)}

Name:      qubes-mgmt-salt
Version:   %{version}
Release:   %{rel}%{?dist}
Summary:   %{package_summary}
License:   GPL 2.0
URL:	   http://www.qubes-os.org/

Group:     System administration tools
BuildArch: noarch
Requires:  salt
Requires:  salt-minion
Requires:  qubes-mgmt-salt-base
BuildRequires: PyYAML
Requires(post): /usr/bin/qubesctl

%define _builddir %(pwd)

%description
%{package_description}

%package config
Summary:   Qubes+Salt Management base configuration for SaltStack's Salt Infrastructure automation and management system.
Group:     System administration tools
Requires:  salt
Requires:  salt-minion
BuildRequires: PyYAML
BuildArch: noarch

%description config
Qubes+Salt Management base configuration for SaltStack's Salt Infrastructure automation and management system.

%package dom0
Summary:   Qubes+Salt Management dom0 dependencies.
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-dom0-qvm
Requires:  qubes-mgmt-salt-dom0-update
Requires:  qubes-mgmt-salt-dom0-virtual-machines
Requires(post): /usr/bin/qubesctl
Conflicts:  qubes-mgmt-salt-vm

%description dom0
Qubes+Salt Management dom0 dependencies.

%package vm
Summary:   Qubes+Salt Management VM dependencies.
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-vm-python-pip
Requires(post): /usr/bin/qubesctl
Conflicts:  qubes-mgmt-salt-dom0

%description vm
Qubes+Salt Management VM dependencies.

%package dom0-formulas
Summary:   All Qubes+Salt Management dom0 formulas
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-dom0-qvm
Requires:  qubes-mgmt-salt-dom0-update
Requires:  qubes-mgmt-salt-dom0-virtual-machines
Requires:  qubes-mgmt-salt-dom0-fix-permissions
Requires:  qubes-mgmt-salt-dom0-policy-qubesbuilder
Requires:  qubes-mgmt-salt-dom0-template-upgrade
Requires(post): /usr/bin/qubesctl

%description dom0-formulas
Qubes+Salt Management dom0 formulas.

%package vm-formulas
Summary:   All Qubes+Salt Management VM formulas
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-vm-python-pip
Requires(post): /usr/bin/qubesctl

%description vm-formulas
Qubes+Salt Management VM formulas.

%package extra-formulas
Summary:   All Qubes+Salt Management extra (qubes-mgmt-all-*) formulas
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-all-salt
Requires:  qubes-mgmt-salt-all-privacy
Requires:  qubes-mgmt-salt-all-theme
Requires:  qubes-mgmt-salt-all-vim
Requires:  qubes-mgmt-salt-all-gnupg
Requires:  qubes-mgmt-salt-all-yamlscript-renderer
Requires:  qubes-mgmt-salt-all-yamlscript-users
Requires(post): /usr/bin/qubesctl

%description extra-formulas
Qubes+Salt Management extra (qubes-mgmt-all-*) formulas.

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
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

%post dom0
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

%post vm
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

%post dom0-formulas
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

%post vm-formulas
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

%post extra-formulas
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

%files
%defattr(-,root,root)

%files config
%defattr(-,root,root)
%{_bindir}/qubesctl

%attr(750, root, root) %dir /etc/salt/minion.d
%{_sysconfdir}/salt/*

%attr(750, root, root) %dir /srv/reactor
/srv/reactor/*

%attr(750, root, root) %dir /srv/formulas
/srv/formulas/.gitignore

%attr(750, root, root) %dir /srv/salt
/srv/salt/*

%attr(750, root, root) %dir /srv/pillar
%config(noreplace) /srv/pillar/*

%files dom0
%defattr(-,root,root)

%files vm
%defattr(-,root,root)

%files dom0-formulas
%defattr(-,root,root)

%files vm-formulas
%defattr(-,root,root)

%files extra-formulas
%defattr(-,root,root)

%changelog
