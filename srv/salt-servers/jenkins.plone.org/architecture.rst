jenkins.plone.org architecture
==============================

Proposal for a new jenkins.plone.org architecture. For an example of how this
could look like see:

http://jenkins.timostollenwerk.net/jenkins/view/Plone-4.2/?

The general idea is that the coredev build jobs only run buildout and that each
package has its own job and test run/failure. The jobs have to be created 
automatically by a script that gets its informations about what jobs are to 
build and how to build from parsing the coredev buildout configuration. This 
might happen as a Jenkins job or from the outside by using the Jenkins API.

The first step would be to set this up by hand to see if this could actually
work and then think about ways how to automate this.


Jenkins Jobs Overview
---------------------

- COREDEV VIEW: Each Plone coredev branch has its own view (e.g. "Plone-4.2")

- COREDEV BUILD JOB: Each Plone coredev view has a main job that checks out 
  its buildout.coredev branch and runs buildout (e.g. 
  views/Plone-4.2/jobs/Plone-4.2-build). This job could trigger the creation
  of the coredev package jobs.

- COREDEV PACKAGE JOBS: Each package in the coredev (e.g. Products.CMFPlone or
  plone.app.layout has its own Jenkins job that uses the workspace of the
  coredev build job from above. 


Jenkins Job Configuration
-------------------------

Coredev build job:

- Project name: Plone-4.2
- Advanced Project Options -> Use custom workspace: plone-4.2
- Source Code Managment -> Git -> URL of the repository: git://github.com/plone/buildout.coredev.git
- Build -> Excecute Shell:
    git checkout 4.2
    python2.6 bootstrap.py
    bin/buildout -c hudson.cfg
- Post-build Actions -> Build other projects: plone.app.layout, Products.CMFPlone, etc.

Package job:

- Project name: Products.CMFPlone
- Source Code Management -> Git -> URL of the repository: git://github.com/plone/Products.CMFPlone.git
- Build Triggers -> Build after other projects are build: Plone-4.2
- Build -> Execute Shell:
    git checkout master
    git pull
    ../../bin/xmltest -s Products.CMFPlone
- Publish JUnit test result report: **/parts/xmltest/*.xml


Github post-commit hook
-----------------------

- For each commit on buildout.coredev, all coredev build jobs (Plone 4.0, 4.1, i
  4.2) are triggered. In the future we might want to develop some component 
  that only triggers the coredev builds corresponding to the branch that has
  changed.

  One problem with this approach is that we have to run buildout on the coredev
  build job when for instance the dependencies in setup.py of a package
  has been changed. We could avoid this problem by always triggering the 
  coredev package build though.

- For each commit on a package (e.g. Products.CMFPlone, plone.app.layout) the
  corresponding jenkins job is triggered that runs the test for that single
  package only.

Test Coverage and Code Analysis
===============================

- We run test coverage and code analysis for each coredev build/branch. Since
  this is expensive, we run it only on a nightly our hourly basis.

E-Mail Notifications
====================

- We send e-mail notifications for each failed build. This means that we could
  get a lot of emails if the build is completely broken. On the other hand do
  we recieve only emails from packages that are broken.

