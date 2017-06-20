"""
Test doubles for use in unit tests, along with tests for them
"""

import threading

import pytest
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
    provides extra methods and attribute for testing:
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
        end = start + sample_count
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


def test_fake_audio_source():
    fake_source = FakeAudioSource(2, 44100, np.arange(5))
    assert np.all(fake_source.read(2) == np.array([0, 1]))
    assert np.all(fake_source.read(2) == np.array([2, 3]))
    assert np.all(fake_source.read(2) == np.array([4, 0]))
    assert fake_source.is_eos()
    assert np.all(fake_source.read(2) == np.array([0, 0]))

    # These should return immediately
    fake_source.wait_for_eos_with_timeout(0)
    fake_source.wait_for_read_with_timeout(0)


class FakeAudioDecoder(object):
    """ Test double for AudioDecoder """

    def __init__(self, blocks):
        """ `blocks` is a list of lists representing the blocks of samples
        returned by each call to read() """
        self._blocks = (np.array(values, dtype=np.float32) for values in blocks)
        self._blocks_remaining = len(blocks)

    def read(self):
        if self._blocks_remaining <= 0:
            return np.zeros(4, dtype=np.float32)
        self._blocks_remaining -= 1
        return next(self._blocks)

    def is_eos(self):
        return self._blocks_remaining <= 0


class TestFakeAudioDecoder(object):

    def test_read_empty_stream(self):
        fake_decoder = FakeAudioDecoder([])
        block = fake_decoder.read()
        assert len(block) > 0
        assert np.all(block == 0)
        assert fake_decoder.is_eos()

    def test_read_entire_stream(self):
        fake_decoder = FakeAudioDecoder([[1, 2], [3, 4]])
        data_read = []
        while not fake_decoder.is_eos():
            data_read += list(fake_decoder.read())
        assert data_read == [1, 2, 3, 4]
