###
#  Users Pillar
#  ============
#  Add/remove users from system
#
#  Notes:
#  ------
#  - It's best to quote strings
#
###

# If the state file contains a #!yamlscript shebang, any values set in the
# pillar that have an exact (or aliased) structure as the state file will be
# automatically applied.  This means you can just add the shebang and enter
# pillar data and thats it so you can easily use existing statefiles.
#
# You can even add it to a #!jinja|yaml|yamlscript statefile, so long as
# the input is valid yaml or yamlscript
#
# If your pillar is not named after the statefile (users.init / users.init),
# simplely add pillar: <pillar_name> in the state file.

# All state values, including ones dynamicly created can be accessed (set or get)
# by dot notation refering to $id.state.key = value.  scalar values beginning
# with a $ are evaluated and contain any valid valuation like:
# ...: $id.state.name
# ...: $2 + 2
# ...: $some_value_set_in_python_before
# ...: $'{0}_name'.format(some_value)
#
#
# Convenience aliases
# Allows shorter path names to values when looking up pillar values.
# For instance,  currently user.user is aliased to null so when looking up values
# for user.user.uid we only need the structure to look like this:
#
# user.user.uid is the id.state.value in the state file.  they must be the
# same or aliased so values can be automatically found
#
# users:
#   mel:
#     uid: 400
#
# instead of the default of:
#
# users:
#   mel:
#     user.user:
#       uid: 400
# - OR -
#     user:
#       user:
#         uid: 400
#

#groups:
#  shadow:
#    system: True

users:
  qubes:
    uid: 98
    createhome: False
#    password: $6$M6qqa5at$vlJuhZV4JdqIyQdaCdteCtturdi7v.Er2m/r4d1Y7HOgF9l/emXBaJHiOwsDveXS.t1Q58kYXqubNSa7JW8qM.
    shell: None
    system: True
    sudouser: True
    sudo_rules:
      - 'ALL=(ALL:ALL) NOPASSWD: ALL'
    user.group:
      name: qubes
      gid: 98
      system: True
#    groups:
#      - sudo
#      - shadow
