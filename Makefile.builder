ifeq ($(PACKAGE_SET),dom0)
  RPM_SPEC_FILES := rpm_spec/salt-dom0.spec

else ifeq ($(PACKAGE_SET),vm)
  #ifneq ($(filter $(DISTRIBUTION), debian),)
  #  DEBIAN_BUILD_DIRS := debian.debian/debian
  #  SOURCE_COPY_IN := source-debian-quilt-copy-in
  #else ifneq ($(filter $(DISTRIBUTION), qubuntu),)
  #  DEBIAN_BUILD_DIRS := debian.qubuntu/debian
  #  SOURCE_COPY_IN := source-debian-quilt-copy-in
  #endif

  RPM_SPEC_FILES := rpm_spec/salt-vm.spec
endif

source-debian-quilt-copy-in: DEBIAN = $(DEBIAN_BUILD_DIRS)/..
source-debian-quilt-copy-in: VERSION = $(shell $(DEBIAN_PARSER) changelog --package-version $(ORIG_SRC)/$(DEBIAN_BUILD_DIRS)/changelog)
source-debian-quilt-copy-in: NAME = $(shell $(DEBIAN_PARSER) changelog --package-name $(ORIG_SRC)/$(DEBIAN_BUILD_DIRS)/changelog)
source-debian-quilt-copy-in: ORIG_FILE = "$(CHROOT_DIR)/$(DIST_SRC)/../$(NAME)_$(VERSION).orig.tar.gz"
source-debian-quilt-copy-in:
	-$(shell $(ORIG_SRC)/debian-quilt $(ORIG_SRC)/series-debian-vm.conf $(CHROOT_DIR)/$(DIST_SRC)/$(DEBIAN)/patches)
	tar cfz $(ORIG_FILE) --exclude-vcs --exclude=rpm --exclude=pkgs --exclude=deb --exclude=debian --exclude=debian.debian --exclude=debian.qubuntu -C $(CHROOT_DIR)/$(DIST_SRC) .
	tar xfz $(ORIG_FILE) -C $(CHROOT_DIR)/$(DIST_SRC)/$(DEBIAN) --strip-components=1 
	mv $(ORIG_FILE) $(CHROOT_DIR)/$(DIST_SRC)

# vim: filetype=make
