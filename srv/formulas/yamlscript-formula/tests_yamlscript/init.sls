#!yamlscript
#
# This is the test template.
#
# See default.sls for inline documentation
$defaults: True
$test_file:
  - salt://tests_yamlscript/tests.tester

$import: tests_yamlscript.default

# Tests to test token replacement recursion
$python: |
    test_value = True

    city = 'Kitchener'
    building = ['Campus 1', '$city']
    a = "A"
    b = "B"
    c = "C"
    d = "D"
    e = "E"
    f = {'f': 'is for fun', 'l': '$lister'}
    g = "G"
    lister = [1, 2, 3, 4, 5, '$a']

    # Test importing salt utils while using a pillar for value
    import salt.utils.ipaddr
    netmask = str(salt.utils.ipaddr.IPNetwork(pillar('my_ip_range')).netmask)

$if test_value:
#$if False:
  tester:
    file:
    - __pillar__:       tester_renamed
    - __alias__:        None
    - name:             $mel_shadow_group.group.name
    - user:             $test_value
    - group:            sudo
    #- test1:            $mel_shadow_group.group.name
    - not_real_key1:    {'wing': 'left', 'floor': 2, 'building': '$building'}
    - not_real_key2:    [$a, [$b, {'c': [$c, $d, $e, [$f, $g]]}]]
    - not_real_key3:    $f
    - netmask:          $netmask
    - if:               True
    - custom:           $mel_user.user.name
    - password:         null
    - contents_pillar:  null
    - makedirs:         true
    - mode:             644
    - require:
      - file: mel_user
    - managed
$elif not test_value:
  tester:
    file:
    - if:               elif not test_value
    - managed
$elif False and test_value:
  tester:
    file:
    - if:               elif test_value
    - managed
$else:
  tester:
    file:
    - if:               else
    - managed
$python: |
    test_value = False

user2:
    user.present:
    - home: $pillar('HOME_PATH')

# ==============================================================================
#!yamlscript
$test_file:
  - salt://tests_yamlscript/tests.ems_service

# EMS_SERVICE Senerio 1
$for ems_service in pillar('EMS_SERVICE_LIST', {}):
  $python: |
      primaryport = pillar('EMS_%s_PRIMARYPORT' % ems_service)
      secondaryport = pillar('EMS_%s_SECONDARYPORT' % ems_service)
      primaryserver = pillar('EMS_%s_PRIMARYSERVER' % ems_service)
      secondaryserver = pillar('EMS_%s_SECONDARYSERVER' % ems_service)

      if pillar('EMS_SERVICE_TYPE') == 'primary':
        ems_listenurl = "tcp://%s:%s" % (primaryserver, primaryport)
        ems_ftactive = "tcp://%s:%s" % (secondaryserver, secondaryport)
        ems_tcp_port = primaryport
      elif pillar('EMS_SERVICE_TYPE') == 'secondary':
        ems_listenurl = "tcp://%s" % secondaryport
        ems_ftactive = "tcp://%s:%s" % (primaryserver, primaryport)
        ems_tcp_port = secondaryport

      ems_service_config.file.text = "%s-%s-%s-%s" % (ems_service,ems_listenurl, ems_ftactive, ems_tcp_port)

  ems_service_config:
    file.append:
     - __id__:           $'{0}_config'.format(ems_service)
     - name:             C:/abc.txt
     - text:             null

$for ems_type, values in pillar('EMS_SERVICE', {}).items():
  ems_service_config_new:
    file.append:
     - __id__: $'{0}_config_new'.format(ems_type)
     - name: C:/abc.txt
     - text: $"{0}-tcp://{1[PRIMARYSERVER]}:{1[PRIMARYPORT]}-tcp://{1[SECONDARYSERVER]}:{1[SECONDARYPORT]}-{1[PRIMARYPORT]}".format(ems_type, values)
