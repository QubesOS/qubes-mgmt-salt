#!yamlscript
#
# This is the test template.
#
# See ../init.sls for inline documentation
$defaults : True
$test_file:
  - salt://users/tests.mel
  - salt://users/tests.bobby
  - salt://users/tests.docker

$import: users.default
