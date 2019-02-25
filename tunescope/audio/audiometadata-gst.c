// This file encapsulates all the GStreamer-aware code for the AudioMetadata class.

#include <gst/gst.h>
#include <gst/pbutils/pbutils.h>
#include <glib.h>

#define TIMEOUT_SECONDS 5
#define MAX_ATTEMPTS 3


typedef struct {
    double duration;
    char *title;
    char *artist;
    char *album;
} AudioMetadataStruct;


AudioMetadataStruct *attempt_read(char *uri) {
    AudioMetadataStruct *metadata = (AudioMetadataStruct *) g_malloc0(sizeof(AudioMetadataStruct));

    GError *error = NULL;

    GstDiscoverer *discoverer = gst_discoverer_new(TIMEOUT_SECONDS * GST_SECOND, &error);
    if (discoverer == NULL) {
        g_printerr("gst_discoverer_new() failed: %s\n", error->message);
        g_clear_error(&error);
        return NULL;
    }

    GstDiscovererInfo *info = gst_discoverer_discover_uri(discoverer, uri, &error);
    if (info == NULL) {
        g_printerr("gst_discoverer_discover_uri() failed: %s\n", error->message);
        g_clear_error(&error);
        g_object_unref(discoverer);
        return NULL;
    }

    metadata->duration = ((double) gst_discoverer_info_get_duration(info)) / GST_SECOND;
    if (metadata->duration <= 0) {
        g_printerr("gst_discoverer_discover_uri() failed to get duration\n");
        g_clear_error(&error);
        g_object_unref(discoverer);
        return NULL;
    }

    const GstTagList *tags = gst_discoverer_info_get_tags(info);
    gst_tag_list_get_string(tags, "title", &(metadata->title));
    gst_tag_list_get_string(tags, "artist", &(metadata->artist));
    gst_tag_list_get_string(tags, "album", &(metadata->album));

    gst_discoverer_info_unref(info);
    g_object_unref(discoverer);

    return metadata;
}


// Read metadata for the file at the given URI, returning NULL in case of an error.
// The caller should free the returned struct using audiometadata_gst_delete().
AudioMetadataStruct *audiometadata_gst_read(char *uri)
{
    AudioMetadataStruct *metadata;

    // GstDiscoverer sometimes reports 0 duration on the first try,
    // but returns a positive value on a subsequent attempt.
    for (int attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        metadata = attempt_read(uri);
        if (metadata) {
            return metadata;
        }
    }

    return NULL;
}


void audiometadata_gst_delete(AudioMetadataStruct *metadata)
{
    g_free(metadata->title);
    g_free(metadata->artist);
    g_free(metadata->album);
    g_free(metadata);
}
