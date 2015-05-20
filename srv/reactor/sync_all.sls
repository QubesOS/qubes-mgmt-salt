# Sync all custom salt modules, grains, etc

sync_all:
  local.saltutil.sync_all:
    - tgt: {{ data['id'] }}

