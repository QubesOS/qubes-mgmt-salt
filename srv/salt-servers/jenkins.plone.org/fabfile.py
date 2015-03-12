from fabric.api import *
from fabric.contrib.files import sed, append, exists, contains

import ConfigParser

env.user = 'timo'
env.hosts = [
    # Slave 1 (Ian)
    '152.19.4.89',
    # Slave 2 (Ian)
    '152.19.4.98',
    # Slave 3 (Wyn)
    '81.90.66.139:75',
    # Slave 4 (Timo)
    #'88.198.77.5',
    # Slave 5 (Timo)
    '188.40.97.212',
]

env.home = "/home/jenkins"

auth_config = ConfigParser.ConfigParser()
auth_config.readfp(open('auth.cfg'))
jenkins_username = auth_config.get("buildout", "jenkins-username")
jenkins_password = auth_config.get("buildout", "jenkins-password")
jenkins_apitoken = auth_config.get("buildout", "jenkins-apitoken")


def setup():
    """Set up slave for jenkins.plone.org.
    """
    # Update system
    sudo('apt-get update -y')
    sudo('apt-get dist-upgrade -y')
    sudo('apt-get autoremove -y')
    # Basics
    sudo('apt-get install -y build-essential')
    sudo('apt-get install -y htop')
    # Remove zope.interface to avoid buildout problems
    sudo('apt-get remove -y python-zope.interface')
    # Time sync
    sudo('apt-get install -y ntp')
    # Keep /tmp clean
    sudo('apt-get install -y tmpreaper')
    # for add-apt-repository
    sudo('apt-get install -y python-software-properties')
    # VCS
    sudo('apt-get install -y git-core')
    sudo('apt-get install -y subversion')
    sudo('apt-get install -y libxml2-utils')
    # Word support
    sudo('apt-get install -y wv')
    # PDF support
    sudo('apt-get install -y poppler-utils')
    # bz2 support to extract pypi packages
    sudo('apt-get install -y libbz2-dev')
    # Code analysis
    sudo('apt-get install -y ohcount')
    sudo('apt-get install -y sloccount')
    # Mockup
    sudo('apt-get install -y phantomjs')
    # Robot Framework (This dependency is only necessary when
    # 'Library  Dialogs' are added to the robot setup, which shouldn't happen)
    sudo('apt-get install -y python-tk')
    # Java is needed to connect the Jenkins slaves
    sudo("apt-get install -y openjdk-7-jre")
    # LXML
    sudo('apt-get install -y libxslt1-dev libxml2-dev')
    # graphviz
    # XXX: graphviz currently breaks the robot results because they include all
    # circular deps warnings
    #sudo('apt-get install -y graphviz')
    # LOCALES
    sudo('echo "en_GB.ISO8859-15 ISO-8859-15" >> /var/lib/locales/supported.d/local')
    sudo('echo "en_US.ISO8859-15 ISO-8859-15" >> /var/lib/locales/supported.d/local')
    sudo('echo "en_US.ISO-8859-1 ISO-8859-1" >> /var/lib/locales/supported.d/local')
    sudo('dpkg-reconfigure locales')

    setup_node()
    setup_jenkins_user()
    setup_jenkins_ssh()
    setup_buildout_cache()
    setup_git_config()
    setup_tmpreaper()

    setup_python_26()
    setup_python_27()

    setup_firefox()
    setup_chrome()

    setup_xfvb()

    setup_clean()


def setup_node():
    # Remove sys nodejs
    sudo('apt-get remove -y nodejs npm')
    # Install Node 0.8.9
    sudo('wget http://nodejs.org/dist/v0.8.9/node-v0.8.9.tar.gz')
    sudo('tar xfvz node-v0.8.9.tar.gz')
    with cd('node-v0.8.9'):
        sudo('./configure')
        sudo('make')
        sudo('make install')
    sudo('rm -rf node-v0.8.9/')
    # XXX: Why is this necessary?
    sudo('npm install -g grunt-cli')
    # Set npm config registry
    sudo('npm config set registry http://registry.npmjs.org/')
    # Install packages with npm
    sudo('npm install -g jslint')
    sudo('npm install -g jshint')
    sudo('npm install -g csslint')


def setup_git_config():
    """Set up a git configuration file (.gitconfig).
    """
    put('etc/.gitconfig', '/tmp')
    sudo('mv /tmp/.gitconfig /home/jenkins/')
    sudo('chown jenkins:jenkins /home/jenkins/.gitconfig')


def setup_tmpreaper():
    put('etc/tmpreaper.conf', '/tmp')
    sudo('mv /tmp/tmpreaper.conf /etc/')


