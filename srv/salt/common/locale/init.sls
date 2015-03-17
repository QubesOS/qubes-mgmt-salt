# Format for Fedora
#
# localectl list-locales | grep -i utf8 | grep -i us
# localectl set-locale en_US.utf8
# touch  /etc/sysconfig/i18n
#
# localectl set-locale LANG=en_US.utf8
#
en_US.utf8:
  locale.system

#en_US.UTF-8:
#  locale.system
