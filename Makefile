_self_path := $(shell readlink -m $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
include $(_self_path)/components.conf

PACKAGE_NAME := qubes-mgmt-salt

RPMS_DIR=rpm/
VERSION := $(shell cat version)
RELEASE := $(shell cat rel)

all:
	@true

help:
	@echo "make all                   -- compile all binaries"
	@echo "make rpms-vm               -- generate binary rpm packages for VM"
	@echo "make rpms-dom0             -- generate binary rpm packages for Dom0"

rpms-dom0:
	PACKAGE_SET=dom0 rpmbuild --define "_rpmdir $(RPMS_DIR)" -bb rpm_spec/$(PACKAGE_NAME).spec

rpms-vm:
	PACKAGE_SET=vm rpmbuild --define "_rpmdir $(RPMS_DIR)" -bb rpm_spec/$(PACKAGE_NAME).spec

install:
	install -d -m 0755 $(DESTDIR)$(BINDIR)
	install -p -m 0755 qubesctl $(DESTDIR)$(BINDIR)/
	install -d -m 0750 $(DESTDIR)$(SYSCONFDIR)/salt
	install -d -m 0750 $(DESTDIR)$(SYSCONFDIR)/salt/minion.d
	install -m 0640 etc/salt/minion.d/* $(DESTDIR)$(SYSCONFDIR)/salt/minion.d/
	@for file in $$(find srv); do \
	    if [ -d "$${file}" ]; then \
	        install -d -m 0750 "$(DESTDIR)/$${file}" ;\
	    else \
	        install -p -m 0640 "$${file}" "$(DESTDIR)/$${file}" ;\
	    fi \
	done

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
