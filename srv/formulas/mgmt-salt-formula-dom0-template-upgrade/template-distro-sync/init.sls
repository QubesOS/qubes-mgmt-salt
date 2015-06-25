#
# Upgrade template to new distro
#
# Create new state
# qubes-template-distro-sync(oldvm, newvm, fedora_release, qubes_release)
#
# create qvm-block, qvm-trim-template
#
# call via qubesctl sls.single ques-template-distro-sync
# -- or --
# make automatic function; loop though all vm's; get fedora release an upgrade all
# 
# - will need to add outputter so we get back only test, no dict
#
# -- or -- 
#
# read from pillar ... maybe all qubes states could auto read pillar if available
# -- key would be same as directory; maybe env, so for this one
# dom0:template-distro-sync.init.sls
# template-distro-sync.init.sls
# somthing like that ... but c color will be invalid as seperator
# dom0|template-distro-sync.init.sls
# -- use salt://xxx structure
#
# -- or --
# I think yamlscript currently matches on id + state name + value that will be replace unless alias provided
# 
# hrmm. Whonix template... should be pillar ... should be able to define mutiple in pillar ... plus another field
# to determine if to be installed...
# IE: define base templates by type (netvm, proxyvm, whonix-firewall)
#     then
#     state install whonixgw; with required stuff filled in (name only I think; or any overrides to default)
# 
# hrmm...  ok, definitions go in pillar; default template type in state.sls; we loop though
# pillar:
#  vms:
#    sys-whonix:
#      type: whonix-gateway
#      enabled: yes
#      label: red
#   sys-net:
#      type: whonix-gateway
#     

