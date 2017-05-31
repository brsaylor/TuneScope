// This file encapsulates all the GStreamer-aware code for the AudioDecoder class.

#include <stdio.h>
#include <gst/gst.h>
#include <gst/audio/audio.h>
#include <gst/app/gstappsink.h>
#include <glib.h>

#define BUFFER_INITIAL_CAPACITY 64

gboolean gstreamer_initialized = FALSE;
gboolean glib_main_loop_started = FALSE;
GMainLoop *glib_main_loop = NULL;


// A buffer containing audio samples in 32-bit float format
typedef struct {
    size_t capacity;  // The number of samples the buffer can hold
    size_t size;      // The number of samples the buffer currently holds
    float *samples;   // The sample data
} AudioDecoderBuffer;


// A handle for a decoding pipeline for an individual file.
// Each instance of AudioDecoder has one of these.
typedef struct {
    GstElement *pipeline, *source, *decoder, *converter, *appsink;
    AudioDecoderBuffer buffer;
} AudioDecoderHandle;


// Links the decoder to the converter when the audio source pad appears on the decoder
static void on_pad_added(GstElement *element, GstPad *pad, gpointer data)
{
    GstElement *converter = (GstElement *) data;

    // Only link once
    GstPad *sinkpad = gst_element_get_static_pad(converter, "sink");
    if (GST_PAD_IS_LINKED (sinkpad)) {
        g_object_unref (sinkpad);
        return;
    }

    // Only link if audio
    GstCaps *caps = gst_pad_query_caps(pad, NULL);
    GstStructure *str = gst_caps_get_structure (caps, 0);
    if (!g_strrstr(gst_structure_get_name(str), "audio")) {
        gst_caps_unref(caps);
        gst_object_unref(sinkpad);
        return;
    }
    gst_caps_unref(caps);

    gst_pad_link(pad, sinkpad);
    gst_object_unref(sinkpad);
}


// Create a new decoding pipeline for the given file
// and return a handle to it
AudioDecoderHandle *audiodecoder_gst_new(char *filename)
{
    if (!gstreamer_initialized) {
        gst_init(NULL, NULL);
        glib_main_loop = g_main_loop_new (NULL, FALSE);
        gstreamer_initialized = TRUE;
    }

    AudioDecoderHandle *handle = (AudioDecoderHandle *) g_malloc0(sizeof(AudioDecoderHandle));

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
    gst_app_sink_set_caps(handle->appsink, caps);
    gst_app_sink_set_max_buffers(handle->appsink, 1);

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
    g_signal_connect(handle->decoder, "pad-added", G_CALLBACK(on_pad_added), handle->converter);

    // Start the pipeline
    gst_pipeline_use_clock(handle->pipeline, NULL);  // Make pipeline run as fast as possible
    gst_element_set_state(handle->pipeline, GST_STATE_PLAYING);

    // TODO
    //if (!glib_main_loop_started) {
    //    g_printerr("starting main loop \n");
    //    g_main_loop_run(glib_main_loop);
    //    glib_main_loop_started = TRUE;
    //    g_printerr("started main loop \n");
    //}

    return handle;
}


// Read a block of audio samples from the file as 32-bit floats.
// Return NULL if no more samples can be read.
// The number of samples returned cannot be controlled and may vary (a GStreamer limitation).
// Treat the returned buffer as read-only.
AudioDecoderBuffer *audiodecoder_gst_read(AudioDecoderHandle *handle)
{
    GstSample *sample = gst_app_sink_pull_sample(handle->appsink);
    if (sample == NULL)
        return NULL;

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


// Return 1 if no more samples can be read because end of stream has been reached,
// otherwise 0
int audiodecoder_gst_is_eos(AudioDecoderHandle *handle)
{
    return (int) gst_app_sink_is_eos(handle->appsink);
}


// Destroy the pipeline and free all associated resources
void audiodecoder_gst_delete(AudioDecoderHandle *handle)
{
    gst_element_set_state(handle->pipeline, GST_STATE_NULL);
    g_object_unref(handle->pipeline);
    g_free(handle->buffer.samples);
    g_free(handle);
}
