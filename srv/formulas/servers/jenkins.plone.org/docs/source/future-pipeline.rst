===========
CI pipeline
===========

Investigation done during Plone Conference 2014 by Gil Forcada (@gforcada).


Problem
=======

During the time between a commit is pushed on any random package on Plone and test are run for it,
more commits can sneak in and cause failures,
the first commit could be then blamed for breaking the build, while it has been some other commits.

Think about merging three or four branches in different packages or at release time,
when the release manager does a lot of pushes.


Investigated solution
=====================

Try to freeze the status of ``buildout.coredev`` at the time of each commit,
so that newer commits do not collide with testing the original commit.


Technical details
=================

The solution basically revolves around two Jenkins plugins:
one that allows to get notifications from jenkins on every commit,
and another one that allows to create artifacts from a given workspace and reuse it on donwstream projects.

Follow the following instructions and things should work:

- install on Jenkins `GitHub OAuth Plugin <https://wiki.jenkins-ci.org/display/JENKINS/Github+OAuth+Plugin>`_

  - follow the plugin instructions, which basically mean:
  - createa a GitHub app and set the ``Client ID`` and ``Client Secret`` on Jenkins security configuration
    (enable ``Github Authentication Plugin`` and ``Github Commiter Authorization Strategy``)

- install on Jenkins `GitHub Plugin <https://wiki.jenkins-ci.org/display/JENKINS/GitHub+Plugin>`_

  - follow the plugin instructions,
    be sure to have configured the previous plugin though
  - use the option ``Manually manage hook URLs`` on Jenkins global configuration
  - create a webhook on all repositories meant to trigger ``buildout.coredev`` jobs
    (i.e. all core packages)

- install on Jenkins `Clone Workspace SCM Plugin <https://wiki.jenkins-ci.org/display/JENKINS/Clone+Workspace+SCM+Plugin>`_

- create a Jenkins job for all core packages,
  this will be the job that GitHub webhook will trigger

  - mark the option: ``Build when a change is pushed to GitHub``

  - add a build step that clones ``buildout.coredev`` and runs buildout on it, i.e::

      if [ ! -d "buildout.coredev" ] ; then git clone https://github.com/plone/buildout.coredev.git; fi
      cd buildout.coredev
      git fetch
      python2.7 bootstrap.py
      ./bin/buildout

  - add a post-build action ``Archive for Clone Workspace SCM`` with the following options:

    - ``Files to include in cloned workspace``: ``buildout.coredev/**/*``
    - ``Override Default Ant Excludes``: checked (this is needed so that dot folders, like ``.git``  are archived)


- create as many downstream jobs as needed with the following configuration:

  - in ``Source Code Management`` select ``Clone Workspace`` and on ``Parent Project`` dropdown select the related upstream job
  - add a build step that does something like::

      cd buildout.coredev
      ./bin/test -s PACKAGE_NAME


*voilà* whenever a commit is pushed on a package in GitHub a job is triggerd on Jenkins
which frezees the current state of buildout.coredev and let's other downstream jobs
reuse that buildout.coredev to run as many things as needed.

The cherry on top is that thatnks to ``Archive for Clone Workspace SCM`` the changelog of the upstream job is replicated on downstream jobs.


What this enable?
=================

To get more reliable test runs and early feedback on breakages.

A possible pipeline could be:

- is the package in ``buildout.coredev`` checkouts? If not, abort and send an email
- do tests on the package itself pass? If not, abort and send an email
- run all tests on buildout.coredev
  - and possibly split that into 3 different jobs: unittest, integration and robot framework

Other ideas

- code analysis?
- coverage?
- create eggs if everything works?
- if it's a branch with a certain name on it and tests do pass merge it?
  - this would create a new commit, so it will be already checked again
- report back to github about the results?


Pipeline visualization
======================

There are a few Jenkins plugins that allow to visualize job pipelines,
here are some findings on them:

- `Build Pipeline Plugin <https://wiki.jenkins-ci.org/display/JENKINS/Build+Pipeline+Plugin>`_
  Allows you to create views where you can see the pipeline of a given job and all its downstream jobs

- `Build Graph View Plugin <https://wiki.jenkins-ci.org/display/JENKINS/Build+Graph+View+Plugin>`_
  On each build of a job you get a link to see the pipeline.

- `Delivery Pipeline Plugin <https://wiki.jenkins-ci.org/display/JENKINS/Delivery+Pipeline+Plugin>`_
  Like ``Build Pipeline Plugin`` let's you create a view to see pipelines,
  but contrary to the other, it let's you see more than one pipeline per view.

Opinion: the second and specially the third are the most interesting ones.