def test_setup_python_26():
    """Test Python 2.6 setup.
    """
    with settings(warn_only=True):
        result = run('echo "print(True)" | python2.6')
    if result.failed:
        abort("Python 2.6 is not properly installed!")

    with settings(warn_only=True):
        result = run('echo "import hashlib" | python2.6')
    if result.failed:
        abort("Python 2.6: Haslib is not properly installed!")

    with settings(warn_only=True):
        run('echo "import lxml" | python2.6')
    if result.failed:
        abort("Python 2.6: LXML is not properly installed!")

    with settings(warn_only=True):
        run('echo "import _imaging" | python2.6')
    if result.failed:
        abort("Python 2.6: PIL is not properly installed!")

    with settings(warn_only=True):
        sudo("""echo "from urllib import urlopen; from cStringIO import StringIO; from PIL import Image; print(Image.open(StringIO(urlopen('http://plone.org/logo.jpg').read())).format)" | python2.6""")
    if result.failed:
        abort("Python 2.6: PIL JPEG support is not properly installed!")

    with settings(warn_only=True):
        sudo('echo "from urllib import urlopen; from cStringIO import StringIO; from PIL import Image; print(Image.open(StringIO(urlopen(\'http://plone.org/logo.png\').read())).format)" | python2.6')
    if result.failed:
        abort("Python 2.6: PIL PNG support is not properly installed!")


def setup_python_26():
    """Install Python 2.6.
    """
    # Python 2.6
    sudo('add-apt-repository -y ppa:fkrull/deadsnakes')
    sudo('apt-get update')
    sudo('apt-get install -y python2.6 python2.6-dev')
    # PIL
    #http://www.sandersnewmedia.com/why/2012/04/16/installing-pil-virtualenv-ubuntu-1204-precise-pangolin/
    sudo('apt-get install -y zlib1g-dev')
    sudo('apt-get install -y libfreetype6 libfreetype6-dev')
    sudo('apt-get install -y libjpeg-dev')
    if not exists('/usr/lib/libfreetype.so'):
        sudo('ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/libfreetype.so')
    if not exists('/usr/lib/libjpeg.so'):
        sudo('ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/libjpeg.so')
    if not exists('/usr/lib/libz.so'):
        sudo('ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/libz.so')
    if not exists('/root/tmp'):
        sudo('mkdir /root/tmp')
    with cd('/root/tmp'):
        sudo('wget http://effbot.org/downloads/Imaging-1.1.7.tar.gz')
        sudo('tar xfvz Imaging-1.1.7.tar.gz')
    with cd('/root/tmp/Imaging-1.1.7/'):
        sudo('/usr/bin/python2.6 setup.py install')
    # Install BZ2 Support
    with cd('/root/tmp'):
        sudo('wget http://labix.org/download/python-bz2/python-bz2-1.1.tar.bz2')
        sudo('tar xfvj python-bz2-1.1.tar.bz2')
    with cd('/root/tmp/python-bz2-1.1/'):
        sudo('/usr/bin/python2.6 setup.py install')
    # Install LXML
    sudo('apt-get install -y libxslt1-dev libxml2-dev')
    with cd('/root/tmp'):
        sudo('wget http://pypi.python.org/packages/source/l/lxml/lxml-2.3.6.tar.gz')
        sudo('tar xfvz lxml-2.3.6.tar.gz')
    with cd('/root/tmp/lxml-2.3.6/'):
        sudo('/usr/bin/python2.6 setup.py install')
    # Clean up
    sudo('rm -rf /root/tmp')
    test_setup_python_26()


