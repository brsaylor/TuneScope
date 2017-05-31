import os.path

import numpy as np
cimport numpy as np


cdef extern from "audiodecoder-gst.c":

    ctypedef struct AudioDecoderBuffer:
        size_t capacity
        size_t size
        float *samples

    ctypedef struct AudioDecoderHandle:
        pass

    AudioDecoderHandle *audiodecoder_gst_new(char *filename)
    AudioDecoderBuffer *audiodecoder_gst_read(AudioDecoderHandle *handle)
    int audiodecoder_gst_is_eos(AudioDecoderHandle *handle)
    void audiodecoder_gst_delete(AudioDecoderHandle *handle)


# TODO: Make this implement a context manager
cdef class AudioDecoder:
    """
    Decodes audio data and metadata from a file
    """

    cdef AudioDecoderHandle *handle
    cdef int x

    def __cinit__(self, filename):
        if not os.path.isfile(filename):
            raise IOError("No such file: '{}'".format(filename))
        self.handle = audiodecoder_gst_new(filename)
        self.x = 123

    cpdef bint is_eos(self):
        """ Return True if end-of-stream has been reached """
        return audiodecoder_gst_is_eos(self.handle)

    cpdef np.ndarray read(self):
        """
        Read a block of 32-bit float audio samples from the file as a numpy.ndarray.
        The number of samples returned is not configurable and may vary.
        """
        cdef AudioDecoderBuffer *buf = audiodecoder_gst_read(self.handle)
        if buf == NULL:
            raise EOFError

        # Get the samples as a memoryview slice
        cdef float[:] samples_view = <float[:buf.size]> buf.samples

        # Copy the samples to a NumPy array
        # TODO: Avoid copying?
        samples_array = np.empty((buf.size,), dtype=np.float32)
        cdef float[:] samples_array_view = samples_array
        samples_array_view[...] = samples_view

        return samples_array

    def __dealloc__(self):
        if self.handle != NULL:
            audiodecoder_gst_delete(self.handle)
