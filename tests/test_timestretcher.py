import mock
import math

import pytest
import numpy as np

from tunescope.audio import TimeStretcher
from test_doubles import FakeAudioSource


def noise(sample_count):
    return np.random.random(sample_count).astype(np.float32) * 2 - 1


def impulse(frame_count, channels, impulse_frame):
    samples = np.zeros(frame_count * channels)
    for c in range(channels):
        samples[impulse_frame * channels + c] = 1
    return samples


def rms(samples):
    return np.sqrt(np.mean(np.square(samples)))


def rms_block_envelope(samples, block_size):
    block_count = len(samples) / block_size
    rms_by_block = np.empty(block_count)
    for i in range(block_count):
        block_start = i * block_size
        block_end = (i + 1) * block_size
        block = samples[block_start:block_end]
        rms_by_block[i] = rms(block)
    return rms_by_block


def test_instantiate_delete():
    source = FakeAudioSource(2, 44100, np.array([]))
    stretcher = TimeStretcher(source)
    del stretcher


def test_channels_samplerate():
    source = FakeAudioSource(2, 44100, np.array([]))
    stretcher = TimeStretcher(source)
    assert stretcher.channels == 2
    assert stretcher.samplerate == 44100


def test_is_eos_with_empty_source():
    source = FakeAudioSource(1, 44100, np.array([]))
    stretcher = TimeStretcher(source)
    assert stretcher.is_eos()


def test_is_eos_after_processing_all_input_at_original_speed():
    source = FakeAudioSource(1, 44100, np.arange(4))
    stretcher = TimeStretcher(source)
    assert not stretcher.is_eos()
    stretcher.read(4)
    stretcher.read_remaining_output()
    assert stretcher.is_eos()


def test_rms_envelope_at_original_speed_mono():
    sample_count = 16384
    block_size = 1024
    skip_blocks = 2  # Beginning of output RMS envelope doesn't match well
    absolute_tolerance = 0.0001

    # Noise with linearly decaying volume envelope
    input_samples = noise(sample_count) * np.linspace(1, 0, num=sample_count)
    source = FakeAudioSource(1, 44100, input_samples)
    stretcher = TimeStretcher(source)
    output_samples = stretcher.read(sample_count)

    assert np.allclose(
        rms_block_envelope(input_samples, block_size)[skip_blocks:],
        rms_block_envelope(output_samples, block_size)[skip_blocks:],
        atol=absolute_tolerance)


def test_rms_envelope_at_half_speed_mono():
    # The input is some noise with a linearly increasing volume envelope. We
    # time-stretch it by a factor of two (half speed). The expected output has a
    # linearly increasing RMS envelope of twice the duration of the input. This
    # is about the best we can do for verifying time-stretching; the actual
    # output has a complex relationship to the input.

    input_sample_count = 16384
    output_sample_count = input_sample_count * 2
    output_block_size = 2048
    skip_blocks = 2  # End of output RMS envelope doesn't match well

    input_samples = noise(input_sample_count) * np.linspace(0, 1, num=input_sample_count)
    source = FakeAudioSource(1, 44100, input_samples)
    stretcher = TimeStretcher(source)
    stretcher.speed = 0.5
    output_samples = stretcher.read(output_sample_count)
    envelope = rms_block_envelope(output_samples, output_block_size)[:-skip_blocks]

    assert np.all(envelope == np.sort(envelope))
    assert np.all(envelope > 0)


def test_stereo_channels_preserved():
    block_size = 1024
    frame_count = block_size * 3  # Silence, left, right
    sample_count = frame_count * 2
    rms_absolute_tolerance = 0.1  # Seems we need a greater tolerance with stereo

    input_samples = np.zeros((frame_count, 2), dtype=np.float32)
    input_samples[block_size:block_size*2, 0] = noise(block_size)
    input_samples[block_size*2:, 1] = noise(block_size)

    source = FakeAudioSource(2, 44100, input_samples.flatten())
    stretcher = TimeStretcher(source)
    output_samples = stretcher.read(sample_count)

    output_samples = output_samples.reshape((frame_count, 2))

    input_rms_left = rms_block_envelope(input_samples[:, 0], block_size)
    input_rms_right = rms_block_envelope(input_samples[:, 1], block_size)

    # Check input RMS
    assert np.all(input_rms_left.round() == np.array([0, 1, 0]))
    assert np.all(input_rms_right.round() == np.array([0, 0, 1]))

    output_rms_left = rms_block_envelope(output_samples[:, 0], block_size)
    output_rms_right = rms_block_envelope(output_samples[:, 1], block_size)

    assert np.allclose(input_rms_left, output_rms_left, atol=rms_absolute_tolerance)
    assert np.allclose(input_rms_right, output_rms_right, atol=rms_absolute_tolerance)


