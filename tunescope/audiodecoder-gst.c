// This file encapsulates all the GStreamer-aware code for the AudioDecoder class.

#include <stdio.h>
#include <gst/gst.h>
#include <gst/audio/audio.h>
#include <gst/app/gstappsink.h>
#include <glib.h>

#define BUFFER_INITIAL_CAPACITY 64


// A buffer containing audio samples in 32-bit float format
typedef struct {
    size_t capacity;  // The number of samples the buffer can hold
    size_t size;      // The number of samples the buffer currently holds
    float *samples;   // The sample data
} AudioDecoderBuffer;


// Audio file metadata
typedef struct {
    int channels;
    int samplerate;
} AudioDecoderMetadata;


// A handle for a decoding pipeline for an individual file.
// Each instance of AudioDecoder has an opaque pointer to one of these.
typedef struct {
    GstElement *pipeline, *source, *decoder, *converter, *appsink;
    AudioDecoderBuffer buffer;
    AudioDecoderMetadata metadata;
} AudioDecoderHandle;


// Links the decoder to the converter when the audio source pad appears on the decoder
static void on_pad_added(GstElement *element, GstPad *pad, gpointer data)
{
    AudioDecoderHandle *handle = (AudioDecoderHandle *) data;

    // Only link once
    GstPad *sinkpad = gst_element_get_static_pad(handle->converter, "sink");
    if (GST_PAD_IS_LINKED (sinkpad)) {
        g_object_unref (sinkpad);
        return;
    }

    // Only link if audio
    GstCaps *caps = gst_pad_get_current_caps(pad);
    GstStructure *str = gst_caps_get_structure (caps, 0);
    if (!g_strrstr(gst_structure_get_name(str), "audio")) {
        gst_caps_unref(caps);
        gst_object_unref(sinkpad);
        return;
    }

    // Get audio info
    GstAudioInfo audio_info;
    if (!gst_audio_info_from_caps(&audio_info, caps)) {
        g_error("Could not get audio info from file\n");
        gst_caps_unref(caps);
        gst_object_unref(sinkpad);
        return;
    }
    handle->metadata.channels = GST_AUDIO_INFO_CHANNELS(&audio_info);
    handle->metadata.samplerate = GST_AUDIO_INFO_RATE(&audio_info);

    gst_caps_unref(caps);

    gst_pad_link(pad, sinkpad);
    gst_object_unref(sinkpad);
}


// Create a new decoding pipeline for the given file
// and return a handle to it
AudioDecoderHandle *audiodecoder_gst_new(char *filename)
{
    AudioDecoderHandle *handle = (AudioDecoderHandle *) g_malloc0(sizeof(AudioDecoderHandle));
    handle->metadata.channels = 0;
    handle->metadata.samplerate = 0;

    // Initialize output buffer
    handle->buffer.samples = g_malloc0(BUFFER_INITIAL_CAPACITY * sizeof(float));
    handle->buffer.capacity = BUFFER_INITIAL_CAPACITY;
    handle->buffer.size = 0;

    // Create elements
    handle->pipeline = gst_pipeline_new("decoder-pipeline");
    handle->source = gst_element_factory_make("filesrc", "source");
    handle->decoder = gst_element_factory_make("decodebin", "decoder");
    handle->converter = gst_element_factory_make("audioconvert", "converter");
    handle->appsink = gst_element_factory_make("appsink", "appsink");
    if (!handle->pipeline || !handle->source || !handle->decoder || !handle->converter || !handle->appsink) {
        g_printerr ("One element could not be created. Exiting.\n");
        return NULL;
    }

    // Set up the appsink to accept only 32-bit float audio
    // with minimal buffering
    GstCaps *caps = gst_caps_new_simple(
                "audio/x-raw",
                "format", G_TYPE_STRING, GST_AUDIO_NE(F32),
                "channels", GST_TYPE_INT_RANGE, 1, 16,
                "rate", GST_TYPE_INT_RANGE, 8000, 96000,
                NULL);
    gst_app_sink_set_caps(GST_APP_SINK(handle->appsink), caps);
    gst_app_sink_set_max_buffers(GST_APP_SINK(handle->appsink), 1);

    // Set file source
    g_object_set(G_OBJECT(handle->source), "location", filename, NULL);

    // Add message handler
    // FIXME: Need to implement bus_call
    // GstBus *bus = gst_pipeline_get_bus(GST_PIPELINE(handle->pipeline));
    // int bus_watch_id = gst_bus_add_watch(bus, bus_call, glib_main_loop);
    // gst_object_unref(bus);

    // Add elements to pipeline
    gst_bin_add_many(GST_BIN(handle->pipeline),
            handle->source,
            handle->decoder,
            handle->converter,
            handle->appsink,
            NULL);

    // Link elements
    gst_element_link(handle->source, handle->decoder);
    gst_element_link(handle->converter, handle->appsink);
    g_signal_connect(handle->decoder, "pad-added", G_CALLBACK(on_pad_added), handle);

    // Start the pipeline
    gst_pipeline_use_clock(GST_PIPELINE(handle->pipeline), NULL);  // Make pipeline run as fast as possible
    gst_element_set_state(handle->pipeline, GST_STATE_PLAYING);

    // Ensure audio metadata is ready (i.e. on_pad_added() gets called)
    gst_app_sink_pull_preroll(GST_APP_SINK(handle->appsink));

    return handle;
}


