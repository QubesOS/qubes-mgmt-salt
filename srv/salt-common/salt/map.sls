#!pyobjects

class SaltMap(Map):
    # Common package names
    salt_master = 'salt-master'
    salt_minion = 'salt-minion'
    salt_syndic = 'salt-syndic'
    salt_ssh = 'salt-ssh'

    # Generic package names
    class Debian:
        salt = 'salt-common'
        python_dev = 'python-dev'
        python_m2crypto = 'python-m2crypto'
        python_openssl = 'python-openssl'
        libevent_dev = 'libevent-dev'
        installed_by_repo = 'dpkg-query -W salt-minion'

    class Ubuntu:
        __grain__ = 'os'
        salt = 'salt-common'
        python_dev = 'python-dev'
        python_m2crypto = 'python-m2crypto'
        python_openssl = 'python-openssl'
        libevent_dev = 'libevent-dev'
        installed_by_repo = 'dpkg-query -W salt-minion'

    class RedHat:
        salt = 'salt'
        python_dev = 'python-devel'
        python_m2crypto = 'm2crypto'
        python_openssl = 'pyOpenSSL'
        libevent_dev = 'libevent-devel'
        installed_by_repo = 'rpm -q salt'
