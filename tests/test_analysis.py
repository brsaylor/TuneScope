from __future__ import division
import math

import pytest
import numpy as np

from tunescope.analysis import analyze
from test_doubles import FakeAudioSource


SINE_WAVE_DURATION = 5  # seconds
SINE_WAVE_SAMPLERATE = 44100
#SINE_WAVE_CHANNELS = 2  # FIXME: Test with stereo


@pytest.fixture(scope='session')
def A440_sine_wave(tmpdir_factory):
    x = np.linspace(0,
                    440 * SINE_WAVE_DURATION * 2 * math.pi,
                    num=SINE_WAVE_SAMPLERATE * SINE_WAVE_DURATION)
    sine = (np.sin(x)).astype(np.float32)
    return sine


def test_pitch_A440(A440_sine_wave):
    source = FakeAudioSource(1, SINE_WAVE_SAMPLERATE, A440_sine_wave)
    hop_size = 512
    page_size = 8

    pitches = np.array([], dtype=np.float32)
    for page in analyze(
            source,
            window_size=2048,
            hop_size=hop_size,
            page_size=page_size):
        assert len(page['pitch']) == page_size or source.is_eos()
        pitches = np.concatenate([pitches, page['pitch']])

    assert len(pitches) == math.ceil(len(A440_sine_wave) / hop_size)

    # Check that pitch is 69 (A440), within half a semitone
    assert np.allclose(pitches, 69, atol=0.5)
