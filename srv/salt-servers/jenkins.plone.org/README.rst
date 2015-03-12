===============================================================================
PLONE JENKINS/CI TEAM
===============================================================================

Plone Jenkins/CI Team Members
=============================

* Eric Steele
* Michael Mulich
* Thomas Desvenain
* Timo Stollenwerk
* William Deegan


Possible Topics / Ideas
=======================

* Plone testing – We've got the basic bin/test bits working now. I've been slowly setting up some static analysis (pep8, zptlint, etc). Selenium/Webdriver testing is something we need to jump on. Test coverage reports. Performance testing would be outstanding.
* PLIP testing – The Framework Team and PLIP implementers would appreciate being able to see the current status of under-development PLIPs.
* Plone releases – Packaging. Pushing to dist.plone.org. Building installers (automating Windows installer builds is a really high priority at the moment). Nightly builds?
* Compatibility testing – Michael's got a great set of scripts/cfgs set up to easily check a package against any/all Plone releases. I'd like to set that up and start plugging in 3rd party packages. Ideally, we could start pulling this data in to plone.org's downloads section: PFG 8.1.7 just came out, what versions of Plone does it work with? I'd also welcome testing against the current Plone development branches. If 30 add-ons break overnight, I can catch the regressions before they make it into the next release.


Work in Progress
================

* JENKINS SERVER:

  [ ] Create fabric configuration

  [ ] Install monitoring

  [ ] Install notifications when jenkins is down

  [timo]

* JENKINS BUILDOUT: Generic Jenkins buildout file/recipe that can be used by
  Plone core, Plone core projects and collective add-ons to generate a
  buildout that provides test data that can be processed by Jenkins. We might
  want to refactor this into a buildout recipe at some point.

    https://github.com/plone/buildout.jenkins

  [X] Create buildout.jenkins project on github

  [X] Make buildout.jenkins work for single source Plone core projects

  [X] Make buildout.jenkins work for multiple source Plone core projects

  [ ] Use buildout.jenkins for Plone core builds

  [ ] Add code analysis features

  [ ] Refactor code into a recipe ???

  [timo]

* CODE COVERAGE RECIPE: Extend collective.xmltestreport to produce code
  coverage data that can be used by the Jenkins cobertura plugin.

  [X] Move collective.xmltestreport to github: https://github.com/collective/collective.xmltestreport

  [ ] Create branch that includes the code coverage feature

  [ ] Make new collective.xmltestreport release

  [timo]

* JENKINS DOCUMENTATION: Refactor the unfinished and unpublished Hudson
  tutorial on plone.org
  (http://plone.org/documentation/kb/how-to-set-up-a-hudson-continuous-integration-server-for-a-plone-project)

  [ ] Rewrite and update the documentation

  [ ] Move the documentation to buildout.jenkins or jenkins.plone.org ???

  [timo]


DONE
====

* Plone coredev is currently triggered on each github commit to the core repo
  no matter to which branch. This leads to load problems on jenkins.plone.org.
  As far as I understood the discussion on that topic the best way to
  accomplish this is a small piece of component that sits in between github
  and jenkins and can decide which commit should trigger a build. Another
  option might be a Jenkins plugin. Any thoughts/ideas?

  - https://github.com/conversation/github-jenkins-bridge
  - http://stackoverflow.com/questions/5784329/how-can-i-make-jenkins-ci-with-git-trigger-on-pushes-to-master

  => UPDATE: If we disable the "Cross Site Request Forgery" setting in the
     Jenkins configuration, the GitHub post-commit hook works.

  => UPDATE: A user "github" has been created in the Plone LDAP and granted
     the right to build a job on jenkins.plone.org. See
     https://github.com/plone/plone.app.discussion/admin/hooks
     for an example of a post-commit hook configuration. Anonymous users are
     not allowed to trigger a build.

  => UPDATE: Setting "pollingThreadCount" (number of parallel version control
     repository checkouts) from 30 to 10, significantly reduces the number of
     failed github checkouts.

  => DONE: We use github post-commit hooks now and triggering the builds is
     quite stable with this.


Books about Jenkins/CI/Testing
==============================

* http://www.wakaleo.com/books/jenkins-the-definitive-guide


Examples of other Jenkins/CI instances
======================================

* http://ci.typo3.org/view/TYPO3/


Useful Jenkins Plugins
======================

* https://wiki.jenkins-ci.org/display/JENKINS/Email-ext+plugin
  Configurable email notifications

* https://wiki.jenkins-ci.org/display/JENKINS/JobConfigHistory+Plugin
  Saves copies of all job and system configurations. Allows you to export job configurations.

* W3C validation:
  https://wiki.jenkins-ci.org/display/JENKINS/Unicorn+Validation+Plugin
