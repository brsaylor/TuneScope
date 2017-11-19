""" Kivy widgets for audio visualization """

import math

import numpy as np
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty, ObjectProperty
from kivy.graphics import Color, Scale, Line
from kivy.clock import Clock


class PitchPlot(RelativeLayout):
    """ A plot of MIDI pitch over time """

    def __init__(self, **kwargs):
        super(PitchPlot, self).__init__(**kwargs)
        self._points = None
        self._scale_matrix = None

    def plot(self, pitches):
        """ Plot the given pitches on the canvas.

        May be safely called from a non-GUI thread.

        Parameters
        ----------
        pitches : ndarray
            Array of MIDI pitch values sampled at regular time intervals
        """
        self._num_pitches = len(pitches)
        self._highest_pitch = pitches.max()

        points = np.empty((len(pitches), 2), dtype=np.float32)
        points[:, 0] = np.arange(len(pitches), dtype=np.float32)
        points[:, 1] = pitches
        self._points = list(points.flatten())

        # Update the drawing instructions on the canvas from the main thread
        Clock.schedule_once(self._update_canvas, 0)

    def clear(self):
        self.plot(np.array([1]))

    def on_size(self, *args):
        self._update_scale_matrix()

    def _update_canvas(self, dt):
        self.canvas.clear()
        with self.canvas:
            self._scale_matrix = Scale(1, 1, 1)
            Color(1, 0.5, 1)
            Line(points=self._points, width=1)
        self._update_scale_matrix()

    def _update_scale_matrix(self, *args):
        if self._scale_matrix:
            self._scale_matrix.x = self.width / self._num_pitches
            self._scale_matrix.y = self.height / self._highest_pitch