def setup_python_26_old():
    """Install Python 2.6 with Imaging and LXML. This is the old and ugly way
    with patches and stuff.
    """
    # http://ubuntuforums.org/showthread.php?t=1976837
    if exists('/opt/python-2.6', use_sudo=True):
        sudo('rm -rf /opt/python-2.6')
    if exists('/root/tmp', use_sudo=True):
        sudo('rm -rf /root/tmp')
    sudo('mkdir /root/tmp')
    with cd('/root/tmp'):
        sudo('wget http://python.org/ftp/python/2.6.8/Python-2.6.8.tgz')
        sudo('tar xfvz Python-2.6.8.tgz')
    with cd('/root/tmp/Python-2.6.8/'):
        put('etc/setup.py.patch', '/tmp')
        sudo('patch setup.py < /tmp/setup.py.patch')
        put('etc/ssl.patch', '/tmp')
        sudo('patch Modules/_ssl.c < /tmp/ssl.patch')
        sudo('env CPPFLAGS="-I/usr/lib/x86_64-linux-gnu" LDFLAGS="-L/usr/include/x86_64-linux-gnu" ./configure --prefix=/opt/python2.6')
        sudo('make')
        put('etc/ssl.py.patch', '/tmp')
        sudo('patch Lib/ssl.py < /tmp/ssl.py.patch')
        sudo('make install')
    # PIL
    sudo('apt-get install -y zlib1g-dev')
    sudo('apt-get install -y libfreetype6 libfreetype6-dev')
    sudo('apt-get install -y libjpeg-dev')
    #http://www.sandersnewmedia.com/why/2012/04/16/installing-pil-virtualenv-ubuntu-1204-precise-pangolin/
    if not exists('/usr/lib/`uname -i`-linux-gnu/libfreetype.so'):
        sudo('ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/')
    if not exists('/usr/lib/`uname -i`-linux-gnu/libjpeg.so'):
        sudo('ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/')
    if not exists('/usr/lib/`uname -i`-linux-gnu/libz.so'):
        sudo('ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/')
    with cd('/root/tmp'):
        sudo('wget http://effbot.org/downloads/Imaging-1.1.7.tar.gz')
        sudo('tar xfvz Imaging-1.1.7.tar.gz')
    with cd('/root/tmp/Imaging-1.1.7/'):
        sudo('/opt/python2.6/bin/python setup.py install')
    # Install BZ2 Support
    with cd('/root/tmp'):
        sudo('wget http://labix.org/download/python-bz2/python-bz2-1.1.tar.bz2')
        sudo('tar xfvj python-bz2-1.1.tar.bz2')
    with cd('/root/tmp/python-bz2-1.1/'):
        sudo('/opt/python2.6/bin/python setup.py install')
    # Install LXML
    sudo('apt-get install -y libxslt1-dev libxml2-dev')
    with cd('/root/tmp'):
        sudo('wget http://pypi.python.org/packages/source/l/lxml/lxml-2.3.6.tar.gz')
        sudo('tar xfvz lxml-2.3.6.tar.gz')
    with cd('/root/tmp/lxml-2.3.6/'):
        sudo('/opt/python2.6/bin/python setup.py install')
    # Create Symlink
    if not exists('/usr/local/bin/python2.6'):
        sudo('ln -s /opt/python2.6/bin/python /usr/local/bin/python2.6')
    # Clean up
    sudo('rm -rf /root/tmp')
    # Install Setuptools
    sudo('wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python2.6')
    test_setup_python_26()


def test_setup_python_27():
    """Test Python 2.7 setup.
    """
    with settings(warn_only=True):
        result = run('echo "print(True)" | python2.7')
    if result.failed:
        abort("Python 2.7 is not properly installed!")

    with settings(warn_only=True):
        result = run('echo "import hashlib" | python2.7')
    if result.failed:
        abort("Python 2.7: Haslib is not properly installed!")

    with settings(warn_only=True):
        run('echo "import lxml" | python2.7')
    if result.failed:
        abort("Python 2.7: LXML is not properly installed!")

    with settings(warn_only=True):
        run('echo "import _imaging" | python2.7')
    if result.failed:
        abort("Python 2.7: PIL is not properly installed!")


def setup_python_27():
    """Install Python 2.7 with Imaging and LXML.
    """
    sudo('apt-get install -y python2.7')
    sudo('apt-get install -y python2.7-dev')
    # PIL
    sudo('apt-get install -y python-imaging')
    # LXML
    sudo('apt-get install -y python-lxml')
    # Test Coverage
    sudo('apt-get install -y enscript')
    # Install Setuptools
    sudo('wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python2.7')
    test_setup_python_27()


def setup_xfvb():
    #if xvfb_is_properly_installed():
    #    return
    # virtual display
    sudo('apt-get install -y xvfb')
    # installs xclock (to test things are working),
    # and xwd (for taking screenshots)
    sudo('apt-get install -y x11-apps')
    # to avoid warnings when staring xvfb
    sudo('apt-get install -y xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic')
    sudo('apt-get install -y imagemagick')   # for converting screenshots'


def xvfb_is_properly_installed():
    #retval = run('/usr/bin/Xvfb :5 -ac -screen 0 1024x768x8', warn_only=True)
    #if retval.failed:
    #    return True
    retval = run('xclock -display :5.0 &', warn_only=True)
    if retval.failed:
        return True
    retval = run('xwd -root -display :5.0 -out outputfile', warn_only=True)
    if retval.failed:
        return True
    retval = run('convert outputfile outputfile.png', warn_only=True)
    if retval.failed:
        return True
    return


def setup_jenkins_user():
    """Set up jenkins user.
    """
    if not exists('/home/jenkins', use_sudo=True):
        sudo('adduser jenkins --disabled-password --home=/home/jenkins')


