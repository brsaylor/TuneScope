import os

import pytest
import numpy as np

from tunescope.audio import audiooutput
from tunescope.audio import AudioOutput
from test_doubles import FakeAudioSource

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