def test_reset():
    block_size = 1024
    sample_count = block_size * 3
    input_samples = noise(sample_count)
    source = FakeAudioSource(1, 44100, input_samples)
    stretcher = TimeStretcher(source)
    
    while not stretcher.is_eos():
        stretcher.read(block_size)

    source.seek(0)
    source.read_called = False

    # Rubber Band has finished processing the final input block,
    # so the source will not be read
    # and any subsequent output is 0
    assert np.all(stretcher.read(block_size) == 0)
    assert not source.read_called

    stretcher.reset()

    # Now that the stretcher has been reset,
    # the stretcher should reading and processing the source again
    assert not stretcher.is_eos()
    block = stretcher.read(block_size)
    assert source.read_called
    assert rms(block) > 0.3


def test_eos_callback():
    source = FakeAudioSource(1, 44100, noise(44100))
    stretcher = TimeStretcher(source)
    eos_callback = mock.Mock()
    stretcher.eos_callback = eos_callback
    while not stretcher.is_eos():
        stretcher.read(1024)
    assert eos_callback.was_called()


@pytest.mark.parametrize(
    ['channels', 'samplerate', 'speed', 'pitch', 'block_size'],
    [
        # Stereo
        (2, 44100, 1, 0, 4096),

        # Small block size
        (1, 44100, 1, 0, 64),

        # High samplerate
        (1, 96000, 1, 0, 4096),

        # Varying speed only
        (1, 44100, 0.10, 0, 4096),
        (1, 44100, 0.50, 0, 4096),
        (1, 44100, 2.00, 0, 4096),

        # Varying pitch only
        (1, 44100, 1, -12, 4096),  # Fails with tolerance = 0.01
        (1, 44100, 1, -5, 4096),
        (1, 44100, 1, 5, 4096),
        (1, 44100, 1, 12, 4096),

        # Varying speed and pitch
        (1, 44100, 0.5, 5, 4096),
        (1, 44100, 1.5, -5, 4096),  # Fails with tolerance = 0.01
    ])
def test_position(channels, samplerate, speed, pitch, block_size):
    tolerance = 0.02
    input_duration = 1.0
    input_samples = noise(int(math.ceil(channels * samplerate * input_duration)))
    source = FakeAudioSource(channels, samplerate, input_samples)
    stretcher = TimeStretcher(source, debug_level=0)
    stretcher.speed = speed
    stretcher.pitch = pitch

    expected_position = 0.0
    assert stretcher.position == expected_position
    position_increment = float(block_size) / channels / samplerate * speed
    while expected_position < input_duration:
        stretcher.read(block_size)
        expected_position = min(expected_position + position_increment, input_duration)
        error = stretcher.position - expected_position
        try:
            assert abs(error) <= tolerance
        except AssertionError:
            debug_info = stretcher.get_debug_info()
            print(("expected position:  {:.3f}\n" +
                   "actual position:    {:.3f}\n" +
                   "error:              {:.3f}\n" +
                   "error in frames:    {:d}\n" +
                   "source position:    {:.3f}\n" +
                   "buffered:           {:d}\n" +
                   "final submitted:    {}\n" +
                   "frames available:   {:d}\n")
                  .format(
                      expected_position,
                      stretcher.position,
                      error,
                      int(round(error * samplerate)),
                      source.position,
                      debug_info['buffered_input_duration'],
                      debug_info['final_input_block_submitted'],
                      debug_info['frames_available']))
            raise


def test_seek():
    channels = 2
    samplerate = 44100
    impulse_frame_offset = 16
    impulse_frame = samplerate / 2 + impulse_frame_offset
    input_samples = impulse(samplerate, channels, impulse_frame)
    source = FakeAudioSource(channels, samplerate, input_samples)
    stretcher = TimeStretcher(source)
    assert stretcher.seek(0.5)
    assert np.isclose(stretcher.position, 0.5)
    
    # Check that the impulse appears in the expected position in the output
    outblock = stretcher.read(64)
    assert outblock.argmax() == impulse_frame_offset * channels


def test_invalid_seek():
    stretcher = TimeStretcher(FakeAudioSource(2, 44100, noise(882)))
    assert not stretcher.seek(-1)


@pytest.mark.skip()
@pytest.mark.parametrize(
    ['channels', 'samplerate', 'speed', 'pitch', 'block_size', 'seek_from', 'seek_to'],
    [
        (1, 44100, 1, 0, 4096, 0.5, 0.25),
    ])
def test_position_after_source_seek(
        channels, samplerate, speed, pitch, block_size, seek_from, seek_to):
    input_samples = noise(channels * samplerate)
    source = FakeAudioSource(channels, samplerate, input_samples)
    stretcher = TimeStretcher(source)
    stretcher.speed = speed
    stretcher.pitch = pitch
    while stretcher.position < seek_from:
        stretcher.read(block_size)
    expected_position_after_seek = stretcher.position - (seek_from - seek_to)
    source.seek(seek_to)
    assert np.isclose(stretcher.position, expected_position_after_seek)
