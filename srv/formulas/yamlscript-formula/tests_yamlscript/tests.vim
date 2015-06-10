local:
  /etc/vim/vimrc:
    file:
    - group: root
    - makedirs: true
    - mode: 644
    - require:
      - pkg: vim
    - template: jinja
    - user: root
    - absent
    - order: 10001
    __sls__: users
    __env__: base
  vim:
    pkg:
    - name: vim-enhanced
    - pkgs: null
    - purged
    - order: 10000
    __sls__: users
    __env__: base