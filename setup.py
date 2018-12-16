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

audiobackend_compiler_args = pkgconfig.parse('gstreamer-1.0 gstreamer-app-1.0 gstreamer-audio-1.0')
audiodecoder_compiler_args = pkgconfig.parse('gstreamer-1.0 gstreamer-app-1.0 gstreamer-audio-1.0')
audiodecoder_compiler_args['include_dirs'].append(np.get_include())
audiometadata_compiler_args = pkgconfig.parse('gstreamer-1.0 gstreamer-pbutils-1.0')
audiooutput_compiler_args = pkgconfig.parse('sdl2')
audiooutput_compiler_args['include_dirs'].append(np.get_include())

extensions = [
    Extension('tunescope.audio.audiobackend',
              ['tunescope/audio/audiobackend.pyx'],
              **audiobackend_compiler_args),

    Extension('tunescope.audio.audiodecoder',
              ['tunescope/audio/audiodecoder.pyx'],
              **audiodecoder_compiler_args),

    Extension('tunescope.audio.audiometadata',
              ['tunescope/audio/audiometadata.pyx'],
              **audiometadata_compiler_args),

    Extension('tunescope.audio.audiooutput',
              ['tunescope/audio/audiooutput.pyx'],
              **audiooutput_compiler_args),

    Extension('tunescope.audio.audioutil',
              ['tunescope/audio/audioutil.pyx'],
              include_dirs=[np.get_include()]),

    Extension('tunescope.audio.buffering',
              ['tunescope/audio/buffering.pyx'],
              include_dirs=[np.get_include()]),

    Extension('tunescope.audio.looper',
              ['tunescope/audio/looper.pyx'],
              include_dirs=[np.get_include()]),

    Extension('tunescope.audio.timestretcher',
              ['tunescope/audio/timestretcher.pyx'],
              libraries=['rubberband'],
              include_dirs=[np.get_include(), 'lib/rubberband'],
              library_dirs=['lib/rubberband/lib']),

    Extension('tunescope.visualization.processing',
              ['tunescope/visualization/processing.pyx'],
              include_dirs=[np.get_include()]),
]

setup(
    name='TuneScope',

    version='0.1',

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
    ext_modules=cythonize(extensions, build_dir='build'),
)
