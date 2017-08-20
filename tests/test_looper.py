import pytest
import numpy as np

from tunescope.looper import Looper
from test_doubles import FakeAudioSource


CHANNELS = 2
SAMPLERATE = 10


@pytest.fixture(scope='session')
def input_samples():
    """ Create one second of samples based on CHANNELS and SAMPLERATE """
    return np.arange(CHANNELS * SAMPLERATE, dtype=np.float32)


@pytest.fixture()
def looper(input_samples):
    return Looper(FakeAudioSource(CHANNELS, SAMPLERATE, input_samples))


def test_channels_samplerate(looper):
    assert looper.channels == CHANNELS
    assert looper.samplerate == SAMPLERATE


def test_read_whole_stream_without_looping(input_samples, looper):
    assert np.all(looper.read(len(input_samples)) == input_samples)


def test_active(looper):
    assert not looper.active
    looper.activate(0, 1)
    assert looper.active


def test_negative_start_pos(looper):
    with pytest.raises(ValueError):
        looper.activate(-1, 0)


def test_invalid_end_pos(looper):
    with pytest.raises(ValueError):
        looper.activate(1, 0.5)


def test_is_eos(input_samples, looper):
    looper.read(len(input_samples))
    assert looper.is_eos()
    looper.activate(0, 1)
    assert not looper.is_eos()
    looper.deactivate()
    assert looper.is_eos()


def test_read_to_loop_end(input_samples, looper):
    looper.activate(0, 1)
    assert np.all(looper.read(len(input_samples)) == input_samples)


def test_read_past_loop_end(input_samples, looper):
    looper.activate(0, 1)
    expected_output = np.concatenate([input_samples,
                                      input_samples[:len(input_samples) / 2]])
    assert np.all(looper.read(len(input_samples) * 1.5) == expected_output)


def test_read_starting_after_loop_end(input_samples, looper):
    looper.read(len(input_samples) * .75)
    looper.activate(0, 0.5)
    assert np.all(looper.read(len(input_samples) / 2)
                  == input_samples[:len(input_samples) / 2])
