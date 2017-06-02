import numpy as np
cimport numpy as np


cdef class StreamBuffer:
    """
    A queue for buffering streaming data represented as 1-dimensional
    NumPy arrays. Input and output array sizes are independent and can vary.
    """

    cdef readonly size_t capacity
    """ Maximum number of elements the buffer can hold """

    cdef readonly size_t size
    """ Current number of elements the buffer holds """

    cdef np.ndarray _data
    cdef size_t _start

    def __cinit__(self, capacity, dtype):
        self._data = np.zeros(capacity, dtype=dtype)
        self.capacity = capacity
        self.size = 0
        self._start = 0
    
    cpdef bint put(self, np.ndarray data):
        """
        Add data to queue.
        Return False if there isn't enough space; True otherwise.
        """
        if len(data) > self.capacity - self.size:
            return False

        cdef size_t end = self._start + self.size
        cdef size_t first_chunk_size = min(len(data), self.capacity - end)
        cdef size_t second_chunk_size

        if len(data) <= first_chunk_size:
            self._data[end:end+len(data)] = data
        else:
            second_chunk_size = len(data) - first_chunk_size
            self._data[end:] = data[:first_chunk_size]
            self._data[:second_chunk_size] = data[first_chunk_size:]
        self.size += len(data)

        return True

    cpdef np.ndarray get(self, size_t count):
        """
        Remove and return `count` data elements from the queue.
        If there are fewer than `count` elements, return all remaining elements.
        """
        count = min(self.size, count)

        cdef np.ndarray chunk
        cdef chunk_end = self._start + count

        if chunk_end > self.capacity:
            chunk_end -= self.capacity
            chunk = np.concatenate((self._data[self._start:],
                                    self._data[:chunk_end]))
        else:
            chunk = self._data[self._start:chunk_end]
        self._start = chunk_end % self.capacity
        self.size -= count

        return chunk

    cpdef expand(self, size_t new_capacity):
        """
        Increase the capacity of the queue.
        `new_capacity` must be larger than existing capacity
        (otherwise, the method does nothing).
        """
        if new_capacity <= self.capacity:
            return
        self._data = np.roll(self._data, -1 * <long> self._start)
        self._data = np.resize(self._data, new_capacity)
        self.capacity = new_capacity
        self._start = 0
