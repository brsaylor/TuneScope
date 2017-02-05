import numpy as np


sample_dtype = np.float32


def copy_buffer(src, src_pos, dest, dest_pos, length):
    """ Copy sample frames from a buffer into a NumPy array.

    The destination array is assumed to be 2-dimensional, with rows
    representing frames and columns representing channels. The source
    buffer is assumed to contain interleaved samples of the same data type
    as the destination, with the same number of channels.

    Parameters
    ----------
    src : buffer-like
        The source buffer (e.g. a bytes object)
    src_pos : int
        Starting frame position in the source buffer
    dest : ndarray
        The destination array
    dest_pos : int
        Starting frame position in the destination array
    length
        Number of frames to copy
    """

    # Create 1-dimensional memoryviews of the bytes in src and dest
    src_mem = memoryview(src)
    dest_mem = dest.data.cast('B', (dest.data.nbytes,))

    # Calculate src and dest byte offsets
    bytes_per_frame = dest.dtype.itemsize * dest.shape[1]
    length_bytes = length * bytes_per_frame
    s1 = src_pos * bytes_per_frame
    s2 = s1 + length_bytes
    d1 = dest_pos * bytes_per_frame
    d2 = d1 + length_bytes

    # Copy the data (this should be the only copy performed!)
    dest_mem[d1:d2] = src_mem[s1:s2]


class QueueFullError(Exception):
    pass


class AudioQueue(object):
    """ Queue for audio frames for re-buffering purposes.

    Works with 32-bit floating-point, channel-interleaved data.
    """

    def __init__(self, channels, capacity):
        """ Instantiate an AudioQueue.

        Parameters
        ----------
        channels : int
            Number of channels
        capacity : int
            Maximum number of sample frames that can fit in the queue
        """

        # Ring buffer to hold queued frames
        self._buffer = np.empty(shape=(capacity, channels), dtype=sample_dtype)
        self._start = 0  # start index of queued frames in _buffer
        self._size = 0   # number of queued frames in buffer

    @property
    def channels(self):
        """ Number of audio channels """
        return self._buffer.shape[1]

    @property
    def capacity(self):
        """ Capacity of the queue in sample frames """
        return self._buffer.shape[0]

    @property
    def size(self):
        """ Number of sample frames in the queue """
        return self._size

    @property
    def free_space(self):
        """ Amount of free space in the queue in sample frames """
        return self.capacity - self.size

    def put(self, buffer):
        """ Add a buffer to the queue.

        The buffer is assumed to be 32-bit floating point interleaved data
        with the same number of channels as the queue.

        Parameters
        ----------
        buffer : buffer-like
            Buffer to add to the queue (e.g. a bytes object)
        """
        frame_count = len(buffer) // self.channels // sample_dtype().itemsize
        if frame_count > self.free_space:
            raise QueueFullError()

        end = self._start + self._size
        first_chunk_size = min(frame_count, self.capacity - end)
        if frame_count <= first_chunk_size:
            copy_buffer(buffer, 0, self._buffer, end, frame_count)
        else:
            second_chunk_size = frame_count - first_chunk_size
            copy_buffer(buffer, 0, self._buffer, end, first_chunk_size)
            copy_buffer(buffer, first_chunk_size, self._buffer, 0, second_chunk_size)
        self._size += frame_count

    def get(self, frame_count):
        """ Remove and return a chunk of audio from the queue.

        Parameters
        ----------
        frame_count : int
            Number of sample frames to retrieve

        Returns
        -------
        numpy.ndarray
            Retrieved sample frames as a frame_count x channels array
        """
        if frame_count > self._size:
            raise RuntimeError("Not enough frames in AudioQueue")

        chunk_end = self._start + frame_count
        if chunk_end > self.capacity:
            chunk_end -= self.capacity
            chunk = np.concatenate((
                self._buffer[self._start:],
                self._buffer[:chunk_end]
            ))
        else:
            chunk = self._buffer[self._start:chunk_end]
        self._start = chunk_end % self.capacity
        self._size -= frame_count

        return chunk

    def expand(self, new_capacity):
        """ Increase the capacity of the queue.

        Parameters
        ----------
        new_capacity : int
            New capacity for the queue; must be larger than existing capacity
        """
        if new_capacity <= self.capacity:
            raise RuntimeError("Decreasing AudioQueue capacity is not supported")

        self._buffer = np.roll(self._buffer, -self._start, axis=0)
        self._buffer.resize((new_capacity, self.channels))
        self._start = 0
