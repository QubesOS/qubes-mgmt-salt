#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install qubesbuilder rpc policies to allow building a template in a DISPVM
##

# --- Dom0 --------------------------------------------------------------------
$if  __grains__['virtual'] == 'Qubes':
  /etc/qubes-rpc/qubesbuilder.AttachDisk:
    file.managed:
      - source: salt://policy-qubesbuilder/files/qubesbuilder.AttachDisk
      - replace: False
      - makedirs: True
      - user: root
      - group: root
      - mode: 644

  /etc/qubes-rpc/qubesbuilder.ExportDisk:
    file.managed:
      - source: salt://policy-qubesbuilder/files/qubesbuilder.ExportDisk
      - replace: False
      - makedirs: True
      - user: root
      - group: root
      - mode: 644

  /etc/qubes-rpc/policy/qubesbuilder.AttachDisk:
    file.managed:
      - source: salt://policy-qubesbuilder/files/policy/qubesbuilder.AttachDisk
      - replace: False
      - makedirs: True
      - user: root
      - group: qubes
      - mode: 664

  /etc/qubes-rpc/policy/qubesbuilder.ExportDisk:
    file.managed:
      - source: salt://policy-qubesbuilder/files/policy/qubesbuilder.ExportDisk
      - replace: False
      - makedirs: True
      - user: root
      - group: qubes
      - mode: 664

# --- AppVM -------------------------------------------------------------------
$if __grains__['virtual_subtype'] == 'Xen PV DomU':
  /etc/qubes-rpc/qubesbuilder.CopyTemplateBack:
    file.managed:
      - source: salt://policy-qubesbuilder/files/qubesbuilder.CopyTemplateBack
      - replace: False
      - makedirs: True
      - user: root
      - group: root
      - mode: 644

  /etc/qubes-rpc/policy/qubesbuilder.CopyTemplateBack:
    file.managed:
      - source: salt://policy-qubesbuilder/files/policy/qubesbuilder.CopyTemplateBack
      - replace: False
      - makedirs: True
      - user: root
      - group: qubes
      - mode: 664

