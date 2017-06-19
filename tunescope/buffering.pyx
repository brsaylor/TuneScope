import numpy as np
cimport numpy as np

from tunescope.audioutil cimport pad_block


cdef class StreamBuffer:
    """
    A queue for buffering streaming data represented as 1-dimensional
    NumPy float32 arrays. Input and output array sizes are independent and can vary.
    Implemented as a ring buffer.
    """

    cdef readonly size_t capacity
    """ Maximum number of elements the buffer can hold """

    cdef readonly size_t size
    """ Current number of elements the buffer holds """

    cdef np.ndarray _buffer
    cdef size_t _start

    def __cinit__(self, size_t capacity):
        self._buffer = np.zeros(capacity, dtype=np.float32)
        self.capacity = capacity
        self.size = 0
        self._start = 0
    
    cpdef bint put(self, np.ndarray[np.float32_t] data):
        """
        Add data to queue.
        Return False if there isn't enough space; True otherwise.
        """
        if len(data) > self.capacity - self.size:
            return False

        cdef float [:] buffer_view = self._buffer
        cdef size_t end = self._start + self.size
        cdef int i
        for i in range(len(data)):
            buffer_view[(end + i) % self.capacity] = data[i]
        self.size += len(data)

        return True

    cpdef np.ndarray get(self, size_t count):
        """
        Remove and return `count` data elements from the queue.
        If there are fewer than `count` elements, return all remaining elements.
        """
        count = min(self.size, count)

        cdef float [:] buffer_view = self._buffer
        cdef np.ndarray[np.float32_t] output_block = np.empty(count, dtype=np.float32)
        cdef int i
        for i in range(count):
            output_block[i] = buffer_view[(self._start + i) % self.capacity]

        self._start = (self._start + count) % self.capacity
        self.size -= count

        return output_block

    cpdef expand(self, size_t new_capacity):
        """
        Increase the capacity of the queue.
        `new_capacity` must be larger than existing capacity
        (otherwise, the method does nothing).
        """
        if new_capacity <= self.capacity:
            return
        self._buffer = np.roll(self._buffer, -1 * <long> self._start)
        self._buffer = np.resize(self._buffer, new_capacity)
        self.capacity = new_capacity
        self._start = 0


cdef class DecoderBuffer:
    """
    Buffers the output of an AudioDecoder
    to allow reading blocks of arbitrary size.
    """

    cdef object _decoder  # Normally an AudioDecoder, but `object` here to allow a test double
    cdef StreamBuffer _stream_buffer

    def __cinit__(self, object decoder, size_t initial_capacity):
        """ Create a DecoderBuffer with the given AudioDecoder `decoder`.
        The internal buffer will be able to hold `initial_capacity` samples,
        and will be expanded as necessary. """

        self._decoder = decoder
        self._stream_buffer = StreamBuffer(initial_capacity)

    @property
    def channels(self):
        return self._decoder.channels

    @property
    def samplerate(self):
        return self._decoder.samplerate

    cpdef np.ndarray read(self, size_t sample_count):
        """ Read a block of `sample_count` samples from the decoder,
        raising EOFError if there are no more sample to be read.
        The last block of the stream is zero-padded if necessary. """

        if self.is_eos():
            raise EOFError()

        self._fill_stream_buffer(sample_count)
        cdef np.ndarray[np.float32_t] block = self._stream_buffer.get(sample_count)
        if len(block) < sample_count:
            block = pad_block(block, sample_count)
        return block

    cpdef bint is_eos(self):
        """ Return True if end-of-stream has been reached
        and buffer has been emptied """
        return self._decoder.is_eos() and self._stream_buffer.size == 0

    cdef _fill_stream_buffer(self, size_t target_size):
        cdef np.ndarray[np.float32_t] input_block
        cdef size_t free_space
        cdef size_t required_capacity

        while self._stream_buffer.size < target_size and not self._decoder.is_eos():
            input_block = self._decoder.read()
            free_space = self._stream_buffer.capacity - self._stream_buffer.size
            if len(input_block) > free_space:
                required_capacity = self._stream_buffer.capacity + len(input_block)
                self._stream_buffer.expand(required_capacity)
            self._stream_buffer.put(input_block)
