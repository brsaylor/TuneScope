"""
Test doubles for use in unit tests, along with tests for them
"""

import threading

import numpy as np

from tunescope.audioutil import pad_block


class FakeAudioSource(object):
    """
    Audio source test double.

    Audio source objects have properties `channels` and `samplerate`
    and methods `is_eos()` and `read(sample_count)`,
    which returns a NumPy float32 array of length `sample_count`.
    Actual audio sources include DecoderBuffer and TimeStretcher.

    Beyond standard functionality,
    provides extra methods and attributes for testing:
        seek(position)
        position
        wait_for_eos_with_timeout()
        wait_for_read_with_timeout()
        read_called
    """

    def __init__(self, channels, samplerate, samples):
        self.channels = channels
        self.samplerate = samplerate
        self.read_called = False

        self._samples = samples.astype(np.float32)
        self._read_position = 0
        self._read_event = threading.Event()
        self._eos_event = threading.Event()

    def read(self, sample_count):
        start = self._read_position
        end = min(start + sample_count, len(self._samples))
        # end = start + sample_count
        self._read_position = end

        if self.is_eos():
            self._eos_event.set()

        self.read_called = True
        self._read_event.set()

        return pad_block(self._samples[start:end], sample_count)

    def is_eos(self):
        return self._read_position >= len(self._samples)

    def wait_for_eos_with_timeout(self, timeout):
        """ Block until entire stream has been read """
        status = self._eos_event.wait(timeout)
        if not status:
            print("waiting for eos_event timed out")

    def wait_for_read_with_timeout(self, timeout):
        """ Block until read() has been called """
        status = self._read_event.wait(timeout)
        if not status:
            print("waiting for read_event timed out")

    def seek(self, position):
        if position < 0:
            return False
        self._read_position = int(position * self.channels * self.samplerate)
        return True

    @property
    def position(self):
        return float(self._read_position) / self.channels / self.samplerate


def test_fake_audio_source():
    fake_source = FakeAudioSource(2, 10, np.arange(20))
    assert np.all(fake_source.read(10) == np.arange(10))
    assert np.all(fake_source.read(12)
                  == np.concatenate((np.arange(10, 20), [0, 0])))
    assert fake_source.is_eos()
    assert np.all(fake_source.read(2) == np.array([0, 0]))

    # These should return immediately
    fake_source.wait_for_eos_with_timeout(0)
    fake_source.wait_for_read_with_timeout(0)

    fake_source.seek(0)
    assert np.all(fake_source.read(5) == np.arange(5))

    fake_source.seek(0.1)
    assert fake_source.position == 0.1
    assert fake_source.read(1) == 2

    # After reading past the end, position should == duration
    fake_source.seek(0)
    fake_source.read(22)
    assert fake_source.position == 1


class FakeAudioDecoder(object):
    """ Test double for AudioDecoder """

    def __init__(self, blocks):
        """ `blocks` is a list of lists representing the blocks of samples
        returned by each call to read() """
        self.channels = 1
        self.samplerate = 100
        self._blocks = [np.array(values, dtype=np.float32) for values in blocks]
        self._next_block_index = 0
        self._samples_read = 0

    def read(self):
        if self.is_eos():
            return np.zeros(4, dtype=np.float32)
        block = self._blocks[self._next_block_index]
        self._samples_read += len(block)
        self._next_block_index += 1
        return block

    @property
    def position(self):
        return self._samples_to_seconds(self._samples_read)

    def seek(self, position):
        self._next_block_index = 0
        self._samples_read = 0
        for block in self._blocks:
            if self._samples_to_seconds(self._samples_read + len(block)) > position:
                break
            self._samples_read += len(block)
            self._next_block_index += 1
        return True

    def is_eos(self):
        return self._next_block_index >= len(self._blocks)

    def _samples_to_seconds(self, samples):
        return float(samples) / self.channels / self.samplerate


class TestFakeAudioDecoder(object):

    def test_read_empty_stream(self):
        decoder = FakeAudioDecoder([])
        block = decoder.read()
        assert len(block) > 0
        assert np.all(block == 0)
        assert decoder.is_eos()

    def test_read_entire_stream(self):
        decoder = FakeAudioDecoder([[1, 2], [3, 4]])
        data_read = []
        while not decoder.is_eos():
            data_read += list(decoder.read())
        assert data_read == [1, 2, 3, 4]

    def test_position(self):
        decoder = FakeAudioDecoder([[1, 2, 3, 4]])
        decoder.channels = 2
        decoder.samplerate = 2
        assert decoder.position == 0
        decoder.read()
        assert decoder.position == 1

    def test_seek_to_block_boundary(self):
        decoder = FakeAudioDecoder([range(6), range(6, 12)])
        decoder.channels = 2
        decoder.samplerate = 3
        decoder.seek(1)
        assert decoder.position == 1
        assert np.all(decoder.read() == range(6, 12))

    def test_seek_between_block_boundaries(self):

        # This assumes that seeking to a position between block boundaries
        # should result in a position at the start of the block containing
        # the seek position.
        # This may or may not accurately reflect GStreamer's behavior.

        decoder = FakeAudioDecoder([range(6), range(6, 12), range(12, 18)])
        decoder.channels = 2
        decoder.samplerate = 3
        decoder.seek(1.5)
        assert decoder.position == 1
        assert np.all(decoder.read() == range(6, 12))

    def test_seek_to_end(self):
        decoder = FakeAudioDecoder([range(6)])
        decoder.channels = 2
        decoder.samplerate = 3
        decoder.seek(1)
        assert decoder.position == 1
        assert decoder.is_eos()
        assert np.all(decoder.read() == 0)
