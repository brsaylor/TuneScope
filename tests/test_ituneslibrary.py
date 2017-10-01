import os.path

import pytest
import numpy as np

from tunescope.ituneslibrary import ITunesLibrary
import tunescope.ituneslibrary



@pytest.fixture(scope='session')
def library_filepath():
    """ Test itunes.xml library file"""
    return os.path.join(
        os.path.dirname(__file__), 'data','test-itunes-library.xml')

def test_open_nonexistent_file():
    with pytest.raises(IOError):
        ITunesLibrary('nonexistent file')


def test_get_metadata_by_filepath(library_filepath):
    lib = ITunesLibrary(library_filepath)
    metadata = lib.get_metadata_by_filepath('/Users/zia/Music/iTunes/iTunes Media/Music/n-generator/testing/presentation_tune.mp3')
    assert metadata.title == 'presentation_tune'
    assert metadata.artist == 'n-generator'
    assert metadata.album == 'testing'
    assert np.isclose(metadata.duration, 11.180)


def test_get_metadata_for_noexistent_track(library_filepath):
    lib = ITunesLibrary(library_filepath)
    with pytest.raises(KeyError):
        metadata = lib.get_metadata_by_filepath('nonexistent Track')


def test_open_default_library(monkeypatch, library_filepath):
    monkeypatch.setattr(tunescope.ituneslibrary, '_DEFAULT_LIBRARY_FILEPATH_MACOS', library_filepath)
    ITunesLibrary()


def test_find_itunes_library(monkeypatch, library_filepath):
    monkeypatch.setattr(tunescope.ituneslibrary, '_DEFAULT_LIBRARY_FILEPATH_MACOS', library_filepath)
    assert ITunesLibrary.find_itunes_library() == library_filepath


def test_find_itunes_library_not_found(monkeypatch):
    monkeypatch.setattr(tunescope.ituneslibrary, '_DEFAULT_LIBRARY_FILEPATH_MACOS', 'nonexistent Library')
    assert ITunesLibrary.find_itunes_library() is None
