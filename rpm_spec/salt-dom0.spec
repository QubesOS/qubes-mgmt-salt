
%{!?version: %define version %(cat version)}

Name: qubes-salt-config
Version: %{version}
Release: 1%{?dist}
Summary: Configuration files for SaltStack's Salt Infrastructure automation and management system

Group:   System Environment/Daemons
License: GPL 2.0
URL:     http://saltstack.org/

BuildArch: noarch

