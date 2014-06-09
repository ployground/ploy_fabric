Changelog
=========

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
