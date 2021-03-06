import numpy as np
cimport numpy as np
from numpy cimport ndarray, float32_t
from libc.stdlib cimport malloc, free

from . cimport rubberband as rb


MIN_SPEED = 0.005

# Rubber Band I/O buffers have a fixed size;
# exceeding buffer capacity will simply result in gaps in audio.
# RB functions refer to sample frames rather than samples;
# a sample frame is simply a set of simultaneous samples for each channel.
DEF RB_INPUT_BUFFER_SIZE_IN_FRAMES = 32768
DEF RB_OUTPUT_BUFFER_SIZE_IN_FRAMES = 32768

# This is what rubberband_available() returns
# after the input block marked "final" has been fully processed and retrieved.
DEF FINAL_BLOCK_RETRIEVED = -1


cdef class TimeStretcher:
    """
    Processes audio data from the given source,
    allowing independent control of playback rate and pitch.
    Audio data is consumed from the source
    and produced via read() at independent rates.
    """

    cdef readonly int channels
    cdef readonly int samplerate

    cdef object _audio_source
    cdef bint _audio_source_is_empty

    cdef double _speed
    cdef bint _speed_changed
    cdef double _pitch
    cdef bint _pitch_changed

    # Position in the input stream that will appear in the output the next time
    # read() is called, accounting for RB's buffering
    cdef double _position

    cdef rb.RubberBandState _rb_state

    # Rubber Band non-interleaved input and output buffers
    # The ndarrays are 2-dimensional (channels x frames).
    # The channel pointer arrays point to the start of each row,
    # and they're what we pass to the Rubber Band library functions.
    cdef ndarray _rb_input_buffer
    cdef float **_rb_input_buffer_channel_pointers
    cdef ndarray _rb_output_buffer
    cdef float **_rb_output_buffer_channel_pointers

    cdef bint _final_input_block_submitted
    cdef object _eos_callback

    def __cinit__(self, object audio_source, debug_level=0):
        """ `debug_level` controls verbosity of RubberBand debugging output,
        ranging from "0 (errors only) to 3 (very verbose, with audible ticks in
        the output at phase reset points)" (RB API docs) """
        self.channels = audio_source.channels
        self.samplerate = audio_source.samplerate

        self._audio_source = audio_source
        self._audio_source_is_empty = self._audio_source.is_eos()
        self._speed = 1.0
        self._speed_changed = False
        self._pitch = 0.0
        self._pitch_changed = False

        self._rb_input_buffer = np.zeros((self.channels, RB_INPUT_BUFFER_SIZE_IN_FRAMES), dtype=np.float32)
        self._rb_output_buffer = np.zeros((self.channels, RB_OUTPUT_BUFFER_SIZE_IN_FRAMES), dtype=np.float32)
        self._rb_input_buffer_channel_pointers = <float **> malloc(self.channels * sizeof(float *))
        self._rb_output_buffer_channel_pointers = <float **> malloc(self.channels * sizeof(float *))
        self._set_rb_buffer_channel_pointers()

        cdef rb.RubberBandOptions rb_options = (
            rb.RubberBandOptionProcessRealTime |
            rb.RubberBandOptionThreadingNever |
            rb.RubberBandOptionChannelsTogether)

        self._rb_state = rb.rubberband_new(
            audio_source.samplerate, audio_source.channels, rb_options, 1.0, 1.0)
        rb.rubberband_set_debug_level(self._rb_state, debug_level)

        self._position = audio_source.position
        self._final_input_block_submitted = False
        self._eos_callback = None

    cdef void _set_rb_buffer_channel_pointers(self):
        cdef float [:, :] rb_input_buffer_view = self._rb_input_buffer
        cdef float [:, :] rb_output_buffer_view = self._rb_output_buffer
        cdef int channel
        for channel in range(self.channels):
            self._rb_input_buffer_channel_pointers[channel] = &rb_input_buffer_view[channel, 0]
            self._rb_output_buffer_channel_pointers[channel] = &rb_output_buffer_view[channel, 0]

    cpdef ndarray read(self, size_t sample_count):
        """ Read a block of `sample_count` samples from the time stretcher,
        returning zeros beyond the end of the stream. """

        cdef unsigned int frame_count = sample_count / self.channels
        self._update_rb_parameters()
        while (rb.rubberband_available(self._rb_state) < frame_count
               and not self._final_input_block_submitted):
            self._process_more_input()
        cdef ndarray output_block = self._retrieve_rb_output(sample_count)
        if self.is_eos() and self._eos_callback is not None:
            self._eos_callback()

        self._update_position(sample_count)

        return output_block

    cdef void _update_rb_parameters(self):
        # Update the Rubber Band instance with the current speed and pitch parameters.
        # This must be done in the same thread as rubberband_process().
        # TODO: Interpolate parameter changes. Depends on how many samples RB requires

        if self._speed_changed:
            self._speed_changed = False
            rb.rubberband_set_time_ratio(self._rb_state, 1.0 / self._speed)
        if self._pitch_changed:
            self._pitch_changed = False
            rb.rubberband_set_pitch_scale(self._rb_state, 2 ** (self._pitch / 12))

    cdef void _process_more_input(self):
        # Transfer a block of input from the audio source
        # to the Rubber Band instance for processing.
        # The size of the block is dictated by the Rubber Band instance.

        cdef unsigned int input_frames_required  = rb.rubberband_get_samples_required(self._rb_state)
        cdef unsigned int input_samples_required = input_frames_required * self.channels
        cdef ndarray[float32_t] input_block = self._audio_source.read(input_samples_required)
        cdef bint is_final_input_block = self._audio_source.is_eos()
        cdef float [:, :] rb_input_buffer_view = self._rb_input_buffer

        # De-interleave input block into RB input buffer
        cdef int i, c
        for i in range(min(input_frames_required, RB_INPUT_BUFFER_SIZE_IN_FRAMES)):
            for c in range(self.channels):
                rb_input_buffer_view[c, i] = input_block[i * self.channels + c]

        rb.rubberband_process(self._rb_state,
                              <const float *const *> self._rb_input_buffer_channel_pointers,
                              input_frames_required,
                              is_final_input_block)

        if is_final_input_block:
            self._final_input_block_submitted = True

    cdef ndarray _retrieve_rb_output(self, size_t sample_count):
        # Retrieve a block of processed output samples from the Rubber Band instance.
        # The returned array is zero-padded if necessary.

        cdef unsigned int frame_count = sample_count / self.channels
        cdef size_t frames_retrieved = rb.rubberband_retrieve(
                self._rb_state,
                self._rb_output_buffer_channel_pointers,
                min(frame_count, RB_OUTPUT_BUFFER_SIZE_IN_FRAMES))
        cdef ndarray[float32_t] output_block = np.zeros(sample_count, dtype=np.float32)
        cdef float [:, :] rb_output_buffer_view = self._rb_output_buffer

        # Interleave RB output buffer into output block
        cdef int i, c
        for i in range(min(frames_retrieved, RB_OUTPUT_BUFFER_SIZE_IN_FRAMES)):
            for c in range(self.channels):
                output_block[i * self.channels + c] = rb_output_buffer_view[c, i]

        return output_block

    cdef void _update_position(self, size_t sample_count):
        # Update self._position after some output has been retrieved from the RB
        # stretcher.  `sample_count` is the number of samples read from the
        # stretcher since the previous call to _update_position().

        cdef double source_position = self._audio_source.position
        cdef double buffered_input_duration
        cdef double available_output_duration
        cdef double new_position

        if self._final_input_block_submitted:
            # Once the final input block has been passed to
            # rubberband_process(), RB's buffering behavior changes. For the
            # last few output blocks, simply increment _position by the expected
            # change.
            new_position = (self._position
                            + <double> sample_count
                            / self.channels
                            / self.samplerate
                            * self._speed)
        else:
            # Normal case: base on source position, but account for input and output buffers

            buffered_input_duration = (
                <double> rb.rubberband_get_buffered_input_duration(self._rb_state)
                / self.samplerate
                * rb.rubberband_get_pitch_scale(self._rb_state))
            # Input buffer contains audio resampled to the new pitch, so we need
            # to multiply by the pitch scale to get its original duration.

            available_output_duration = (<double> rb.rubberband_available(self._rb_state)
                                         / self.samplerate
                                         * self._speed)

            new_position = (source_position
                            - buffered_input_duration
                            - available_output_duration)

        self._position = min(new_position, source_position)


    cpdef bint seek(self, double position):
        """ Seek to the given position in seconds.
        Return True on success, False on failure. """
        if not self._audio_source.seek(position):
            return False
        self.reset()
        return True


    cpdef ndarray read_remaining_output(self):
        """ Read and return any remaining output samples that have been
        processed but not yet retrieved. """

        cdef int frames_available = rb.rubberband_available(self._rb_state)
        if frames_available == FINAL_BLOCK_RETRIEVED:
            return np.empty(0, dtype=np.float32)
        cdef ndarray output_block = self._retrieve_rb_output(frames_available)
        return output_block

    cpdef bint is_eos(self):
        return (rb.rubberband_available(self._rb_state) == FINAL_BLOCK_RETRIEVED
                or self._audio_source_is_empty)

    cpdef void reset(self):
        """ Enable further processing after end-of-stream
        (e.g. after a seek backward from EOS) """
        rb.rubberband_reset(self._rb_state)
        self._position = self._audio_source.position
        self._final_input_block_submitted = False

    @property
    def position(self):
        """ Position in the input stream that will appear in the output the next
        time read() is called, accounting for the effects of time-stretching """
        return self._position

    @property
    def speed(self):
        """ Ratio of playback speed to original speed """
        return self._speed

    @speed.setter
    def speed(self, double speed):
        self._speed = max(speed, MIN_SPEED)
        self._speed_changed = True

    @property
    def pitch(self):
        """ Pitch offset in semitones """
        return self._pitch

    @pitch.setter
    def pitch(self, double pitch):
        self._pitch = pitch
        self._pitch_changed = True

    @property
    def eos_callback(self):
        """ Function to be called when end of stream has been processed """
        return self._eos_callback

    @eos_callback.setter
    def eos_callback(self, callback):
        self._eos_callback = callback

    def get_debug_info(self):
        return {
            'frames_available': rb.rubberband_available(self._rb_state),
            'buffered_input_duration': rb.rubberband_get_buffered_input_duration(self._rb_state),
            'final_input_block_submitted': self._final_input_block_submitted,
        }

    def __dealloc__(self):
        # FIXME: Need to ensure that it's not deleted while read() is running
        rb.rubberband_delete(self._rb_state)
        free(self._rb_input_buffer_channel_pointers)
        free(self._rb_output_buffer_channel_pointers)
