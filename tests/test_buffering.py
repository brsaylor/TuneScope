import pytest
import numpy as np

from tunescope.buffering import StreamBuffer, DecoderBuffer

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


class FakeAudioDecoder(object):
    """ Test double for AudioDecoder """

    def __init__(self, blocks):
        """ `blocks` is a list of lists representing the blocks of samples
        returned by each call to read() """
        self._blocks = (np.array(values) for values in blocks)
        self._blocks_remaining = len(blocks)

    def read(self):
        if self._blocks_remaining <= 0:
            raise EOFError
        self._blocks_remaining -= 1
        return next(self._blocks)

    def is_eos(self):
        return self._blocks_remaining == 0


class TestFakeAudioDecoder(object):

    def test_read_empty_stream(self):
        fake_decoder = FakeAudioDecoder([])
        with pytest.raises(EOFError):
            fake_decoder.read()
        assert fake_decoder.is_eos()

    def test_read_entire_stream(self):
        fake_decoder = FakeAudioDecoder([[1, 2], [3, 4]])
        data_read = []
        while not fake_decoder.is_eos():
            data_read += list(fake_decoder.read())
        assert data_read == [1, 2, 3, 4]


class TestDecoderBuffer(object):

    def test_empty_stream_is_eos(self):
        fake_decoder = FakeAudioDecoder([])
        buf = DecoderBuffer(fake_decoder, 4)
        assert buf.is_eos()

    def test_read_from_finished_stream(self):
        fake_decoder = FakeAudioDecoder([])
        buf = DecoderBuffer(fake_decoder, 4)
        with pytest.raises(EOFError):
            buf.read(1)

    def test_read_single_block(self):
        fake_decoder = FakeAudioDecoder([[0, 1, 2, 3]])
        buf = DecoderBuffer(fake_decoder, 4)
        block = buf.read(4)
        assert np.all(block == np.arange(4))

    def test_read_two_blocks(self):
        fake_decoder = FakeAudioDecoder([[0, 1, 2, 3]])
        buf = DecoderBuffer(fake_decoder, 4)
        block1 = buf.read(2)
        assert np.all(block1 == np.array([0, 1]))
        block2 = buf.read(2)
        assert np.all(block2 == np.array([2, 3]))

    def test_read_past_end(self):
        fake_decoder = FakeAudioDecoder([[0, 1, 2]])
        buf = DecoderBuffer(fake_decoder, 4)
        block = buf.read(4)
        assert np.all(block == np.array([0, 1, 2, 0]))

    def test_not_eos_until_streambuffer_empty(self):
        fake_decoder = FakeAudioDecoder([[0, 1, 2, 3]])
        buf = DecoderBuffer(fake_decoder, 4)
        buf.read(2)
        assert not buf.is_eos()
        buf.read(2)
        assert buf.is_eos()

    def test_streambuffer_expand_required(self):
        fake_decoder = FakeAudioDecoder([[0, 1, 2, 3]])
        buf = DecoderBuffer(fake_decoder, 3)
        assert np.all(buf.read(4) == np.array([0, 1, 2, 3]))

    def test_different_input_output_boundaries(self):
        fake_decoder = FakeAudioDecoder([[0, 1], [2, 3, 4]])
        buf = DecoderBuffer(fake_decoder, 4)
        block1 = buf.read(3)
        assert np.all(block1 == np.array([0, 1, 2]))
        block2 = buf.read(2)
        assert np.all(block2 == np.array([3, 4]))
