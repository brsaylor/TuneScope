import os
import threading

import pytest
import numpy as np

from tunescope import audiooutput
from tunescope.audiooutput import AudioOutput


os.environ['SDL_AUDIODRIVER'] = 'dummy'


@pytest.fixture()
def sdl_output_file(tmpdir):
    """ Tell SDL to use the 'disk' audio driver
    and return the path to the output file containing raw audio data. """

    # Setup
    filepath = str(tmpdir.join('sdlaudio.raw'))
    os.environ['SDL_AUDIODRIVER'] = 'disk'
    os.environ['SDL_DISKAUDIODELAY'] = '0'
    os.environ['SDL_DISKAUDIOFILE'] = filepath
    audiooutput.reinitialize()

    yield filepath

    # Teardown
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    del os.environ['SDL_DISKAUDIODELAY']
    del os.environ['SDL_DISKAUDIOFILE']
    audiooutput.reinitialize()


class FakeAudioSource(object):
    """
    Audio source test double to use as input to AudioOutput.

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
        samples_available = len(self._samples) - self._read_position
        if samples_available <= 0:
            raise EOFError()
        elif sample_count > samples_available:
            sample_count = samples_available

        start = self._read_position
        end = start + sample_count
        self._read_position = end

        if self.is_eos():
            self._eos_event.set()

        self.read_called = True
        self._read_event.set()

        return self._samples[start:end]

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
    assert np.all(fake_source.read(2) == np.array([4]))
    assert fake_source.is_eos()
    with pytest.raises(EOFError):
        fake_source.read(1)

    # These should return immediately
    fake_source.wait_for_eos_with_timeout(0)
    fake_source.wait_for_read_with_timeout(0)


def test_source_read_called():
    fake_source = FakeAudioSource(2, 44100, np.arange(5))
    output = AudioOutput(fake_source)
    output.play()
    fake_source.wait_for_read_with_timeout(1)
    output.close()
    assert fake_source.read_called


def test_close_while_playing():
    fake_source = FakeAudioSource(2, 44100, np.arange(5))
    output = AudioOutput(fake_source)
    output.play()
    output.close()


def test_samples_written(sdl_output_file):

    # Fake audio source providing one second of 44.1 kHz stereo noise
    samples = np.random.random_sample(88200).astype(np.float32) * 2 - 1
    fake_source = FakeAudioSource(2, 44100, samples)

    output = AudioOutput(fake_source)
    output.play()
    fake_source.wait_for_eos_with_timeout(2)
    output.close()

    samples_written = np.fromfile(sdl_output_file, dtype=np.float32)

    # SDL writes some leading and trailing zeros; trim them off
    samples_written_trimmed = np.trim_zeros(samples_written)

    assert np.all(samples_written_trimmed == samples)


def test_two_simultaneous_outputs():
    output1 = AudioOutput(FakeAudioSource(2, 44100, np.arange(5)))
    output2 = AudioOutput(FakeAudioSource(2, 44100, np.arange(5)))
    output1.play()
    output2.play()
    output1.close()
    output2.close()
