#
# salt-call --local --out=yaml state.show_sls tests_yamlscript test
#
# salt-call --local state.highstate test
# salt '*' state.highstate test -l debug
#

test:
  '*':
    - tests_yamlscript
    #- tests_yamlscript.default
