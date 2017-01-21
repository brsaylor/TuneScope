"""
Tests for the audioread library
"""

import wave

import pytest
import numpy as np
from audioread.gstdec import *


@pytest.fixture(scope='session')
def wav_file(tmpdir_factory):
    """ Create a WAV file with 10 seconds of noise """
    channels = 2
    samplewidth = 2
    samplerate = 44100
    duration = 10  # seconds
    file_path = str(tmpdir_factory.mktemp('audio').join('test.wav'))
    writer = wave.open(file_path, mode='wb')
    writer.setnchannels(channels)
    writer.setsampwidth(samplewidth)
    writer.setframerate(samplerate)
    writer.setnframes(samplerate * duration)
    writer.writeframes(np.random.bytes(
        channels * samplewidth * samplerate * duration
    ))
    writer.close()
    return file_path


def test_gst_audio_file(wav_file):
    """ Test that GstAudioFile can open and read a WAV file correctly """

    wav_reader = wave.open(wav_file, 'rb')

    with GstAudioFile(wav_file) as gst_reader:
        assert gst_reader.channels == wav_reader.getnchannels()
        assert gst_reader.samplerate == wav_reader.getframerate()
        assert gst_reader.duration * gst_reader.samplerate == wav_reader.getnframes()
        samplewidth = wav_reader.getsampwidth()

        frames_read = 0
        for gst_block in gst_reader:
            frame_count = len(gst_block) // gst_reader.channels // samplewidth
            wav_block = wav_reader.readframes(frame_count)
            assert gst_block == wav_block
            frames_read += frame_count

        assert frames_read == wav_reader.getnframes()
