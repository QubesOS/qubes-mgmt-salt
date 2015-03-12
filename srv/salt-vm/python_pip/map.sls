#!pyobjects

class PipMap(Map):
    # Generic package names
    python_pip = ['python-pip']
    python_virtualenv = ['python-virtualenv']

    class Debian:
        python_dev = ['python-dev']
        build_essential = ['build-essential']

    class Ubuntu:
        __grain__ = 'os'
        python_dev = ['python-dev']
        build_essential = ['build-essential']

    class RedHat:
        python_dev = ['python-devel']
        build_essential = ['make', 'automake', 'gcc', 'gcc-c++', 'kernel-devel']
