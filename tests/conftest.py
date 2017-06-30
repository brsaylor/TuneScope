"""
Shared test fixtures.
pytest automatically makes these available in all test modules.
"""

import wave

import pytest
import numpy as np


@pytest.fixture(scope='session')
def wav_file_params():
    return {
        'channels': 2,
        'samplerate': 44100,
        'duration': 10  # seconds
    }


@pytest.fixture(scope='session')
def wav_file_samples(wav_file_params):
    """ This is the sample data (noise) written to wav_file """
    sample_count = (wav_file_params['channels'] *
                    wav_file_params['samplerate'] *
                    wav_file_params['duration'])
    return np.random.random(sample_count).astype(np.float32) * 2 - 1


@pytest.fixture(scope='session')
def wav_file(tmpdir_factory, wav_file_params, wav_file_samples):
    """ A generated test WAV file """
    channels = wav_file_params['channels']
    samplewidth = 2
    samplerate = wav_file_params['samplerate']
    duration = wav_file_params['duration']
    file_path = str(tmpdir_factory.mktemp('audio').join('test.wav'))
    writer = wave.open(file_path, mode='wb')
    writer.setnchannels(channels)
    writer.setsampwidth(samplewidth)
    writer.setframerate(samplerate)
    writer.setnframes(samplerate * duration)

    samples_16bit = (wav_file_samples * 2.0 ** 15).astype('<i2')
    writer.writeframes(samples_16bit.data)

    writer.close()
    return file_path
