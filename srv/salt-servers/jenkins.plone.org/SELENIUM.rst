==============================================================================
How to install Selenium Server on jenkins.plone.org
==============================================================================

Install virtual display
-----------------------

$ sudo aptitude install xvfb          # virtual display
$ sudo aptitude install x11-apps      # installs xclock (to test things are working), and xwd (for taking screenshots)
$ sudo aptitude install xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic  # to avoid warnings when staring xvfb
$ sudo aptitude install imagemagick   # for converting screenshots


Install Firefox
---------------

$ sudo aptitude install firefox


Start and test virtual display manually
---------------------------------------

$ /usr/bin/Xvfb :5 -ac -screen 0 1024x768x8 &

$ xclock -display :5.0 &
$ xwd -root -display :5.0 -out outputfile
$ convert outputfile outputfile.png

scp outputfile.png to your local machine and you will see a clock in the upper left.


Install and set up Xvfb Jenkins plugin
--------------------------------------

- Install Jenkins xvfb plugin: https://wiki.jenkins-ci.org/display/JENKINS/Xvfb+Plugin
- Jenkins -> Configure Jenkins -> Xvfb Installation: Name: "default", Directory: "/usr/bin"
- Go to Jenkins project: check "Start Xvfb before the build, and shut it down after."


Install Selenium Server
-----------------------

$ wget http://selenium.googlecode.com/files/selenium-server-standalone-2.25.0.jar


Start Selenium Server
---------------------

$ java -jar selenium-server-standalone-2.25.0.jar &
$ export DISPLAY=:5.0 # firefox needs this to know where to find a display to run on

Sources
-------

- http://centripetal.ca/blog/2011/02/07/getting-started-with-selenium-and-jenkins/
