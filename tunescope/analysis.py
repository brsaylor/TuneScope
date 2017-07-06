from __future__ import division
import math

import numpy as np
import aubio


WINDOW_SIZE = 2048  # aubio window size
HOP_SIZE = 512      # aubio hop size (this is the time resolution of the analyses)


class Analyzer(object):
    """ Performs sound/musical analysis on an audio file.

    Parameters
    ----------
    audio_source : object
        An object with properties `channels` and `samplerate`
        and methods `is_eos()` and `read(sample_count)`,
        which returns a NumPy float32 array of length `sample_count`.
    duration : float
        Duration of input in seconds

    Attributes
    ----------
    pitch : ndarray
        Pitches as (possibly non-integer) MIDI note numbers.
        Will be None until analyze() is called.
    """

    def __init__(self, audio_source, duration):
        self._audio_source = audio_source
        self._duration = duration
        self.pitch = None

    def analyze(self):
        """ Perform the analysis """

        pitch_detector = aubio.pitch('yinfft', WINDOW_SIZE, HOP_SIZE, self._audio_source.samplerate)
        pitch_detector.set_unit('midi')

        duration_frames = int(math.ceil(self._duration * self._audio_source.samplerate))
        duration_hops = int(math.ceil(duration_frames / HOP_SIZE))

        # Each row contains (time, pitch)
        self.pitch = np.zeros(duration_hops, dtype=np.float32)

        for hop in range(duration_hops):
            frames = self._audio_source.read(HOP_SIZE * self._audio_source.channels).reshape((-1, self._audio_source.channels))
            frames_mono = frames.mean(axis=1)
            self.pitch[hop] = pitch_detector(frames_mono)[0]
