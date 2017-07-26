""" Kivy widgets for audio visualization """

import math

import numpy as np
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty, ObjectProperty
from kivy.graphics import Color, Scale, Line
from kivy.clock import Clock


class PitchPlot(RelativeLayout):
    """ A plot of MIDI pitch over time.

    Adjusting the scale attributes automatically updates the `size` property
    to contain the entire plot.

    Attributes
    ----------
    xscale : float
        Pixels per time interval
    yscale : float
        Pixels per semitone
    """

    xscale = NumericProperty(1.)
    yscale = NumericProperty(1.)

    def __init__(self, **kwargs):
        super(PitchPlot, self).__init__(**kwargs)
        self._points = None
        self._scale_matrix = None
        self.bind(xscale=self._update_scale, yscale=self._update_scale)

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

    def _update_canvas(self, dt):
        self.canvas.clear()
        with self.canvas:
            self._scale_matrix = Scale(self.xscale, self.yscale, 1)
            Color(1, 0.5, 1)
            Line(points=self._points, width=1)
        self._update_scale()

    def _update_scale(self, *args):
        """ Compute widget size and canvas scale """
        if self._points is None:
            return
        width = math.ceil(self._num_pitches * self.xscale)
        height = math.ceil(self._highest_pitch * self.yscale)
        self.size = (width, height)
        if self._scale_matrix:
            self._scale_matrix.x = self.xscale
            self._scale_matrix.y = self.yscale
