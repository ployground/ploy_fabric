from setuptools import setup
import os


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
HISTORY = open(os.path.join(here, 'HISTORY.rst')).read()


version = "1.1.1"


install_requires = [
    'setuptools',
    'ploy >= 1.0.0, < 2dev',
    'Fabric>=1.4.0,!=1.8.3,<2dev']


setup(
    version=version,
    description="Plugin to integrate Fabric with ploy.",
    long_description=README + "\n\n" + HISTORY,
    name="ploy_fabric",
    author='Florian Schulze',
    author_email='florian.schulze@gmx.net',
    license="BSD 3-Clause License",
    url='http://github.com/ployground/ploy_fabric',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration'],
    include_package_data=True,
    zip_safe=False,
    packages=['ploy_fabric'],
    install_requires=install_requires,
    entry_points="""
        [ploy.plugins]
        fabric = ploy_fabric:plugin
    """)
