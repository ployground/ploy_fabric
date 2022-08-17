import os
import setuptools


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
HISTORY = open(os.path.join(here, 'HISTORY.rst')).read()


version = "2.0.0"

install_requires = [
    'setuptools',
    'ploy >= 2.0.0',
    'Fabric>=1.4.0,!=1.8.3,<2dev']

classifiers = [
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: System :: Installation/Setup',
    'Topic :: System :: Systems Administration']


setuptools.setup(
    version=version,
    description="Plugin to integrate Fabric with ploy.",
    long_description=README + "\n\n" + HISTORY,
    name="ploy_fabric",
    author='Florian Schulze',
    author_email='florian.schulze@gmx.net',
    license="BSD 3-Clause License",
    url='http://github.com/ployground/ploy_fabric',
    classifiers=classifiers,
    include_package_data=True,
    zip_safe=False,
    packages=['ploy_fabric'],
    install_requires=install_requires,
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, !=3.6.*',
    entry_points="""
        [ploy.plugins]
        fabric = ploy_fabric:plugin
    """)
