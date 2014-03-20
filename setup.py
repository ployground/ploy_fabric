from setuptools import setup

version = "0.1"

setup(
    version=version,
    description="A plugin for mr.awsome providing integration with Fabric.",
    name="mr.awsome.fabric",
    author='Florian Schulze',
    author_email='florian.schulze@gmx.net',
    url='http://github.com/fschulze/mr.awsome.fabric',
    include_package_data=True,
    zip_safe=False,
    packages=['mr'],
    namespace_packages=['mr'],
    install_requires=[
        'setuptools',
        'mr.awsome',
        'Fabric >= 1.3.0'
    ],
    setup_requires=[
        'setuptools-git'],
    entry_points="""
        [mr.awsome.plugins]
        fabric = mr.awsome.fabric:plugin
    """)
