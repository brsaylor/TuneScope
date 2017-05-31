from os import path
from codecs import open  # To use a consistent encoding
import glob

from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
import numpy as np
import pkgconfig

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

compiler_args = pkgconfig.parse('gstreamer-1.0 gstreamer-app-1.0')
compiler_args['include_dirs'].append(np.get_include())
extensions = [
    Extension('tunescope.audiodecoder', ['tunescope/audiodecoder.pyx'], **compiler_args)
]

setup(
    name='TuneScope',

    version='0.0.1a0',

    description='An application for tune learning',
    long_description=long_description,

    url='https://github.com/brsaylor/TuneScope',

    author='Ben Saylor',
    author_email='brsaylor@gmail.com',

    license='GNU General Public License v3 or later (GPLv3+)',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2.7',
    ],

    packages=find_packages(),
    ext_modules=cythonize(extensions),
)
