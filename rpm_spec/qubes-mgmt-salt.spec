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
Requires:  salt >= 2015.5
Requires:  salt-minion
Requires:  qubes-mgmt-salt-base
BuildRequires: PyYAML
BuildRequires: tree
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
qubesctl saltutil.clear_cache -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all refresh=true -l quiet --out quiet > /dev/null || true

%post config
qubesctl saltutil.clear_cache -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all refresh=true -l quiet --out quiet > /dev/null || true

%post extra-formulas
qubesctl saltutil.clear_cache -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all refresh=true -l quiet --out quiet > /dev/null || true

%files
%defattr(-,root,root)

%files config
%defattr(-,root,root)
%attr(750, root, root) %dir /etc/salt
%attr(750, root, root) %dir /etc/salt/minion.d
%attr(750, root, root) %dir /etc/salt/spm.repos.d
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
/srv/salt/top.sls.old

/usr/bin/qubesctl

%files extra-formulas
%defattr(-,root,root)

%changelog
