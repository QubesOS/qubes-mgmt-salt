%{!?version: %define version %(cat version)}

Name:      qubes-mgmt-salt-dom0
Version:   %{version}
Release:   1%{?dist}
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

mkdir -p $RPM_BUILD_ROOT/etc/salt
echo -n dom0 > $RPM_BUILD_ROOT/etc/salt/minion_id

%files
%defattr(-,root,root)
%config(noreplace) /etc/salt/minion_id

%files formulas
%defattr(-,root,root)

%changelog
