import math
from functools import partial

import numpy as np
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.graphics import Color, Scale, Line
from kivy.clock import Clock
from kivy.metrics import dp


class PitchPlot(RelativeLayout):
    """ A plot of MIDI pitch over time

    All public methods may be safely called from a non-GUI thread.
    """

    line_color = ListProperty([0, 0, 0, 1])

    def __init__(self, **kwargs):
        super(PitchPlot, self).__init__(**kwargs)
        self._scale_matrix = None

    def prepare(self, data_length):
        """ Prepare the canvas for a new plot """
        self._data_length = data_length
        self._pitches_plotted = 0
        self._max_pitch = 1
        Clock.schedule_once(self._prepare_canvas, 0)

    def _prepare_canvas(self, dt):
        self.canvas.clear()
        with self.canvas:
            self._scale_matrix = Scale(1, 1, 1)
            Color(*self.line_color)
        self._update_scale_matrix()

    def add_data(self, pitches):
        """ Append ndarray `pitches` to the plot """
        max_pitch = pitches.max()
        if max_pitch > self._max_pitch:
            self._max_pitch = max_pitch
            self._update_scale_matrix()
        points = np.empty((len(pitches), 2), dtype=np.float32)
        points[:, 0] = np.arange(
            self._pitches_plotted,
            self._pitches_plotted + len(pitches),
            dtype=np.float32)
        points[:, 1] = pitches
        points = list(points.flatten())
        Clock.schedule_once(partial(self._plot, points), 0)
        self._pitches_plotted += len(pitches)

    def _plot(self, points, dt):
        self.canvas.add(Line(points=points, width=dp(1)))

    def on_size(self, *args):
        self._update_scale_matrix()

    def _update_scale_matrix(self):
        if self._scale_matrix:
            self._scale_matrix.x = self.width / self._data_length
            self._scale_matrix.y = self.height / self._max_pitch
