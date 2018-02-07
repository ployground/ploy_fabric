Changelog
=========

2.0.0b1 - 2018-02-07
--------------------

* Support Python 3.x via Fabric3.
  [fschulze]

* Support for ploy 2.0.0.
  [fschulze]


1.1.0 - 2014-10-27
------------------

* Require Fabric >= 1.4.0 and vastly simplify the necessary patching.
  [fschulze]

* Close all newly opened connections after a Fabric call.
  [fschulze]

* Add context manager and decorator to easily switch fabric connections.
  [fschulze]


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
