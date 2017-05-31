import wave

import pytest
import numpy as np

from tunescope.audiodecoder import AudioDecoder

# TODO: Test reading invalid files
# TODO: Test reading audio from video files

CHANNELS = 2


@pytest.fixture(scope='session')
def wav_file(tmpdir_factory):
    """ Create a WAV file with 10 seconds of noise """
    channels = CHANNELS
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


def test_nonexistent_file():
    with pytest.raises(IOError):
        AudioDecoder('nonexistent-file')


def test_read(wav_file):
    """ Test that AudioDecoder can read a WAV file correctly """
    wav_reader = wave.open(wav_file, 'rb')
    decoder = AudioDecoder(wav_file)

    total_frame_count = wav_reader.getnframes()
    frames_read = 0

    while not decoder.is_eos():
        decoder_samples = decoder.read()
        frames_read += len(decoder_samples) / CHANNELS
        assert len(decoder_samples > 1)
        wav_samples = np.frombuffer(
            wav_reader.readframes(len(decoder_samples) / CHANNELS),
            dtype='<i2').astype(np.float32) / 2.0 ** 15
        assert np.allclose(decoder_samples, wav_samples)

    assert frames_read == total_frame_count

    with pytest.raises(EOFError):
        decoder.read()


def test_delete(wav_file):
    """ Ensure that AudioDecoder.__dealloc__ does not crash """
    decoder = AudioDecoder(wav_file)
    del decoder
