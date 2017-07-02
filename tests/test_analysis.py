from __future__ import division
import math
import wave

import pytest
import numpy as np

from tunescope.analysis import *
from tunescope.audiodecoder import AudioDecoder
from tunescope.buffering import DecoderBuffer
from tunescope.audiometadata import AudioMetadata
from test_doubles import FakeAudioSource


SINE_WAVE_DURATION = 5  # seconds
SINE_WAVE_SAMPLERATE = 44100


@pytest.fixture(scope='session')
def A440_sine_wave(tmpdir_factory):
    x = np.linspace(0,
                    440 * SINE_WAVE_DURATION * 2 * math.pi,
                    num=SINE_WAVE_SAMPLERATE * SINE_WAVE_DURATION)
    sine = (np.sin(x) * 2**14).astype('<i2')
    return sine


def test_pitch_A440(A440_sine_wave):
    source = FakeAudioSource(1, SINE_WAVE_SAMPLERATE, A440_sine_wave)
    analyzer = Analyzer(source, SINE_WAVE_DURATION)
    analyzer.analyze()

    # Check that pitch array has correct shape
    assert analyzer.pitch.shape == (math.ceil(len(A440_sine_wave) / HOP_SIZE), 2)

    # Check that the time column is correct
    assert np.allclose(analyzer.pitch[:, 0],
                       np.arange(0, SINE_WAVE_DURATION, HOP_SIZE / SINE_WAVE_SAMPLERATE))

    # Check that pitch is 69 (A440), within half a semitone
    assert np.allclose(analyzer.pitch[:, 1], 69, atol=0.5)
