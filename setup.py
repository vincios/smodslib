# Always prefer setuptools over distutils
from setuptools import setup

# To use a consistent encoding
from codecs import open
from os import path

# The directory containing this file
HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# This call to setup() does all the work
setup(
    name="smodslib",
    version="0.1.12",
    description="A Skymods.ru automation library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vincios/smodslib",
    author="vincios",
    author_email="",
    license="MIT",
    packages=["smodslib"],
    install_requires=["requests", "beautifulsoup4", "cloudscraper"]
)
