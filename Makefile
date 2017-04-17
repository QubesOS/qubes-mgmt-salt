# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2015 Jason Mehring <nrgaway@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

_self_path := $(shell readlink -m $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
include $(_self_path)/components.conf

# This file is generated from FORMULA* by yaml-dumper in mgmt-salt builder plugin
include Makefile.vars

# This file is copied in from mgmt-salt
include Makefile.install

build:
	make manpages -C doc

.PHONY: install-custom
install-custom:: 
	# Install qubesctl
	@install -d -m 0755 $(DESTDIR)$(BINDIR)
	@install -p -m 0755 qubesctl $(DESTDIR)$(BINDIR)
	
	# Install /etc/salt/* and /srv/*
	cp -Tr etc $(DESTDIR)/etc
	cp -Tr srv $(DESTDIR)/srv
	
.PHONY: install-vm
install-vm:
	install -d $(DESTDIR)/usr/lib/qubes-vm-connector/ssh-wrapper
	install ssh-wrapper $(DESTDIR)/usr/lib/qubes-vm-connector/ssh-wrapper/ssh
	ln -s ssh $(DESTDIR)/usr/lib/qubes-vm-connector/ssh-wrapper/scp
	ln -s /bin/true $(DESTDIR)/usr/lib/qubes-vm-connector/ssh-wrapper/ssh-keygen
	install -d $(DESTDIR)/etc/qubes-rpc
	install qubes.SaltLinuxVM $(DESTDIR)/etc/qubes-rpc

.PHONY: install-dom0
install-dom0:
	python setup.py install -O1 --root $(DESTDIR)
	make install -C doc

.PHONY: get-sources
get-sources: GIT_REPOS := $(addprefix $(SRC_DIR)/,$(MGMT_SALT_COMPONENTS) mgmt-salt-app-saltstack)
get-sources:
	@set -a; \
	pushd $(BUILDER_DIR) &> /dev/null; \
	SCRIPT_DIR=$(BUILDER_DIR)/scripts; \
	SRC_ROOT=$(BUILDER_DIR)/$(SRC_DIR); \
	for REPO in $(GIT_REPOS); do \
		if [ ! -d $$REPO ]; then \
			$$SCRIPT_DIR/get-sources || exit 1; \
		fi; \
	done; \
	popd &> /dev/null

.PHONY: verify-sources
verify-sources:
	@true
