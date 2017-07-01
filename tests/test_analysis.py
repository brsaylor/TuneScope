from __future__ import division
import math
import wave

import pytest
import numpy as np

from tunescope.analysis import *
from tunescope.audiodecoder import AudioDecoder
from tunescope.buffering import DecoderBuffer
from tunescope.audiometadata import AudioMetadata


TEST_FILE_DURATION = 5  # Test file duration in seconds


@pytest.fixture(scope='session')
def wav_file_A440(tmpdir_factory):
    """ Generate a mono WAV file with a sine wave at A440 """
    file_path = str(tmpdir_factory.mktemp('audio').join('A440.wav'))
    channels = 1
    samplewidth = 2
    samplerate = 44100
    duration = TEST_FILE_DURATION
    writer = wave.open(file_path, mode='wb')
    writer.setnchannels(channels)
    writer.setsampwidth(samplewidth)
    writer.setframerate(samplerate)
    writer.setnframes(samplerate * duration)

    x = np.linspace(0, 440 * duration * 2 * math.pi, num=samplerate*duration)
    sine = (np.sin(x) * 2**14).astype('<i2')

    writer.writeframes(sine.tobytes(
        channels * samplewidth * samplerate * duration
    ))

    writer.close()
    return file_path


def test_pitch_A440(wav_file_A440):
    metadata = AudioMetadata(wav_file_A440)
    decoder = AudioDecoder(wav_file_A440)
    buf = DecoderBuffer(decoder, 1024)
    analyzer = Analyzer(buf, metadata.duration)
    analyzer.analyze()

    # MIDI note number for A440 is 69
    wav_reader = wave.open(wav_file_A440, 'rb')

    # Check that pitch array has correct shape
    assert analyzer.pitch.shape == (math.ceil(wav_reader.getnframes() / HOP_SIZE), 2)

    # Check that the time column is correct
    assert np.allclose(analyzer.pitch[:, 0],
                       np.arange(0, TEST_FILE_DURATION, HOP_SIZE / wav_reader.getframerate()))

    # Check that pitch is 69, within half a semitone
    assert np.allclose(analyzer.pitch[:, 1], 69, atol=0.5)
