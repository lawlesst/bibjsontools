#import ez_setup
#ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name='bibjsonutils',
    version='0.1',
    author='Ted Lawless',
    author_email='lawlesst@gmail.com',
    packages=find_packages(),
    package_data={'bibjsonutils': ['test/data/*.*']},
)


