Overview
========

The ploy_fabric plugin provides integration of `Fabric`_ with `ploy`_.

.. _Fabric: http://fabfile.org
.. _ploy: https://github.com/ployground/


Installation
============

ploy_fabric is best installed with easy_install, pip or with zc.recipe.egg in a buildout.

Once installed, it's functionality is immediately usable with ploy.


Commands
========

The plugin adds the following commands to ploy.

``do``
  Runs a Fabric task with simplified syntax for arguments.
  You can just put positional arguments on the command line behind the task name.
  For keyword arguments user the ``name=value`` syntax.
  For example::

    ploy do something arg key=value

``fab``
  Runs a Fabric task and passes on command line options to Fabric.
  This basically reflects the ``fab`` script of Fabric.


Options
=======

Instances only get the new ``fabfile`` option to specify which file to look in for tasks.
The location is relative to ``ploy.conf``.

Instance methods
================

For the Python side, each instance gains the ``do(task, *args, **kwargs)`` method.
The ``task`` argument is the name of a task from the Fabric script which should be run. The remaining arguments are passed on to that task.


Fabric environment
==================

The Fabric environment has the following settings by default.

``reject_unknown_hosts``
  Always set to ``True``, ssh connections are handled by this plugin and ploy.

``disable_known_hosts``
  Always set to ``True``, handled by ploy.

``host_string``
  The **unique id** of the current instance, only manipulate if you know what you do!

``known_hosts``
  Path to the ``known_hosts`` file managed by ploy.

``instances``
  Dictionary allowing access to the other instances to get variables or call methods on.

``instance``
  The current instance to access variables from the ``config`` attribute or other things and methods.

``config_base``
  The directory of ``ploy.conf``.

Any option of the instance starting with ``fabric-`` is stripped of the ``fabric-`` prefix and overwrites settings in the environment with that name.


Changelog
=========

1.0.0 - 2014-07-19
------------------

* Added documentation.
  [fschulze]


1.0b6 - 2014-07-15
------------------

* Allow overwriting of fabric env from config with options prefixed by
  ``fabric-``, i.e. ``fabric-shell = /bin/sh -c``.
  [fschulze]


1.0b5 - 2014-07-08
------------------

* Packaging and test fixes.
  [fschulze]

* Fix task listing for ``do`` command.
  [fschulze]


1.0b4 - 2014-07-04
------------------

* Use unique id for host string to avoid issues.
  [fschulze]

* Added ``fab`` command which is just a wrapper for Fabric with all it's options
  and reworked ``do`` command into a simple version to just run a task.
  [fschulze]

* Renamed mr.awsome to ploy and mr.awsome.fabric to ploy_fabric.
  [fschulze]


1.0b3 - 2014-06-09
------------------

* When depending on Fabric, skip 1.8.3 which added a version pin on paramiko.
  [fschulze]

* Only add Fabric to install_requires if it can't be imported. That way we
  don't get problems if it's already installed as a system packages or in a
  virtualenv.
  [fschulze]


1.0b2 - 2014-05-15
------------------

* Register ``fabfile`` massager for all instances.
  [fschulze]

* Use context manager for output filtering and filter in ``do`` helper.
  [fschulze]

* Moved setuptools-git from setup.py to .travis.yml, it's only needed for
  releases and testing.
  [fschulze]


1.0b1 - 2014-03-24
------------------

* Initial release
  [fschulze]