// Read a block of audio samples from the file as 32-bit floats.
// The number of samples returned cannot be controlled and may vary (a GStreamer limitation).
// If called beyond the end of the stream, a zero-filled buffer is returned.
// Treat the returned buffer as read-only.
AudioDecoderBuffer *audiodecoder_gst_read(AudioDecoderHandle *handle)
{
    GstSample *sample = gst_app_sink_pull_sample(GST_APP_SINK(handle->appsink));
    if (sample == NULL) {
        // No more audio to be decoded: send an empty buffer downstream
        handle->buffer.size = handle->buffer.capacity;
        memset(handle->buffer.samples, 0, handle->buffer.size * sizeof(float));
        return &(handle->buffer);
    }

    GstBuffer* gst_buffer = gst_sample_get_buffer(sample);
	GstMapInfo map;
    gst_buffer_map(gst_buffer, &map, GST_MAP_READ);

    int num_samples = map.size / sizeof(float);

    // Resize output buffer if needed
    if (handle->buffer.capacity < num_samples) {
        handle->buffer.samples = g_realloc(handle->buffer.samples, map.size);
        handle->buffer.capacity = num_samples;
    }

    // Copy samples to output buffer
    memmove(handle->buffer.samples, map.data, map.size);
    handle->buffer.size = num_samples;

    gst_buffer_unmap(gst_buffer, &map);
    gst_sample_unref(sample);

    return &(handle->buffer);
}


AudioDecoderMetadata *audiodecoder_gst_get_metadata(AudioDecoderHandle *handle)
{
    return &(handle->metadata);
}


// Seek to the given position in seconds.
// Return 1 on success, 0 on failure.
int audiodecoder_gst_seek(AudioDecoderHandle *handle, double position)
{
    int success = gst_element_seek_simple(
            handle->pipeline,
            GST_FORMAT_TIME,
            GST_SEEK_FLAG_FLUSH | GST_SEEK_FLAG_ACCURATE,
            //GST_SEEK_FLAG_FLUSH | GST_SEEK_FLAG_KEY_UNIT,
            position * GST_SECOND);
    if (!success) {
        g_printerr("gst_element_seek_simple() failed\n");
        return 0;
    }

    // Wait until the seek has completed
    GstState state;
    GstStateChangeReturn state_change_return = gst_element_get_state(
            handle->pipeline,
            &state,
            NULL,
            GST_SECOND);
    switch (state_change_return) {
        case GST_STATE_CHANGE_SUCCESS:
            success = 1;
            break;
        case GST_STATE_CHANGE_ASYNC:
            g_printerr("audiodecoder_gst_seek: GST_STATE_CHANGE_ASYNC\n");
            success = 0;
            break;
        case GST_STATE_CHANGE_FAILURE:
            g_printerr("audiodecoder_gst_seek: GST_STATE_CHANGE_FAILURE\n");
            success = 0;
            break;
        case GST_STATE_CHANGE_NO_PREROLL:
            g_printerr("audiodecoder_gst_seek: GST_STATE_CHANGE_NO_PREROLL\n");
            success = 0;
            break;
        default:
            g_printerr("audiodecoder_gst_seek: unknown GstStateChangeReturn\n");
            success = 0;
            break;
    }

    return success;
}


double audiodecoder_gst_get_position(AudioDecoderHandle *handle)
{
    gint64 position_nanoseconds;
    if (!gst_element_query_position(handle->pipeline, GST_FORMAT_TIME, &position_nanoseconds)) {
        g_printerr("Could not query current position.\n");
        return 0;
    }
    return ((double) position_nanoseconds) / GST_SECOND;
}


// Return 1 if no more samples can be read because end of stream has been reached,
// otherwise 0
int audiodecoder_gst_is_eos(AudioDecoderHandle *handle)
{
    return (int) gst_app_sink_is_eos(GST_APP_SINK(handle->appsink));
}


// Destroy the pipeline and free all associated resources
void audiodecoder_gst_delete(AudioDecoderHandle *handle)
{
    gst_element_set_state(handle->pipeline, GST_STATE_NULL);
    g_object_unref(handle->pipeline);
    g_free(handle->buffer.samples);
    g_free(handle);
}
