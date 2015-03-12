# -*- coding: utf-8 -*-
import xml.etree.ElementTree as XML


def xvfb(parser, xml_parent, data):
    """yaml: xvfb

    Configures xvfb to be used on this job.
    Requires the Jenkins `Xvfb Plugin.
    <https://wiki.jenkins-ci.org/display/JENKINS/Xvfb+Plugin>`_

    :arg str name: xvfb screen name
    :arg str screen: screen dimensions
    :arg bool debug: whether debug is enabled (default False)
    :arg int timeout: seconds to wait until xvfb is ready (default 0)
    :arg bool shutdown: whether xvfb should be shut down when build finishes
      (default True)

    Example::

      properties:
        - xvfb:
            name: default
            screen: 1024x768x24

    Extended example::

      properties:
        - xvfb:
            name: default
            screen: 1024x768x24
            debug: false
            timeout: 0
            shutdown: false
    """
    xvfb_data = XML.SubElement(
        xml_parent,
        'org.jenkinsci.plugins.xvfb.XvfbBuildWrapper'
    )
    data_property = str(data.get('name'))
    XML.SubElement(xvfb_data, 'installationName').text = data_property

    data_property = str(data.get('screen'))
    XML.SubElement(xvfb_data, 'screen').text = data_property

    if data.get('debug', True):
        XML.SubElement(xvfb_data, 'debug').text = 'true'
    else:
        XML.SubElement(xvfb_data, 'debug').text = 'false'

    XML.SubElement(xvfb_data, 'displayNameOffset').text = '1'

    data_property = str(data.get('timeout', 0))
    XML.SubElement(xvfb_data, 'timeout').text = data_property

    if data.get('shutdown', True):
        XML.SubElement(xvfb_data, 'shutdownWithBuild').text = 'true'
    else:
        XML.SubElement(xvfb_data, 'shutdownWithBuild').text = 'false'
