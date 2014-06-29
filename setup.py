from setuptools import setup
import os


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()


version = "1.0b4"


install_requires = [
    'setuptools',
    'ploy >= 1.0rc9']


try:
    import fabric  # noqa
except ImportError:
    install_requires.append('Fabric>=1.3.0,!=1.8.3')


setup(
    version=version,
    description="A plugin for ploy providing integration with Fabric.",
    long_description=README + "\n\n",
    name="ploy_fabric",
    author='Florian Schulze',
    author_email='florian.schulze@gmx.net',
    url='http://github.com/ployground/ploy_fabric',
    include_package_data=True,
    zip_safe=False,
    packages=['ploy_fabric'],
    install_requires=install_requires,
    entry_points="""
        [ploy.plugins]
        fabric = ploy_fabric:plugin
    """)
