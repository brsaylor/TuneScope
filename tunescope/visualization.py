""" Kivy widgets for audio visualization """

import math

import numpy as np
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty, ObjectProperty
from kivy.graphics import Color, Mesh, Scale
from kivy.graphics.tesselator import Tesselator
from kivy.clock import Clock


class PitchPlot(RelativeLayout):
    """ An area plot of MIDI pitch over time.

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
        self.bind(xscale=self._update_scale, yscale=self._update_scale)
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

        # Create the points of a polygon outlining the pitch plot.
        # The area under the pitch contour is to be filled,
        # so we add two extra points at (xmax, 0) and (0, 0).
        points = np.empty((len(pitches) + 2, 2), dtype=np.float32)
        points[:-2, 0] = np.arange(len(pitches), dtype=np.float32)
        points[:-2, 1] = pitches
        points[-2] = (len(pitches) - 1, 0)
        points[-1] = (0, 0)

        self._tesselator = Tesselator()
        self._tesselator.add_contour(points.flatten())
        if not self._tesselator.tesselate():
            raise RuntimeError("Failed to generate pitch plot")
        
        # Update the drawing instructions on the canvas from the main thread
        Clock.schedule_once(self._update_canvas, 0)

    def _update_canvas(self, dt):
        self.canvas.clear()
        with self.canvas:
            self._scale_matrix = Scale(self.xscale, self.yscale, 1)
            Color(1, 0.5, 1)
            for vertices, indices in self._tesselator.meshes:
                Mesh(vertices=vertices,
                     indices=indices,
                     mode="triangle_fan")
        self._update_scale()

    def _update_scale(self, *args):
        """ Compute widget size and canvas scale """
        width = math.ceil(self._num_pitches * self.xscale)
        height = math.ceil(self._highest_pitch * self.yscale)
        self.size = (width, height)
        if self._scale_matrix:
            self._scale_matrix.x = self.xscale
            self._scale_matrix.y = self.yscale
