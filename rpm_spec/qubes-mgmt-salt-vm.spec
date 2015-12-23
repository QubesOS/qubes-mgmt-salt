%{!?version: %define version %(cat version)}

Name:      qubes-mgmt-salt-vm
Version:   %{version}
Release:   1%{?dist}
Summary:   Qubes+Salt Management VM dependencies
License:   GPL 2.0
URL:	   http://www.qubes-os.org/

Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
BuildRequires: PyYAML
BuildRequires: tree
Requires(post): /usr/bin/qubesctl
Conflicts:  qubes-mgmt-salt-dom0

%define _builddir %(pwd)

%description
Qubes+Salt Management VM dependencies.

%package formulas
Summary:   All Qubes+Salt Management VM formulas
Group:     System administration tools
BuildArch: noarch
Requires:  qubes-mgmt-salt
Requires:  qubes-mgmt-salt-vm
Requires(post): /usr/bin/qubesctl
#Requires:  qubes-mgmt-salt-vm-python-pip

%description formulas
Qubes+Salt Management VM formulas.

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
