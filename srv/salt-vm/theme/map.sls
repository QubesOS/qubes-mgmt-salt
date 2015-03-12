#!pyobjects

class ThemeMap(Map):
    class Debian:
        xdg_qubes_settings = '/etc/X11/Xsession.d/25xdg-qubes-settings'
        theme_dependencies = [ 'gnome-tweak-tool', 
                               'dconf-editor', 
                               'xdg-user-dirs', 
                               'gnome-themes-standard', 
                               'xsettingsd' ]
    class Ubuntu:
        __grain__ = 'os'
        xdg_qubes_settings = '/etc/X11/Xsession.d/25xdg-qubes-settings'
        theme_dependencies = [ 'gnome-tweak-tool ', 
                               'dconf-editor', 
                               'xdg-user-dirs', 
                               'gnome-themes-standard', 
                               'xsettingsd' ]

    class RedHat:
        xdg_qubes_settings = '/etc/X11/xinit/Xclients.d/25xdg-qubes-settings'
        theme_dependencies = [ 'freetype-freeworld', 
                               'gnome-tweak-tool', 
                               'dconf-editor', 
                               'xdg-user-dirs', 
                               'gnome-themes-standard', 
                               'xsettingsd' ]