def setup_buildout_cache():
    if not exists('/home/jenkins/.buildout/'):
        sudo('mkdir /home/jenkins/.buildout', user='jenkins')
        sudo('mkdir /home/jenkins/.buildout/eggs', user='jenkins')
        sudo('mkdir /home/jenkins/.buildout/downloads', user='jenkins')
    if exists('/home/jenkins/.buildout/default.cfg'):
        sudo('rm /home/jenkins/.buildout/default.cfg', user='jenkins')
    put('etc/default.cfg', '/tmp/')
    sudo('cp /tmp/default.cfg /home/jenkins/.buildout/', user='jenkins')


def setup_jenkins_ssh():
    """Set up ssh key.
    """
    if not exists('/home/jenkins/.ssh', use_sudo=True):
        sudo('mkdir /home/jenkins/.ssh', user='jenkins')
    if not exists('/home/jenkins/.ssh/authorized_keys', use_sudo=True):
        with cd('/home/jenkins/.ssh'):
            sudo(
                'wget https://raw.github.com/plone/jenkins.plone.org/master/jenkins.plone.org.pub',
                user='jenkins'
            )
            sudo('touch authorized_keys', user='jenkins')
            sudo(
                'cat jenkins.plone.org.pub >> authorized_keys', user='jenkins'
            )
            sudo('rm jenkins.plone.org.pub', user='jenkins')
            sudo(
                'chmod g-w /home/jenkins/ /home/jenkins/.ssh /home/jenkins/.ssh/authorized_keys',
                user='jenkins'
            )


def setup_connect_to_master():
    sudo('apt-get install -y openjdk-7-jre')
    if not exists('/home/jenkins/slave.jar', use_sudo=True):
        sudo('wget http://jenkins.plone.org/jnlpJars/slave.jar')
    sudo('java -jar slave.jar -jnlpUrl http://jenkins.plone.org/computer/Slave1/slave-agent.jnlp -jnlpCredentials %s:%s &' % (
        jenkins_username,
        jenkins_apitoken,
    ))


def setup_firefox():
    sudo('apt-get -y install firefox')


def setup_chrome():
    sudo('wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -')
    sudo('echo deb http://dl.google.com/linux/chrome/deb/ stable main > /etc/apt/sources.list.d/google.list')
    sudo('apt-get update')
    sudo('apt-get install -y google-chrome-stable')
    sudo('wget http://chromedriver.googlecode.com/files/chromedriver_linux32_26.0.1383.0.zip')
    sudo('apt-get install -y unzip')
    sudo('unzip chromedriver_linux32_26.0.1383.0.zip')
    sudo('mv chromedriver /usr/local/bin')
    sudo('rm -rf chromedriver*')


# HELPER ---------------------------------------------------------------------

def _sudo_put(source, destination, user):
    put(source, '/tmp')
    sudo('mv /tmp/%s %s' % (source, destination))
    sudo('chown user:user %s' % (user, user, destination))


# TODO -----------------------------------------------------------------------

def setup_users():
    _setup_user(username='ramon', key='ramon.pub')

def _setup_user(username, key):
    # setup user
    if not exists('/home/%s' % username, use_sudo=True):
        sudo('adduser %s --disabled-password --home=/home/%s' % (
            username, username))
    sudo('adduser %s sudo' % username)
    # setup ssh key
    if not exists('/home/%s/.ssh' % username, use_sudo=True):
        sudo('mkdir /home/%s/.ssh' % username, user=username)
    if exists('/home/%s/.ssh/authorized_keys' % username):
        sudo('rm /home/%s/.ssh/authorized_keys' % username)
    with cd('/home/%s/.ssh' % username):
        sudo(
            'wget https://raw.github.com/plone/jenkins.plone.org/master/etc/%s' % key,
            user=username
        )
        sudo('touch authorized_keys', user=username)
        sudo(
            'cat %s >> authorized_keys' % key, user=username
        )
        sudo('rm %s' % key, user=username)
        sudo(
            'chmod g-w /home/%s /home/%s/.ssh /home/%s/.ssh/authorized_keys' % (username, username, username),
            user=username
        )


def setup_eggproxy():
    """Set up collective.eggproxy to make the buildouts faster.
    """
    pass


def setup_munin():
    """Set up munin.
    """
    sudo('apt-get install -y munin munin-node')
    put('etc/munin.conf', '/etc/munin/munin.conf')
    put('etc/munin-node.conf', '/etc/munin/munin-node.conf')
    sudo('/etc/init.d/munin-node restart')

def setup_clean():
    sudo('apt-get --purge -y autoremove')
    sudo('apt-get --purge -y clean')
    sudo('rm -f /var/cache/apt/archives/*.deb')
    sudo('rm -f /var/cache/apt/*cache.bin')
    sudo('rm -f /var/lib/apt/lists/*_Packages')
