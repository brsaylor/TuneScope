import pytest
import numpy as np

from tunescope.buffering import StreamBuffer, DecoderBuffer
from test_doubles import FakeAudioDecoder


class TestStreamBuffer(object):

    # StreamBuffers of various capacities

    @pytest.fixture()
    def sb3(self):
        return StreamBuffer(3)

    @pytest.fixture()
    def sb4(self):
        return StreamBuffer(4)

    @pytest.fixture()
    def sb6(self):
        return StreamBuffer(6)

    # Tests

    def test_capacity(self, sb3):
        assert sb3.capacity == 3

    def test_size_empty(self, sb3):
        assert sb3.size == 0

    def test_put_not_enough_space(self, sb3):
        assert not sb3.put(np.arange(4, dtype=np.float32))

    def test_size_after_put(self, sb3):
        sb3.put(np.arange(3, dtype=np.float32))
        assert sb3.size == 3

    def test_get_empty(self, sb3):
        a = sb3.get(9)
        assert len(a) == 0

    def test_put_get(self, sb3):
        sb3.put(np.arange(3, dtype=np.float32))
        out = sb3.get(3)
        assert sb3.size == 0
        assert np.all(out == np.arange(3))

    def test_fill_empty(self, sb6):

        # Fill the queue
        sb6.put(np.array([0, 1], dtype=np.float32))
        sb6.put(np.array([0, 1, 2, 3], dtype=np.float32))
        assert sb6.size == 6

        # Get 4 elements (overlapping both input buffers)
        assert np.all(sb6.get(4) == np.array([0, 1, 0, 1], dtype=np.float32))
        assert sb6.size == 2

        # Get the remaining two elements
        assert np.all(sb6.get(2) == np.array([2, 3], dtype=np.float32))
        assert sb6.size == 0

    def test_wraparound(self, sb4):
        sb4.put(np.arange(3, dtype=np.float32))
        sb4.get(3)
        assert sb4.size == 0
        sb4.put(np.arange(3, dtype=np.float32))
        assert sb4.size == 3
        assert np.all(sb4.get(3) == np.arange(3, dtype=np.float32))
        assert sb4.size == 0

    def test_get_more_than_size(self, sb4):
        sb4.put(np.arange(3, dtype=np.float32))
        assert np.all(sb4.get(4) == np.arange(3, dtype=np.float32))
        assert sb4.size == 0

    def test_expand_empty_buffer(self, sb4):
        sb = sb4
        sb.expand(5)
        assert sb.capacity == 5
        assert sb.size == 0

    def test_expand_after_putting(self, sb3):
        sb = sb3
        sb.put(np.arange(2, dtype=np.float32))
        sb.expand(4)
        assert np.all(sb.get(2) == np.arange(2, dtype=np.float32))

    def test_expand_full_wraparound(self, sb4):
        sb = sb4
        sb.put(np.array([0, 1, 2], dtype=np.float32))
        # sb now contains  0 1 2 _
        assert np.all(sb.get(2) == np.array([0, 1], dtype=np.float32))
        # sb now contains  _ _ 2 _
        assert sb.size == 1
        sb.put(np.array([3, 4, 5], dtype=np.float32))
        # sb now contains      2 3 | 4 5
        # where | is the wraparound point
        assert sb.size == 4
        sb.expand(5)
        # sb now contains 2 3 4 5 _
        out4 = sb.get(4)
        assert np.all(out4 == np.array([2, 3, 4, 5], dtype=np.float32))

    def test_clear(self, sb4):
        sb4.clear()
        assert sb4.size == 0
        assert len(sb4.get(4)) == 0


class TestDecoderBuffer(object):

    def test_empty_stream_is_eos(self):
        decoder = FakeAudioDecoder([])
        buf = DecoderBuffer(decoder, 4)
        assert buf.is_eos()

    def test_read_from_finished_stream(self):
        decoder = FakeAudioDecoder([])
        buf = DecoderBuffer(decoder, 4)
        assert np.all(buf.read(1) == np.zeros(1))

    def test_read_single_block(self):
        decoder = FakeAudioDecoder([[0, 1, 2, 3]])
        buf = DecoderBuffer(decoder, 4)
        block = buf.read(4)
        assert np.all(block == np.arange(4))

    def test_read_two_blocks(self):
        decoder = FakeAudioDecoder([[0, 1, 2, 3]])
        buf = DecoderBuffer(decoder, 4)
        block1 = buf.read(2)
        assert np.all(block1 == np.array([0, 1]))
        block2 = buf.read(2)
        assert np.all(block2 == np.array([2, 3]))

    def test_read_past_end(self):
        decoder = FakeAudioDecoder([[0, 1, 2]])
        buf = DecoderBuffer(decoder, 4)
        block = buf.read(4)
        assert np.all(block == np.array([0, 1, 2, 0]))

    def test_not_eos_until_streambuffer_empty(self):
        decoder = FakeAudioDecoder([[0, 1, 2, 3]])
        buf = DecoderBuffer(decoder, 4)
        buf.read(2)
        assert not buf.is_eos()
        buf.read(2)
        assert buf.is_eos()

    def test_streambuffer_expand_required(self):
        decoder = FakeAudioDecoder([[0, 1, 2, 3]])
        buf = DecoderBuffer(decoder, 3)
        assert np.all(buf.read(4) == np.array([0, 1, 2, 3]))

    def test_different_input_output_boundaries(self):
        decoder = FakeAudioDecoder([[0, 1], [2, 3, 4]])
        buf = DecoderBuffer(decoder, 4)
        block1 = buf.read(3)
        assert np.all(block1 == np.array([0, 1, 2]))
        block2 = buf.read(2)
        assert np.all(block2 == np.array([3, 4]))

    def test_position(self):
        decoder = FakeAudioDecoder([range(12)])  # 2 seconds
        decoder.channels = 2
        decoder.samplerate = 3
        buf = DecoderBuffer(decoder, 100)
        assert buf.position == 0
        buf.read(6)  # Read 1 second
        assert buf.position == 1

    def test_seek(self):
        decoder = FakeAudioDecoder([range(12)])  # 2 seconds
        decoder.channels = 2
        decoder.samplerate = 3
        buf = DecoderBuffer(decoder, 100)
        buf.read(6)  # Read 1 second
        buf.seek(0)
        assert buf.position == 0
