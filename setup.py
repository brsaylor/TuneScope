from os import path
from codecs import open  # To use a consistent encoding

from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
import numpy as np
import pkgconfig

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

audiobackend_compiler_args = pkgconfig.parse(
    'gstreamer-1.0 gstreamer-app-1.0 gstreamer-audio-1.0')

audiodecoder_compiler_args = pkgconfig.parse(
    'gstreamer-1.0 gstreamer-app-1.0 gstreamer-audio-1.0')
audiodecoder_compiler_args['include_dirs'].append(np.get_include())

buffering_compiler_args = {'include_dirs': [np.get_include()]}

audiooutput_compiler_args = pkgconfig.parse('sdl2')
audiooutput_compiler_args['include_dirs'].append(np.get_include())

extensions = [
    Extension('tunescope.audiobackend',
              ['tunescope/audiobackend.pyx'],
              **audiobackend_compiler_args),

    Extension('tunescope.audiodecoder',
              ['tunescope/audiodecoder.pyx'],
              **audiodecoder_compiler_args),

    Extension('tunescope.buffering',
              ['tunescope/buffering.pyx'],
              **buffering_compiler_args),

    Extension('tunescope.audiooutput',
              ['tunescope/audiooutput.pyx'],
              **audiooutput_compiler_args),
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
