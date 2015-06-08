# Locales
# =======
#
# Some basic info:
# ----------------
# localectl list-locales | grep -i utf8 | grep -i us
# localectl set-locale en_US.utf8
# touch  /etc/sysconfig/i18n
#
# Fedora
# ------
# localectl set-locale LANG=en_US.utf8
#
# Debian Jessie:
# --------------
# localedef -f UTF-8 -i en_US -c en_US.UTF-8
# localectl set-locale LANG=en_US.utf8
#
# Not needed?
# update-locale LC_ALL=en_US.UTF-8
#
en_US.utf8:
  locale.system

