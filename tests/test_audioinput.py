import pytest
import numpy as np

from tunescope.audioinput import *


def test_copy_buffer():

    dtype = np.int32

    # Make source buffer
    src = np.array([
        [10, 20],
        [30, 40],
    ], dtype=dtype).tobytes()

    # Need a new dest array for each test
    def make_dest_array():
        return np.array([
            [1, 2],
            [3, 4],
            [5, 6],
        ], dtype=dtype)

    # Copy first frame of src to first frame of dest
    dest = make_dest_array()
    copy_buffer(src, 0, dest, 0, 1)
    assert np.all(dest == np.array([
        [10, 20],
        [3, 4],
        [5, 6]
    ]))

    # Copy both frames of src to start of dest
    dest = make_dest_array()
    copy_buffer(src, 0, dest, 0, 2)
    assert np.all(dest == np.array([
        [10, 20],
        [30, 40],
        [5, 6]
    ]))

    # Copy both frames of src to end of dest
    dest = make_dest_array()
    copy_buffer(src, 0, dest, 1, 2)
    assert np.all(dest == np.array([
        [1, 2],
        [10, 20],
        [30, 40]
    ]))

    # Try to copy past end of dest
    dest = make_dest_array()
    with pytest.raises(ValueError):
        copy_buffer(src, 0, dest, 2, 2)

    # Try to copy more frames from src than it contains
    dest = make_dest_array()
    with pytest.raises(ValueError):
        copy_buffer(src, 0, dest, 0, 3)


class TestAudioQueue(object):

    @pytest.fixture()
    def q4(self):
        """ A 2-channel queue with capacity 4 """
        return AudioQueue(2, 4)

    @pytest.fixture()
    def q6(self):
        """ A 2-channel queue with capacity 6 """
        return AudioQueue(2, 6)

    @pytest.fixture()
    def buf2(self):
        """ A 2-frame, 2-channel buffer """
        return np.array([
            [0, 1],
            [2, 3]
        ], dtype=sample_dtype).tobytes()

    @pytest.fixture()
    def buf3(self):
        """ A 3-frame, 2-channel buffer """
        return np.array([
            [4, 5],
            [6, 7],
            [8, 9]
        ], dtype=sample_dtype).tobytes()

    @pytest.fixture()
    def buf4(self):
        """ A 4-frame, 2-channel buffer """
        return np.array([
            [10, 11],
            [12, 13],
            [14, 15],
            [16, 17],
        ], dtype=sample_dtype).tobytes()

    def test_init(self, q4):
        assert q4.channels == 2
        assert q4.capacity == 4
        assert q4.size == 0
        assert q4.free_space == 4

    def test_put_get_buf2(self, q4, buf2):
        q4.put(buf2)
        assert q4.size == 2
        assert q4.free_space == 2
        out = q4.get(2)
        assert np.all(out == np.array([
            [0, 1],
            [2, 3]
        ], dtype=sample_dtype))
        assert q4.size == 0
        assert q4.free_space == 4

    def test_fill_empty(self, q6, buf2, buf4):

        # Fill the queue
        q6.put(buf2)
        q6.put(buf4)
        assert q6.size == 6
        assert q6.free_space == 0

        # Get 4 frames (overlapping both input buffers)
        out4 = q6.get(4)
        assert np.all(out4 == np.array([
            [0, 1],
            [2, 3],
            [10, 11],
            [12, 13],
        ], dtype=sample_dtype))
        assert q6.size == 2
        assert q6.free_space == 4

        # Get the remaining two frames
        out2 = q6.get(2)
        assert np.all(out2 == np.array([
            [14, 15],
            [16, 17],
        ], dtype=sample_dtype))
        assert q6.size == 0
        assert q6.free_space == 6

    def test_wraparound(self, q4, buf3):
        q4.put(buf3)
        q4.get(3)
        assert q4.size == 0
        q4.put(buf3)
        assert q4.size == 3
        out3 = q4.get(3)
        assert np.all(out3 == np.array([
            [4, 5],
            [6, 7],
            [8, 9]
        ], dtype=sample_dtype))
        assert q4.size == 0

    def test_overfill(self, q4, buf3):
        q4.put(buf3)
        with pytest.raises(RuntimeError):
            q4.put(buf3)

    def test_overtake(self, q4, buf2):
        q4.put(buf2)
        with pytest.raises(RuntimeError):
            q4.get(3)

    def test_expand_empty(self, q4):
        q = q4
        q.expand(5)
        assert q.capacity == 5
        assert q.size == 0
        assert q.free_space == 5

    def test_expand_full_wraparound(self, q4, buf3):
        q = q4
        q.put(buf3)
        # q now contains [4,5] [6,7] [8,9]
        q.get(2)
        # q now contains             [8,9]
        assert q.size == 1
        q.put(buf3)
        # q now contains             [8,9] [4,5] | [6,7] [8,9]
        # where | is the wraparound point
        assert q.size == 4
        q.expand(5)
        out4 = q.get(4)
        assert np.all(out4 == np.array([
            [8, 9],
            [4, 5],
            [6, 7],
            [8, 9]
        ]))
