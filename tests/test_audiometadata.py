import os.path

import pytest

from tunescope.audio import AudioMetadata


def test_nonexistent_file():
    with pytest.raises(IOError):
        AudioMetadata('nonexistent-file')


def test_read_metadata():
    filename = os.path.join(
        os.path.dirname(__file__), 'data', 'short-noise-with-metadata.ogg')

    metadata = AudioMetadata(filename)

    assert metadata.duration == 1.0
    assert metadata.title == 'Test Track'
    assert metadata.artist == 'Test Artist'
    assert metadata.album == 'Test Album'


def test_file_with_no_tags(wav_file, wav_file_params):
    metadata = AudioMetadata(wav_file)
    assert metadata.duration == wav_file_params['duration']
    assert metadata.title == ''
    assert metadata.artist == ''
    assert metadata.album == ''
