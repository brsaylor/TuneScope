import os.path

import numpy as np
cimport numpy as np

from tunescope cimport audiobackend


cdef extern from "audiodecoder-gst.c":

    ctypedef struct AudioDecoderBuffer:
        size_t capacity
        size_t size
        float *samples

    ctypedef struct AudioDecoderMetadata:
        int channels
        int samplerate

    ctypedef struct AudioDecoderHandle:
        pass

    AudioDecoderHandle *audiodecoder_gst_new(char *filename)
    AudioDecoderBuffer *audiodecoder_gst_read(AudioDecoderHandle *handle)
    AudioDecoderMetadata *audiodecoder_gst_get_metadata(AudioDecoderHandle *handle)
    int audiodecoder_gst_seek(AudioDecoderHandle *handle, double position)
    int audiodecoder_gst_is_eos(AudioDecoderHandle *handle)
    void audiodecoder_gst_delete(AudioDecoderHandle *handle)


cdef class AudioDecoder:
    """
    Decodes audio data and metadata from a file
    """

    cdef AudioDecoderHandle *_handle
    cdef AudioDecoderMetadata *_metadata;

    def __cinit__(self, filename):
        if not os.path.isfile(filename):
            raise IOError("No such file: '{}'".format(filename))
        audiobackend.initialize_if_not_initialized()
        self._handle = audiodecoder_gst_new(filename)
        self._metadata = audiodecoder_gst_get_metadata(self._handle)

    cpdef bint is_eos(self):
        """ Return True if end-of-stream has been reached """
        return audiodecoder_gst_is_eos(self._handle)

    cpdef np.ndarray[np.float32_t] read(self):
        """
        Read a block of 32-bit float channel-interleaved audio samples
        from the file as a numpy.ndarray.
        The number of samples returned is not configurable and may vary.
        If called beyond the end of the stream, a zero-filled array is returned.
        """
        cdef AudioDecoderBuffer *buf = audiodecoder_gst_read(self._handle)

        # Get the samples as a memoryview slice
        cdef float[:] samples_view = <float[:buf.size]> buf.samples

        # Copy the samples to a NumPy array
        samples_array = np.empty((buf.size,), dtype=np.float32)
        cdef float[:] samples_array_view = samples_array
        samples_array_view[...] = samples_view

        return samples_array

    cpdef bint seek(self, double position):
        """ Seek to the given position in seconds.
        Return True on success, False on failure. """
        return audiodecoder_gst_seek(self._handle, position)

    @property
    def channels(self):
        return self._metadata.channels

    @property
    def samplerate(self):
        return self._metadata.samplerate

    def __dealloc__(self):
        if self._handle != NULL:
            audiodecoder_gst_delete(self._handle)
