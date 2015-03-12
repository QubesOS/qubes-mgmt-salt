==================
sphinx-doc-formula
==================

Formulas to install the `Sphinx`_ documentation system.

.. _`Sphinx`: http://sphinx-doc.org/

.. note::

    See the full `Salt Formulas installation and usage instructions
    <http://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html>`_.

Available states
================

.. contents::
    :local:

``sphinx_doc``
--------------

Installs the Sphinx package.

``sphinx_doc.sphinx_venv``
--------------------------

Installs the Sphinx package to an empty virtualenv.

Requires:

* virtualenv-formula
* Pillar:

  * ``sphinx_doc:venv`` to point to the virtualenv that Sphinx is installed to.
