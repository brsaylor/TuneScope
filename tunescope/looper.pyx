import numpy as np
cimport numpy as np
from numpy cimport ndarray, float32_t


cdef class Looper:
    """
    Allows looping regions of audio. `audio_source` must implement `read()`,
    `seek()`, and `position`.
    """

    cdef readonly int channels
    cdef readonly int samplerate

    cdef readonly bint active
    """ True if looping is enabled; otherwise, `read()` passively returns blocks
    read from `audio_source` """

    cdef object _audio_source
    cdef ndarray _output_buffer  # Array of samples filled and returned by read()
    cdef double _start_pos_seconds, _end_pos_seconds  # Loop bounds in seconds
    cdef size_t _start_pos_samples, _end_pos_samples  # Loop bounds in samples

    def __cinit__(self, object audio_source):
        self.channels = audio_source.channels
        self.samplerate = audio_source.samplerate
        self.active = False
        self._audio_source = audio_source
        self._output_buffer = np.array([], dtype=np.float32)

    def activate(self, start_pos, end_pos):
        """ Begin looping for the region `start_pos` and `end_pos`, which are
        specified in seconds """
        if start_pos < 0 or end_pos <= start_pos:
            raise ValueError()
        self._start_pos_seconds = start_pos
        self._end_pos_seconds = end_pos
        self._start_pos_samples = start_pos * self.samplerate * self.channels
        self._end_pos_samples = end_pos * self.samplerate * self.channels
        self.active = True

    def deactivate(self):
        """ Stop looping and continue normal playback """
        self.active = False

    cpdef ndarray read(self, size_t sample_count):
        """ Read a block of `sample_count` samples from `audio_source`, looping
        if active. Returned array should be treated as read-only """
        if not self.active:
            return self._audio_source.read(sample_count)
        if len(self._output_buffer) < sample_count:
            self._output_buffer = np.resize(self._output_buffer, sample_count)
        if self._audio_source.position > self._end_pos_seconds:
            self._audio_source.seek(self._start_pos_seconds)

        cdef size_t samples_buffered = self._buffer_more_input(sample_count, 0)
        while samples_buffered < sample_count:
            self._audio_source.seek(self._start_pos_seconds)
            samples_buffered = self._buffer_more_input(sample_count, samples_buffered)

        return self._output_buffer[:samples_buffered]

    cpdef bint is_eos(self):
        """ Return True if end-of-stream has been reached
        and looping is not enabled """
        return not self.active and self._audio_source.is_eos()

    cdef size_t _buffer_more_input(self, size_t target_sample_count, size_t samples_buffered):
        """ Fill output buffer until there are `target_sample_count` samples
        buffered, or end of loop is reached, whichever comes first.
        `samples_buffered` is the current number of samples in the output
        buffer. Return new number of samples in output buffer. """
        cdef size_t cur_pos_samples = (self._audio_source.position
                                       * self.samplerate
                                       * self.channels)
        cdef size_t samples_to_read = min(target_sample_count - samples_buffered,
                                          self._end_pos_samples - cur_pos_samples)
        self._output_buffer[ samples_buffered : samples_buffered + samples_to_read ] = \
            self._audio_source.read(samples_to_read)
        samples_buffered += samples_to_read
        return samples_buffered
