import io
import os
import re

from setuptools import setup, find_packages


def read(*names, **kwargs):
    with io.open(
            os.path.join(os.path.dirname(__file__), *names),
            encoding=kwargs.get("encoding", "utf8")) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


release_version = os.environ.get("RELEASE_VERSION", None)
if release_version:
    version = release_version
else:
    version = find_version('aiops', '__init__.py')

with open('README.md') as f:
    long_description = f.read()

setup(
    name='aiops',
    packages=find_packages(exclude=['.data', '.github', 'resources', 'tests']),
    version=version,
    license='MIT',
    description='Basic Utilities for aiops implementations',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Amandeep',
    author_email='deep.aman91@gmail.com',
    url='https://github.com/amandeep1991/aiops',
    download_url='https://github.com/amandeep1991/aiops/archive/{}.tar.gz'.format(version),
    keywords=['aiops', 'AI for Ops', 'AI for operations'],
    install_requires=[
        'beautifulsoup4',
        'transformers',
        'torch',
        'torchtext',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
)
