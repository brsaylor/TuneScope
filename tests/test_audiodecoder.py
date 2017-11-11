import os.path
import wave

import pytest
import numpy as np

from tunescope.audio import AudioDecoder

# TODO: Test reading audio from video files


def test_nonexistent_file():
    with pytest.raises(IOError):
        AudioDecoder('nonexistent-file')


def test_read_wav(wav_file, wav_file_params):
    """ Test that AudioDecoder can read a WAV file correctly """
    wav_reader = wave.open(wav_file, 'rb')
    decoder = AudioDecoder(wav_file)

    total_frame_count = wav_reader.getnframes()
    frames_read = 0

    while not decoder.is_eos():
        decoder_samples = decoder.read()
        frames_read += len(decoder_samples) / wav_file_params['channels']
        assert len(decoder_samples > 1)
        wav_samples = np.frombuffer(
            wav_reader.readframes(len(decoder_samples) / wav_file_params['channels']),
            dtype='<i2').astype(np.float32) / 2.0 ** 15
        assert np.allclose(decoder_samples, wav_samples)

    assert frames_read == total_frame_count

    assert np.all(decoder.read() == 0)


def test_basic_metadata(wav_file, wav_file_params):
    decoder = AudioDecoder(wav_file)
    assert decoder.channels == wav_file_params['channels']
    assert decoder.samplerate == wav_file_params['samplerate']


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


def test_seek(wav_file, wav_file_params):
    wav_reader = wave.open(wav_file, 'rb')
    decoder = AudioDecoder(wav_file)

    # Seek to 0:05
    wav_reader.readframes(wav_file_params['samplerate'] * 5)
    assert decoder.seek(5.0)

    # Compare WAV reader and AudioDecoder output after seek
    decoder_samples = decoder.read()
    assert len(decoder_samples) > 32  # Won't do much good to compare a tiny number of samples
    wav_samples = np.frombuffer(
        wav_reader.readframes(len(decoder_samples) / wav_file_params['channels']),
        dtype='<i2').astype(np.float32) / 2.0 ** 15
    assert np.allclose(decoder_samples, wav_samples)


def test_position(wav_file):
    filename = os.path.join(
        os.path.dirname(__file__), 'data', 'short-noise-with-metadata.ogg')
    decoder = AudioDecoder(filename)
    decoder.seek(0.5)
    assert np.isclose(decoder.position, 0.5, atol=0.01)


def test_seek_after_eos(wav_file, wav_file_samples):

    # Read file to end
    decoder = AudioDecoder(wav_file)
    while not decoder.is_eos():
        decoder.read()

    # Seek back to start
    decoder.seek(0)
    assert np.isclose(decoder.position, 0, atol=0.05)

    # Make an array to hold samples decoded after seeking back to 0,
    # adding some padding at the end
    padding = 4096
    samples_after_seek = np.zeros(len(wav_file_samples) + padding, dtype=np.float32)
    
    # Decode entire file again
    pos = 0  # position in samples
    while not decoder.is_eos():
        block = decoder.read()
        samples_after_seek[pos: pos + len(block)] = block
        pos += len(block)

    assert np.allclose(samples_after_seek[:len(wav_file_samples)],
                       wav_file_samples, atol=0.001)


def test_read_invalid_file(tmpdir_factory):
    file_path = str(tmpdir_factory.mktemp('audio').join('random.raw'))
    with open(file_path, 'wb') as f:
        f.write(np.random.bytes(1000))
    with pytest.raises(IOError, match='Could not determine type of stream'):
        AudioDecoder(file_path)
