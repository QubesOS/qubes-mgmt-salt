%{!?version: %define version %(cat version)}
%{!?rel: %define rel %(cat rel)}

%{!?formula_name: %define formula_name %(grep 'name' FORMULA|head -n 1|cut -f 2 -d :|xargs)}
%{!?state_name: %define state_name %(grep 'top_level_dir' FORMULA|head -n 1|cut -f 2 -d :|xargs)}
%{!?saltenv: %define saltenv %(grep 'saltenv' FORMULA|head -n 1|cut -f 2 -d :|xargs)}

%if "%{state_name}" == ""
  %define state_name %{formula_name}
%endif

%if "%{saltenv}" == ""
  %define saltenv base
%endif

%define salt_state_dir /srv/salt
%define salt_pillar_dir /srv/pillar
%define salt_formula_dir /srv/formulas

Name:      qubes-mgmt-salt
Version:   %{version}
Release:   %{rel}%{?dist}
Summary:   Configuration files for SaltStack's Salt Infrastructure automation and management system
License:   GPL 2.0
URL:	   http://www.qubes-os.org/

Group:     System administration tools
BuildArch: noarch
Requires:  salt >= 2015.8.0
Requires:  salt-minion >= 2015.8.0
Requires:  ca-certificates
#Requires:  redhat-lsb
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
Requires(post): /usr/bin/salt-call
Conflicts:  qubes-mgmt-salt-vm

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
Conflicts:  qubes-mgmt-salt-dom0

%description vm
Qubes+Salt Management vm dependencies.

Qubes+Salt Management dom0 dependencies (all dom0 packages).
%prep
# we operate on the current directory, so no need to unpack anything
# symlink is to generate useful debuginfo packages
rm -f %{name}-%{version}
ln -sf . %{name}-%{version}
%setup -T -D

%build

%install
make install DESTDIR=%{buildroot} LIBDIR=%{_libdir} BINDIR=%{_bindir} SBINDIR=%{_sbindir} SYSCONFDIR=%{_sysconfdir} VERBOSE=%{_verbose}

%post
# Update Salt Configuration
qubesctl state.sls qubes.config -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

# Enable Pillar States
qubesctl topd.enable qubes saltenv=%{saltenv} pillar=true -l quiet --out quiet > /dev/null || true
qubesctl topd.enable qubes.config saltenv=%{saltenv} pillar=true -l quiet --out quiet > /dev/null || true

%post dom0
# Update Salt Configuration
qubesctl state.sls qubes.config -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

%post vm
# Update Salt Configuration
qubesctl state.sls qubes.config -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all -l quiet --out quiet > /dev/null || true

%files
%defattr(-,root,root)

%files dom0
%defattr(-,root,root)

%files vm
%defattr(-,root,root)

%files config
%defattr(-,root,root)
%{_bindir}/qubesctl

%attr(750, root, root) %dir /etc/salt/minion.d
%{_sysconfdir}/salt/*

%attr(750, root, root) %dir /srv/reactor
/srv/reactor/*

%attr(750, root, root) %dir %{salt_formula_dir}
/srv/formulas/.gitignore

%attr(750, root, root) %dir %{salt_state_dir}
%{salt_state_dir}/*

%attr(750, root, root) %dir %{salt_pillar_dir}
%config(noreplace) %{salt_pillar_dir}/*

%changelog
