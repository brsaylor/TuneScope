import numpy as np
cimport numpy as np

from tunescope.audioutil cimport pad_block


cdef extern from "Python.h":
    void PyEval_InitThreads()


cdef extern from "audiooutput-sdl.c":

    ctypedef struct AudioOutputHandle:
        pass

    AudioOutputHandle *audiooutput_sdl_new(int channels, int samplerate)
    void audiooutput_sdl_set_write_samples_callback(
        AudioOutputHandle *handle,
        void *audio_output_instance,
        void (*callback) (void *instance, float *block, int sample_count))
    void audiooutput_sdl_play(AudioOutputHandle *handle)
    void audiooutput_sdl_pause(AudioOutputHandle *handle)
    void audiooutput_sdl_close(AudioOutputHandle *handle)
    void audiooutput_sdl_reinitialize()


cdef class AudioOutput:
    """
    Sends audio data from the given source to the audio device.

    `audio_source` is an object with properties `channels` and `samplerate`
    and methods `is_eos()` and `read(sample_count)`,
    which returns a NumPy float32 array of length `sample_count`.
    """

    cdef object _audio_source
    cdef AudioOutputHandle *_handle

    def __cinit__(self, object audio_source):

        # Initialize the GIL.
        # This is required because _write_samples_callback()
        # is called from a different C thread and requires the GIL.
        # http://docs.cython.org/en/latest/src/userguide/external_C_code.html#acquiring-and-releasing-the-gil
        PyEval_InitThreads()

        self._audio_source = audio_source
        self._handle = audiooutput_sdl_new(
            self._audio_source.channels,
            self._audio_source.samplerate)
        audiooutput_sdl_set_write_samples_callback(
            self._handle,
            <void *> self,
            <void (*) (void *, float *, int)> AudioOutput._write_samples_callback)

    cpdef play(self):
        audiooutput_sdl_play(self._handle)

    cpdef pause(self):
        audiooutput_sdl_pause(self._handle)
    
    cpdef close(self):
        """ Close the audio device.

        This must be called before the object is deleted or garbage collected;
        otherwise, the program will likely crash.
        Do not call any other methods after calling this. """

        audiooutput_sdl_close(self._handle)

    cdef void _write_samples_callback(self, float *block, int sample_count) with gil:
        # Called by the audio back-end to fill a buffer of samples.
        #
        # Calling Python code from a C thread callback requires acquiring the GIL
        # (otherwise, it crashes).

        cdef np.ndarray[np.float32_t] samples

        if self._audio_source.is_eos():
            samples = np.zeros(sample_count, dtype=np.float32)
        else:
            samples = self._audio_source.read(sample_count)
            if len(samples) < sample_count:
                samples = pad_block(samples, sample_count)

        cdef int i
        for i in range(sample_count):
            block[i] = samples[i]


def reinitialize():
    """ Reinitialize the SDL audio system.
    This is necessary when switching drivers. """
    audiooutput_sdl_reinitialize()
