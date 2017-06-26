import os.path
import wave
import time

import pytest
import numpy as np

from tunescope.audiodecoder import AudioDecoder

# TODO: Test reading invalid files
# TODO: Test reading audio from video files

CHANNELS = 2
SAMPLERATE = 44100


@pytest.fixture(scope='session')
def wav_file(tmpdir_factory):
    """ Create a WAV file with 10 seconds of noise """
    channels = CHANNELS
    samplewidth = 2
    samplerate = SAMPLERATE
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


def test_read_wav(wav_file):
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

    assert np.all(decoder.read() == 0)


def test_basic_metadata(wav_file):
    decoder = AudioDecoder(wav_file)
    assert decoder.channels == CHANNELS
    assert decoder.samplerate == SAMPLERATE


def test_delete(wav_file):
    """ Ensure that AudioDecoder.__dealloc__ does not crash """
    decoder = AudioDecoder(wav_file)
    del decoder


def test_read_ogg():
    """ Test that AudioDecoder can read channels, samplerate, and audio
    from an Ogg Vorbis file """

    filename = os.path.join(
        os.path.dirname(__file__), 'data', 'short-noise-with-metadata.ogg')
    decoder = AudioDecoder(filename)

    assert decoder.channels == 2
    assert decoder.samplerate == 44100

    while not decoder.is_eos():
        # FIXME: This occasionally fails
        assert len(decoder.read()) > 0


def test_seek(wav_file):
    wav_reader = wave.open(wav_file, 'rb')
    decoder = AudioDecoder(wav_file)

    # Seek to 0:05
    wav_reader.readframes(SAMPLERATE * 5)
    assert decoder.seek(5.0)

    # Compare WAV reader and AudioDecoder output after seek
    decoder_samples = decoder.read()
    assert len(decoder_samples) > 32  # Won't do much good to compare a tiny number of samples
    wav_samples = np.frombuffer(
        wav_reader.readframes(len(decoder_samples) / CHANNELS),
        dtype='<i2').astype(np.float32) / 2.0 ** 15
    assert np.allclose(decoder_samples, wav_samples)


def test_position(wav_file):
    filename = os.path.join(
        os.path.dirname(__file__), 'data', 'short-noise-with-metadata.ogg')
    decoder = AudioDecoder(filename)
    decoder.seek(0.5)
    assert decoder.position == 0.5
