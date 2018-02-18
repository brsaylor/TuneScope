import math
from functools import partial

import numpy as np
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.graphics import Color, Scale, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.graphics.instructions import InstructionGroup
from kivy.clock import Clock
from kivy.metrics import dp

from .colormaps import viridis
from .processing import log_axis


def _colormap_to_array(colormap, extend_to_black=0):
    colormap = np.array(colormap)

    if extend_to_black:
        extra_rows = np.vstack([
            np.linspace(0, colormap[0,col], num=extend_to_black, endpoint=False)
            for col in range(colormap.shape[1])
        ]).T
        colormap = np.concatenate([extra_rows, colormap], axis=0)

    colormap = (colormap * 255).astype(np.uint8)

    return colormap


def spectra_to_pixels(spectra, colormap):
    """spectra dimensions: 
        rows must be a power of 2 
        collumns must be a power of 2 + 1"""
    colormap_indices = np.clip(
        (spectra[:,1:].T.flatten() * len(colormap)).astype(np.int32),
        0, len(colormap) - 1)
    pixels = colormap[colormap_indices].flatten()
    size = (spectra.shape[0], spectra.shape[1] - 1)
    return pixels, size


class Spectrogram(RelativeLayout):

    def __init__(self, **kwargs):
        super(Spectrogram, self).__init__(**kwargs)
        self._scale_matrix = None
        self._colormap = _colormap_to_array(viridis)

    def prepare(self, data_length):
        """ Prepare the canvas for a new plot """
        self._data_length = data_length
        self._spectra_plotted = 0
        self._max_texture_height = 1
        Clock.schedule_once(self._prepare_canvas, 0)

    def _prepare_canvas(self, dt):
        self.canvas.clear()
        with self.canvas:
            self._scale_matrix = Scale(1, 1, 1)
            Color(1, 1, 1)
        self._update_scale_matrix()

    def add_data(self, spectra):
        spectra = log_axis(spectra)

        spectra = np.log2(spectra + 1)

        spectra = spectra / np.clip(spectra.max(axis=1)[:,np.newaxis], 0.01, 1) # normalize
        # spectra = spectra * 30


        # pixels, texture_size = spectra_to_pixels(np.log10(spectra * 9 + 1), self._colormap)
        # pixels, texture_size = spectra_to_pixels(np.log2(spectra + 1), self._colormap)
        pixels, texture_size = spectra_to_pixels(spectra, self._colormap)

        if texture_size[1] > self._max_texture_height:
            self._max_texture_height = texture_size[1]
            self._update_scale_matrix()
        Clock.schedule_once(partial(self._plot_spectra, self._spectra_plotted, pixels, texture_size), 0)
        self._spectra_plotted += len(spectra)

    def _plot_spectra(self, x, pixels, texture_size, dt):
        texture = Texture.create(size=texture_size)
        texture.blit_buffer(pixels, colorfmt='rgb', bufferfmt='ubyte')
        # rectangle = Rectangle(pos=(x, 0), size=texture_size)
        rectangle = Rectangle(pos=(x, 0), size=texture_size, texture=texture)
        self.canvas.add(rectangle)

    def on_size(self, *args):
        self._update_scale_matrix()

    def _update_scale_matrix(self):
        if self._scale_matrix:
            self._scale_matrix.x = self.width / self._data_length
            self._scale_matrix.y = self.height / self._max_texture_height
