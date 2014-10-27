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

Another helper added to each instance is a context manager accessible via the ``fabric`` attribute on instances.
With that you can switch to a new ssh connection with a different user in your Fabric tasks:

.. code-block:: python

    from fabric.api import env, run


    def sometask():
        run("whoami")  # prints the default user (root)
        with env.instance.fabric(user='foo'):
          run("whoami")  # prints 'foo' if the connection worked
        run("whoami")  # prints the default user (root)

All changes to the Fabric environment are reverted when the context manager exits.

Fabric task decorator
=====================

With ``ploy_fabric.context`` you can decorate a task to use a specific user with a separate connection.
All changes to the Fabric environment are reverted when the context manager exits.
This is useful if you want to run a task from inside another task.

.. code-block:: python

    from fabric.api import env, run
    from ploy_fabric import context


    @context  # always run with the default user
    def sometask():
        run("whoami")  # prints the default user (root)


    @context(user=None)  # always run with the default user (alternate syntax)
    def someothertask():
        env.forward_agent = True
        run("whoami")  # prints the default user (root)


    @context(user='foo')  # always run as foo user
    def anothertask():
        env.forward_agent = False
        run("whoami")  # prints the default user (user)
        someothertask()
        assert env.forward_agent == False


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
