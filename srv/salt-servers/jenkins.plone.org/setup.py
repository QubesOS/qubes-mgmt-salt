# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


version = '0.1a1.dev0'

long_description = open('README.rst').read()

setup(
    name='jenkins.plone.org',
    version=version,
    description='Jenkins configuration for Plone project',
    long_description=long_description,
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing',
    ],
    keywords='jenkins plone',
    author='The Plone Foundation',
    author_email='plone@plone.org',
    url='https://github.com/plone/jenkins.plone.org',
    license='gpl',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['jenkins_builder', ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'jenkins-job-builder',
    ],
    entry_points={
        'jenkins_jobs.wrappers': [
            'xvfb = jenkins_builder.builder:xvfb'
        ],
    },
)
