%{!?version: %define version %(make get-version)}
%{!?rel: %define rel %(make get-release)}
%{!?package_name: %define package_name %(make get-package_name)}
%{!?package_summary: %define package_summary %(make get-summary)}
%{!?package_description: %define package_description %(make get-description)}

Name:      qubes-mgmt-salt-dom0
Version:   %{version}
Release:   %{rel}%{?dist}
Summary:   Qubes+Salt Management dom0 dependencies
License:   GPL 2.0
URL:	   http://www.qubes-os.org/

Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-dom0-qvm
Requires:  qubes-mgmt-salt-dom0-update
Requires:  qubes-mgmt-salt-dom0-virtual-machines
BuildRequires: PyYAML
BuildRequires: tree
Requires(post): /usr/bin/qubesctl
Conflicts:  qubes-mgmt-salt-vm

%define _builddir %(pwd)

%description
Qubes+Salt Management dom0 dependencies.

%package formulas
Summary:   All Qubes+Salt Management dom0 formulas
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-dom0
Requires:  qubes-mgmt-salt-dom0-qvm
Requires:  qubes-mgmt-salt-dom0-update
Requires:  qubes-mgmt-salt-dom0-virtual-machines
Requires:  qubes-mgmt-salt-dom0-fix-permissions
Requires:  qubes-mgmt-salt-dom0-policy-qubesbuilder
Requires:  qubes-mgmt-salt-dom0-template-upgrade
Requires(post): /usr/bin/qubesctl

%description formulas
Qubes+Salt Management dom0 formulas.

%prep
# we operate on the current directory, so no need to unpack anything
# symlink is to generate useful debuginfo packages
rm -f %{name}-%{version}
ln -sf . %{name}-%{version}
%setup -T -D

%build

%install

%post
qubesctl saltutil.clear_cache -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all refresh=true -l quiet --out quiet > /dev/null || true

%post formulas
qubesctl saltutil.clear_cache -l quiet --out quiet > /dev/null || true
qubesctl saltutil.sync_all refresh=true -l quiet --out quiet > /dev/null || true

%files
%defattr(-,root,root)

%files formulas
%defattr(-,root,root)

%changelog
