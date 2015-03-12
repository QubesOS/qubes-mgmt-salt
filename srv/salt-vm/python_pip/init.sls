#!yamlscript

##
# python-pip
##

$defaults: False
$pillars:
  auto: False

$python: |
    from salt://python_pip/map.sls import PipMap
    
    pip_dependencies = PipMap.python_pip + \
                       PipMap.python_dev + \
                       PipMap.python_virtualenv + \
                       PipMap.build_essential

$with pip-dependencies:
  pkg.installed:
    - names: $pip_dependencies

  virtualenvwrapper:
    pip.installed:
      - wheel
      - pkg: pip-dependencies
