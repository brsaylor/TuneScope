import os.path

# FIXME: Python 2 code
from pathlib2 import Path

from . cimport audiobackend


cdef extern from "audiometadata-gst.c":

    ctypedef struct AudioMetadataStruct:
        double duration
        char *title
        char *artist
        char *album

    AudioMetadataStruct *audiometadata_gst_read(char *filename)
    void audiometadata_gst_delete(AudioMetadataStruct *metadata)


cdef class AudioMetadata:
    """ Provides duration and basic tags data for the given audio file """

    cdef readonly double duration
    cdef readonly unicode title  # FIXME Python 2 code
    cdef readonly unicode artist
    cdef readonly unicode album

    def __cinit__(self, filename):
        audiobackend.initialize_if_not_initialized()

    def __init__(self, filename):
        if not os.path.isfile(filename):
            raise IOError("No such file: '{}'".format(filename))

        metadata_struct = audiometadata_gst_read(Path(filename).as_uri())

        if metadata_struct == NULL:
            raise IOError("Error reading metadata from {}".format(filename))

        self.duration = metadata_struct.duration
        self.title = _c_string_to_unicode(metadata_struct.title)
        self.artist = _c_string_to_unicode(metadata_struct.artist)
        self.album = _c_string_to_unicode(metadata_struct.album)

        audiometadata_gst_delete(metadata_struct)


cdef unicode _c_string_to_unicode(char *string):
    if string == NULL:
        return u''
    return string.decode('UTF-8')
