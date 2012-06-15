#import ez_setup
#ez_setup.use_setuptools()

from setuptools import setup, find_packages

install_requires = []
try:
    import json
except ImportError:
    install_requires.append('simplejson')

setup(
    name='bibjsontools',
    version='0.1',
    author='Ted Lawless',
    author_email='lawlesst@gmail.com',
    packages=find_packages(),
    package_data={'bibjsontools': ['test/data/*.*']},
    install_requires=install_requires,
)


