###!yamlscript

#===============================================================================
# NOTE:  BUG IN SALT
# ------------------
# The pillar file must be named differently than any state file if it is
# yamlscript otherwise SALT will copy THIS file over the original state file in
# the cache:
#   /var/cache/salt/minion/files/base/users_test/init.sls
#
# A workaround would be to name this file
#   /srv/pillar/users_test/users.sls
# AND NOT:
#   /srv/pillar/users_test/init.sls
#
# And don't foget to update the pillar top file to include 'user-test.pillar'
#===============================================================================

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

users_pillar:
  mel:
    # Notice how there are no hyphens ('-') before keywords and only keywords with a list
    # will have them.  Be careful not to include them or you will get errors!!!
    uid: 400
    system: True
    #home: None
    createhome: True
    shell: '/bin/bash'
    groups:
      - 'sudo'
      - 'shadow'
    # Primary group
    user.group:
      name: 'users'
      gid: 444
      system: True
    # User home directory
    user.file:
      mode: 777
    sudo:
      user: True
      rules:
        - 'ALL=(ALL:ALL) NOPASSWD: ALL'
    ssh:
      save_keys:        True
      key_type:         'rsa'
      keys:
        private: |
          -----BEGIN RSA PRIVATE KEY-----
          MIIEpAIBAAKCAQEAynOcKwXp1G8Bvox16ltiE2XzOjLz6QCBBrp22SlZtQ01s+l+
          N5uWJttp6Shn5xQzvsR7kD1BSovCmwCA0a3smKnUoTMIz1DVFKUV91ULrqgv8+OR
          xxKn771nHzp7t3kQ3cP/8sSS/mvv72axaM7uKtgd8dyQI9fRgnovR40TXUTp5q9E
          ZRH6d2qr0vJ/dEIAoZdZ9mYJozY/tPYIBKFwT76H/6R0KoXfC7+MBeteejOyZDxv
          a4PMTb+PLW302Ko7tvOXJKDVYbpubUSlSKpp98T/Z3QIrV7xzw3HgW4T2iDqciOb
          Kf/vYRJ+zGhcXsJYkPoNQ8ZIBHRkdTnqT/V9UwIDAQABAoIBAEFKp8L4VUE9y8I4
          ao76idbXumm6pQ8wKmyRFmNTAqtxZzBuzVYBx5sgiDe54EiWK1oK5A7Qso3oJQr4
          TpNRFEzn+LtESkMSPqY516u8sdfSRiTR7+HUEnUvEGLx6ZRyZw4eeB1DaGTFSsxa
          wjybABSxPncSOypUIC2EWlspFGWvkICJDdOUCTU4KoX/IqP9f/XRupne0JBbs4v1
          H6MZPpXOrhSTb8fHSIZAMGQcXnDwpDsrOfANVQALtO5Lhsb/eig7ymEotEm21OZF
          PTG6omzHwcXClmyoI3d0gu7M8JlMlU4Td8sJNl06z2gKyKzUHusyqwZcemNPp1Ys
          +7M2aoECgYEA+jBCxXAwm/Ihyy9K7Zsri/M+hfUQ9voqgbIYNkj4vp4omfLrWdfg
          RWN1AYkPhaYuhIH66uZff37wLBUyuR0imdiu+wkwWfpKhsgrLHHUPbZIV45ArCF2
          cic0AgCwly8BhIUKvUw6X+rVefPLoqrSc990cPj8Dc23ijDzvpV0wN8CgYEAzyd7
          oa+sgLW3V6ZxyNjkaNHKYrCZvi1B9PSdVvZ23nikzgjULldn+HOq+B9L1AQXhuKm
          a/cylFlc/Tt+/9HvGoHzYQmSt6TtsWsIYFZB3wlbiN8nx7kUS1Yq2EK6ZMGjAA5S
          vVPHezq61MBDxBNSZDebbwdz+wo80g6Kjo90jg0CgYEA0GEL7BhiVDDa1rnAJaDd
          J0Zk5/vSsnJwnu9v3R7wFwvx8y9xuLXl9MU+uhWnWQCts+3yyF0yYyWd8omBYs8S
          d6MTMsFXhUnDcvkbhHwWc4P0QwCXewav+aoPVi+u5WzgTbjl1f68jBEy1s0o6YZv
          nNUbzdCDVxfla/MTwMQIp28CgYBFw39AYYBPzGLVcumJAXpSzqxA9kagpG89BpBi
          dBhuLeUauiBzBt6t7o5ah3erDEG8HGJ9o7919G57nejUUKgcnj0PpgCyNioSgQBO
          KV5/tZANFVI5UdxCzt8Y+8f4HLo/T5OPzUI1/v5inel0hClQNOX0y2bE2ZrIBzuk
          bS2MlQKBgQDcYhpmx/s+lBWCDUqyRjBWgGf48TvSod3xg9CUBsYFu183UWblgr6C
          5RZSHtxWVLmRPsQluxy/uu53mM8EfXaWCC+JrmfU4XGzEGva6/U32BodsNhEi0TW
          dQ7X/Qimh+BZr9kqEcYbLkETVtfjRIQT4Zh0ZwCzxkclrhOWfzCsSA==
          -----END RSA PRIVATE KEY-----
        public: 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKc5wrBenUbwG+jHXqW2ITZfM6MvPpAIEGunbZKVm1DTWz6X43m5Ym22npKGfnFDO+xHuQPUFKi8KbAIDRreyYqdShMwjPUNUUpRX3VQuuqC/z45HHEqfvvWcfOnu3eRDdw//yxJL+a+/vZrFozu4q2B3x3JAj19GCei9HjRNdROnmr0RlEfp3aqvS8n90QgChl1n2ZgmjNj+09ggEoXBPvof/pHQqhd8Lv4wF6156M7JkPG9rg8xNv48tbfTYqju285ckoNVhum5tRKVIqmn3xP9ndAitXvHPDceBbhPaIOpyI5sp/+9hEn7MaFxewliQ+g1DxkgEdGR1OepP9X1T root@plex'
    auth_present.ssh_auth:
      #name: 'aaaab3nZAc1KC3maaacbal0Sq9Fj5ByteYy=='
      names:
        - 'AAAAB3NzaC1kc3MAAACBAL0sQ9fJ5bYTEyY=='
        - 'ssh-dss AAAAB3NzaCL0sQ9fJ5bYTEyY== user@domain'
        - 'option3="value3" ssh-dss AAAAB3NzaC1kcQ9J5bYTEyY== other@testdomain'
        - 'AAAAB3NzaC1kcQ9fJFF435bYTEyY== newcomment'
      comment:        'hello@there'
    auth_absent.ssh_auth:
      name: 'DDdDDAAAAB3NzaC1kc3MAAACBAL0sQ9fJ5bYTEyY=='
      #name: 'AAAAB3NzaC1kcQ9fJFF435bYTEyY=='
      #name: 'aaaab3nZAc1KC3maaacbal0Sq9Fj5ByteYy=='
      #names:
      #  - 'option3="value3" ssh-dss AAAAB3NzaC1kcQ9J5bYTEyY== other@testdomain'
      #  - 'AAAAB3NzaC1kcQ9fJFF435bYTEyY== newcomment'

  bobby:
    uid: 4000
  #carl:
  admin:
    uid: 98
    createhome: False
    # Real password string starts with a '$' so it needs to be escaped with another '$'
    # so it won't be seen as a token '$$...'
    password: $$6$v.tjGO0O$Hs7/xYmNR/pZLZZrxuihexeRWL8bFsKD9zRqAu7.X428xxzmbzUxDMViZbMBI.p5ij.npHYsTKDME5B9Q5aOF1
    home: /
    shell: /bin/bash
    system: True
    sudouser: True
    sudo_rules:
      - 'ALL=(ALL:ALL) NOPASSWD: ALL'
    user.group:
      name: admin
      gid: 98
      system: True
    groups:
      - sudo
      - shadow
  guest:
    fullname: guest
    uid: 99
    createhome: False
    home: /bin/false
    shell: /bin/false
    system: True
    user.group:
      name: guest
      gid: 99
      system: True

