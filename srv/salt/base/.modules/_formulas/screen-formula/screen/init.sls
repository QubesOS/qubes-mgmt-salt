screen:
  pkg.installed

/usr/local/etc/.screenrc:
    file:
        - managed
        - source: salt://screen/.screenrc
        - require:
            - pkg: screen
