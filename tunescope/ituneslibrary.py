import os.path
import plistlib
from urllib import url2pathname
'''
needs to fetch a song by filepath.
use libpytunes Song()?

'''
_DEFAULT_LIBRARY_FILEPATH_MACOS = '~/Music/iTunes/iTunes Music Library.xml'

class ITunesLibrary(object):
    def __init__(self, filepath=None):
        if filepath is None:
            filepath = self.find_itunes_library()
        plist = plistlib.readPlist(filepath)
        self._attributes_by_filepath = {}
        for attributes in plist['Tracks'].itervalues():
            filepath = url2pathname(attributes['Location']).replace('file://', '')
            self._attributes_by_filepath[filepath] = attributes

    def get_metadata_by_filepath(self, filepath):
        attributes = self._attributes_by_filepath[filepath]
        metadata = ITunesTrackMetadata()
        metadata.duration = float(attributes['Total Time']) / 1000
        metadata.title = attributes['Name']
        metadata.artist = attributes['Artist']
        metadata.album = attributes['Album']
        return metadata

    @staticmethod
    def find_itunes_library():
        filepath = os.path.expanduser(_DEFAULT_LIBRARY_FILEPATH_MACOS)
        if os.path.exists(filepath):
            return filepath
        else:
            return None


class ITunesTrackMetadata(object):
    pass