#tester_renamed:
#  file:
#    makedirs: False
#    source: code

#tester_renamed:
#  tester_renamed.file:
#    makedirs: False
#    source: code

tester_renamed:
  makedirs: False
  source: code
  # Real password string starts with two '$$ 'so it needs to be escaped with a '\'
  # so it won't be seen as a token '\$$...'
  password: \$$6$v.tjGO0O$Hs7/xYmNR/pZLZZrxuihexeRWL8bFsKD9zRqAu7.X428xxzmbzUxDMViZbMBI.p5ij.npHYsTKDME5B9Q5aOF1

#absent_users:
#  - carl
#  - frank

#absent_groups:
#  - carl
#  - frank

# Testing calling pillar from a ptyhon function
my_ip_range: 10.0.0.10

# Testing function embeded dirrectly from scalar
CONFIG_PATH: C:/config
HOME_PATH: $pillar('CONFIG_PATH') + '/home'
#SAME_PATH: $CONFIG_PATH + '/home'

# A senerio for a salt user
EMS_SERVICE_LIST:
  - MESSAGING
  - TEST

EMS_MESSAGING_PRIMARYSERVER: primaryserver
EMS_MESSAGING_PRIMARYPORT: 7921
EMS_MESSAGING_SECONDARYSERVER: secondaryserver
EMS_MESSAGING_SECONDARYPORT: 7922

EMS_TEST_PRIMARYSERVER: primaryserver
EMS_TEST_PRIMARYPORT: 7931
EMS_TEST_SECONDARYSERVER: secondaryserver
EMS_TEST_SECONDARYPORT: 7932

EMS_SERVICE_TYPE: primary

EMS_SERVICE:
  MESSAGING:
    PRIMARYSERVER: primaryserver
    PRIMARYPORT: 7921
    SECONDARYSERVER: secondaryserver
    SECONDARYPORT: 7922
  TEST:
    PRIMARYSERVER: primaryserver
    PRIMARYPORT: 7931
    SECONDARYSERVER: secondaryserver
    SECONDARYPORT: 7932
