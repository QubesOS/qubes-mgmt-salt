#!yamlscript

##
# theme
#
# use 'xrdb -query' to check rendering results
##

$defaults: False
$pillars:
  auto: False

$python: |
    from salt://theme/map.sls import ThemeMap

# TODO:
# Look into Infinity fonts for Debian
# http://forums.debian.net/viewtopic.php?f=16&t=88545
#
# REbuild Debian font cache after installing fonts:
# fc-cache -fv  rebuilds cached list of fonts fc-cache -fv  rebuilds cached list of fonts 

$with theme-dependencies:
  pkg.installed:
    - names: $ThemeMap.theme_dependencies

  gsettings set org.gnome.settings-daemon.plugins.xsettings hinting slight:
    cmd.run: 
      - onlyif: /bin/bash -c "[ $(gsettings get org.gnome.settings-daemon.plugins.xsettings hinting) != 'slight' ]"

  gsettings set org.gnome.settings-daemon.plugins.xsettings antialiasing rgba:
    cmd.run:
      - onlyif: /bin/bash -c "[ $(gsettings get org.gnome.settings-daemon.plugins.xsettings antialiasing) != 'rgba' ]"

  X11_configuration: 
    file.managed:
      - __id__: $ThemeMap.xdg_qubes_settings
      - source: salt://theme/files/25xdg-qubes-settings
      - user: root
      - group: root
      - mode: 644

  /etc/xdg/fonts.conf:
    file.managed:
      - source: salt://theme/files/fonts.conf
      - user: root
      - group: root
      - mode: 644

  /etc/xdg/Xresources:
    file.managed:
      - source: salt://theme/files/Xresources
      - user: root
      - group: root
      - mode: 644

  /etc/xdg/xsettingsd:
    file.managed:
      - source: salt://theme/files/xsettingsd
      - user: root
      - group: root
      - mode: 644

  # Fix for blurry fonts in Fedora 20
  $if grains('os') == 'Fedora' and grains('osmajorrelease') == '20':
    /etc/xdg/fedora-font-fix.conf:
      file.managed:
        - source: salt://theme/files/fedora-font-fix.conf
        - makedirs: True
        - user: root
        - group: root
        - mode: 644
