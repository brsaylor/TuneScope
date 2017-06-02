import pytest
import numpy as np

from tunescope.buffering import StreamBuffer

default_dtype = np.array([1]).dtype


class TestStreamBuffer(object):

    # StreamBuffers of various capacities

    @pytest.fixture()
    def sb3(self):
        return StreamBuffer(3, default_dtype)

    @pytest.fixture()
    def sb4(self):
        return StreamBuffer(4, default_dtype)

    @pytest.fixture()
    def sb6(self):
        return StreamBuffer(6, default_dtype)

    # Tests

    def test_capacity(self, sb3):
        assert sb3.capacity == 3

    def test_size_empty(self, sb3):
        assert sb3.size == 0

    def test_put_not_enough_space(self, sb3):
        assert not sb3.put(np.arange(4))

    def test_size_after_put(self, sb3):
        sb3.put(np.arange(3))
        assert sb3.size == 3

    def test_get_empty(self, sb3):
        a = sb3.get(9)
        assert len(a) == 0

    def test_put_get(self, sb3):
        sb3.put(np.arange(3))
        out = sb3.get(3)
        assert sb3.size == 0
        assert np.all(out == np.arange(3))

    def test_fill_empty(self, sb6):

        # Fill the queue
        sb6.put(np.array([0, 1]))
        sb6.put(np.array([0, 1, 2, 3]))
        assert sb6.size == 6

        # Get 4 elements (overlapping both input buffers)
        assert np.all(sb6.get(4) == np.array([0, 1, 0, 1]))
        assert sb6.size == 2

        # Get the remaining two elements
        assert np.all(sb6.get(2) == np.array([2, 3]))
        assert sb6.size == 0

    def test_wraparound(self, sb4):
        sb4.put(np.arange(3))
        sb4.get(3)
        assert sb4.size == 0
        sb4.put(np.arange(3))
        assert sb4.size == 3
        assert np.all(sb4.get(3) == np.arange(3))
        assert sb4.size == 0

    def test_get_more_than_size(self, sb4):
        sb4.put(np.arange(3))
        assert np.all(sb4.get(4) == np.arange(3))
        assert sb4.size == 0

    def test_expand_empty_buffer(self, sb4):
        sb = sb4
        sb.expand(5)
        assert sb.capacity == 5
        assert sb.size == 0

    def test_expand_after_putting(self, sb3):
        sb = sb3
        sb.put(np.arange(2))
        sb.expand(4)
        assert np.all(sb.get(2) == np.arange(2))

    def test_expand_full_wraparound(self, sb4):
        sb = sb4
        sb.put(np.array([0, 1, 2]))
        # sb now contains  0 1 2 _
        assert np.all(sb.get(2) == np.array([0, 1]))
        # sb now contains  _ _ 2 _
        assert sb.size == 1
        sb.put(np.array([3, 4, 5]))
        # sb now contains      2 3 | 4 5
        # where | is the wraparound point
        assert sb.size == 4
        sb.expand(5)
        # sb now contains 2 3 4 5 _
        out4 = sb.get(4)
        assert np.all(out4 == np.array([2, 3, 4, 5]))
