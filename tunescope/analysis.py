from __future__ import division
import math

import numpy as np
import aubio


def analyze(
        audio_source,
        window_size=2048,
        hop_size=512,
        page_size=1024,
        on_progress=None):
    """ Analyze the audio, producing data for plots.

    Parameters
    ----------
    audio_source : object
        An object with properties `channels` and `samplerate`
        and methods `is_eos()` and `read(sample_count)`,
        which returns a NumPy float32 array of length `sample_count`.
    window_size : int
        FFT window size
    hop_size: int
        Input data is analyzed in overlapping windows spaced `hop_size` audio
        frames apart. Each hop produces one data point.
    page_size: int
        Number of data points (hops) per page yielded
    on_progress : function
        Called on each hop to report progress

    Yields
    ------
    dict
    A dictionary with the current page of data:
        {
            'pitch': np.ndarray, dtype=np.float32, length=page_size - MIDI pitch value
        }
    """
    pitch_detector = aubio.pitch('yinfft', window_size, hop_size, audio_source.samplerate)
    pitch_detector.set_unit('midi')
    pitch_page = np.zeros(page_size, dtype=np.float32)
    i = 0
    while not audio_source.is_eos():
        frames_mono = (
            audio_source
            .read(hop_size * audio_source.channels)
            .reshape((-1, audio_source.channels))
            .mean(axis=1))
        pitch_page[i] = pitch_detector(frames_mono)[0]
        i += 1
        if i == page_size:
            yield {'pitch': pitch_page}
            i = 0
        on_progress and on_progress()
    if i != 0:
        yield {'pitch': pitch_page[:i]}
