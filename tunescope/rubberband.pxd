cdef extern from '<rubberband/rubberband-c.h>':

    cdef enum RubberBandOption:

        RubberBandOptionProcessOffline       = 0x00000000
        RubberBandOptionProcessRealTime      = 0x00000001

        RubberBandOptionStretchElastic       = 0x00000000
        RubberBandOptionStretchPrecise       = 0x00000010
        
        RubberBandOptionTransientsCrisp      = 0x00000000
        RubberBandOptionTransientsMixed      = 0x00000100
        RubberBandOptionTransientsSmooth     = 0x00000200

        RubberBandOptionDetectorCompound     = 0x00000000
        RubberBandOptionDetectorPercussive   = 0x00000400
        RubberBandOptionDetectorSoft         = 0x00000800

        RubberBandOptionPhaseLaminar         = 0x00000000
        RubberBandOptionPhaseIndependent     = 0x00002000
        
        RubberBandOptionThreadingAuto        = 0x00000000
        RubberBandOptionThreadingNever       = 0x00010000
        RubberBandOptionThreadingAlways      = 0x00020000

        RubberBandOptionWindowStandard       = 0x00000000
        RubberBandOptionWindowShort          = 0x00100000
        RubberBandOptionWindowLong           = 0x00200000

        RubberBandOptionSmoothingOff         = 0x00000000
        RubberBandOptionSmoothingOn          = 0x00800000

        RubberBandOptionFormantShifted       = 0x00000000
        RubberBandOptionFormantPreserved     = 0x01000000

        RubberBandOptionPitchHighQuality     = 0x00000000
        RubberBandOptionPitchHighSpeed       = 0x02000000
        RubberBandOptionPitchHighConsistency = 0x04000000

        RubberBandOptionChannelsApart        = 0x00000000
        RubberBandOptionChannelsTogether     = 0x10000000

    ctypedef int RubberBandOptions

    cdef struct RubberBandState_:
        pass
    ctypedef RubberBandState_ *RubberBandState

    cdef extern RubberBandState rubberband_new(
            unsigned int sampleRate,
            unsigned int channels,
            RubberBandOptions options,
            double initialTimeRatio,
            double initialPitchScale)

    cdef extern void rubberband_delete(RubberBandState)

    cdef extern void rubberband_reset(RubberBandState)

    cdef extern void rubberband_set_time_ratio(RubberBandState, double ratio)
    cdef extern void rubberband_set_pitch_scale(RubberBandState, double scale)

    cdef extern double rubberband_get_time_ratio(const RubberBandState)
    cdef extern double rubberband_get_pitch_scale(const RubberBandState)

    cdef extern unsigned int rubberband_get_latency(const RubberBandState)

    cdef extern void rubberband_set_transients_option(RubberBandState, RubberBandOptions options)
    cdef extern void rubberband_set_detector_option(RubberBandState, RubberBandOptions options)
    cdef extern void rubberband_set_phase_option(RubberBandState, RubberBandOptions options)
    cdef extern void rubberband_set_formant_option(RubberBandState, RubberBandOptions options)
    cdef extern void rubberband_set_pitch_option(RubberBandState, RubberBandOptions options)

    cdef extern void rubberband_set_expected_input_duration(RubberBandState, unsigned int samples)

    cdef extern unsigned int rubberband_get_samples_required(const RubberBandState)

    cdef extern unsigned int rubberband_get_buffered_input_duration(const RubberBandState)

    cdef extern void rubberband_set_max_process_size(RubberBandState, unsigned int samples)
    cdef extern void rubberband_set_key_frame_map(RubberBandState, unsigned int keyframecount, unsigned int *from_, unsigned int *to)

    cdef extern void rubberband_study(RubberBandState, const float *const *input, unsigned int samples, int final)
    cdef extern void rubberband_process(RubberBandState, const float *const *input, unsigned int samples, int final)

    cdef extern int rubberband_available(const RubberBandState)
    cdef extern unsigned int rubberband_retrieve(const RubberBandState, float *const *output, unsigned int samples)

    cdef extern unsigned int rubberband_get_channel_count(const RubberBandState)

    cdef extern void rubberband_calculate_stretch(RubberBandState)

    cdef extern void rubberband_set_debug_level(RubberBandState, int level)
    cdef extern void rubberband_set_default_debug_level(int level)
