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


@pytest.mark.xfail(reason="pitch analysis disabled for now")
@pytest.mark.parametrize(
    ['window_size', 'hop_size'],
    [
        (2048, 512),
        (2048, 1024),
        (4096, 512),
    ])
def test_pitch_A440(A440_sine_wave, window_size, hop_size):
    source = FakeAudioSource(1, SINE_WAVE_SAMPLERATE, A440_sine_wave)
    page_size = 8
    data_length = int(math.ceil(len(A440_sine_wave) / hop_size))
    spectrum_size = window_size // 2 + 1
    pitches = np.zeros(data_length, dtype=np.float32)
    spectra = np.zeros((data_length, spectrum_size), dtype=np.float32)

    i = 0
    for page in analyze(
            source,
            window_size=window_size,
            hop_size=hop_size,
            page_size=page_size):

        if source.is_eos():
            pitches[i:i+len(page['pitch'])] = page['pitch']
            spectra[i:i+len(page['spectrum'])] = page['spectrum']
        else:
            assert len(page['pitch']) == page_size
            assert len(page['spectrum']) == page_size
            pitches[i:i+page_size] = page['pitch']
            spectra[i:i+page_size, :] = page['spectrum']
            i += page_size

    assert source.is_eos()

    # Check that pitch is 69 (A440), within half a semitone
    assert np.allclose(pitches, 69, atol=0.5)

    # Trim off beginning and end so we're only looking at hops with a full signal
    trim_length = window_size // hop_size
    trimmed_spectra = spectra[trim_length:-trim_length]

    # Figure out which spectrum bin should have the most energy
    window_freq = SINE_WAVE_SAMPLERATE / float(window_size)  # frequency of bin 1
    # window_freq * bin_number ~= 440
    expected_max_bin = int(round(440.0 / window_freq))
    actual_max_bin = trimmed_spectra.argmax(axis=1)
    assert np.all(actual_max_bin == expected_max_bin)

    # Check that total amplitude is preserved
    assert np.allclose(trimmed_spectra.sum(axis=1), 1, atol=0.1)
