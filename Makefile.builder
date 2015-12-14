# vim: filetype=make

MGMT_PLUGIN_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
_CHROOT_SRC = $(CHROOT_DIR)/$(DIST_SRC)

get-mgmt-debian-dir = \
	$(strip $(if $(wildcard $(ORIG_SRC)/debian.$(PACKAGE_SET)/.), \
	    debian.$(PACKAGE_SET), \
	    $(if $(wildcard $(ORIG_SRC)/debian), debian) \
	))

get-mgmt-rpm-spec = \
	$(eval _spec_prefix = rpm_spec/qubes-$(COMPONENT)) \
	$(strip \
	    $(if $(wildcard $(ORIG_SRC)/$(_spec_prefix).spec), $(_spec_prefix).spec) \
	    $(if $(wildcard $(ORIG_SRC)/$(_spec_prefix)-$(PACKAGE_SET).spec), $(_spec_prefix)-$(PACKAGE_SET).spec) \
	)

ifndef LOADING_PLUGINS
    SOURCE_COPY_IN := mgmt-salt-copy-in
    ifeq ($(PACKAGE_SET),dom0)
        ifneq ($(filter $(DISTRIBUTION), debian qubuntu),)
            DEBIAN_BUILD_DIRS := $(call get-mgmt-debian-dir)
        else
            RPM_SPEC_FILES := $(call get-mgmt-rpm-spec)
        endif
    else ifeq ($(PACKAGE_SET),vm)
        ifneq ($(filter $(DISTRIBUTION), debian qubuntu),)
            DEBIAN_BUILD_DIRS := $(call get-mgmt-debian-dir)
        else
            RPM_SPEC_FILES := $(call get-mgmt-rpm-spec)
        endif
    endif
endif

# =========================================================
# Generic parse-formula targets for all mgmt-salt* packages
# =========================================================
# All other 'mgmt-salt' Makefile.builder set:
#     SOURCE_COPY_IN := mgmt-salt-copy-in
#
# 'mgmt-salt-copy-in' will create/copy mgmt specific Makefiles, copy any
# file/directory templates (IE: FORMULA.vm to FORMULA) and prepare Debian
# builds (IE: Create *orig.tar.gz file)

# Move any existing template files or directories into place. If $(PACKAGE_SET)
# is 'vm' all '*.vm' files and directories in the root chroot package directory
# will be copied dropping the '.vm' extension. Same for '*.dom0'
mgmt-salt-copy-templates::
	@$(eval package_set_templates = $(wildcard $(_CHROOT_SRC)/*.$(PACKAGE_SET))) \
	$(foreach template, $(package_set_templates), \
	     $(shell cp -a $(template) $(basename $(template))) \
	) 

# Parse the 'FORMULA' and 'FORMULA-DEFAULTS' yaml configuration files and dump
# the configuration values to a Makefile compatible key+value format to
# 'Makefile.vars'
mgmt-salt-create-vars-makefile::
	@$(eval mgmt_parser_paths = $(MGMT_PLUGIN_DIR)/FORMULA-DEFAULTS $(_CHROOT_SRC)/FORMULA) \
	$(eval mgmt_parser_outfile = $(_CHROOT_SRC)/Makefile.vars) \
	$(eval mgmt_parser_environ = VERBOSE) \
	"$(MGMT_PLUGIN_DIR)yaml-dumper" --env $(mgmt_parser_environ) \
	                                --outfile $(mgmt_parser_outfile) \
	                                -- $(mgmt_parser_paths)

# Copy the master 'Makefile.install' to the package's chroot environment
mgmt-salt-copy-master-makefile::
	@$(if $(filter-out $(SOURCE_COPY_IN), source-mgmt-salt-copy-in), \
	    $(shell cp --remove-destination -p $(MGMT_PLUGIN_DIR)Makefile.install \
			$(_CHROOT_SRC)) \
	) 

# Copy / create all required build Makefiles for each mgmt-salt* COMPONENT
mgmt-salt-makefiles:: mgmt-salt-copy-master-makefile mgmt-salt-create-vars-makefile
	@true

# Applies any Debian patches, then creates a Debian 
# <package_name>_<version>.orig.tar.gz file to represent upstream orig file
mgmt-salt-debian-prep::
	@$(if $(filter $(DISTRIBUTION), debian qubuntu), \
	    $(eval changelog  = $(ORIG_SRC)/$(DEBIAN_BUILD_DIRS)/changelog) \
	    $(eval version    = $(shell $(DEBIAN_PARSER) changelog --package-version $(changelog))) \
	    $(eval package    = $(shell $(DEBIAN_PARSER) changelog --package-name $(changelog))) \
	    $(eval orig_file  = $(_CHROOT_SRC)/../$(package)_$(version).orig.tar.gz) \
	    $(eval tar_opts   = --exclude-vcs --exclude=./pkgs --exclude=./*.vm --exclude=./*.dom0 --exclude=./debian* --exclude=./rpm_spec) \
	    -$(shell $(MGMT_PLUGIN_DIR)/debian-quilt $(ORIG_SRC)/series-debian-vm.conf $(_CHROOT_SRC)/debian/patches) \
	    $(shell tar cfz $(orig_file) $(tar_opts) -C $(_CHROOT_SRC) .) \
	)

# 'SOURCE-COPY-IN' provided by all mgmt-salt* packages
mgmt-salt-copy-in:: mgmt-salt-copy-templates mgmt-salt-makefiles mgmt-salt-debian-prep
	@true

# 'SOURCE-COPY-IN' for this 'salt-mgmt' package
source-mgmt-salt-copy-in:: mgmt-salt-copy-in
	@true
