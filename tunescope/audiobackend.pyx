"""
Common audio back end (i.e. GStreamer) code
"""


cdef extern from "<gst/gst.h>":
    void gst_init (int *argc, char **argv[])

cdef extern from "<glib.h>":
    ctypedef int gint
    ctypedef gint gboolean
    ctypedef struct GMainLoop:
        pass
    ctypedef struct GMainContext:
        pass
    GMainLoop *g_main_loop_new(GMainContext *context, gboolean is_running)


cdef bint _gstreamer_initialized = False
cdef GMainLoop *_glib_main_loop = NULL


cdef initialize_if_not_initialized():
    """ Call GStreamer and GLib initialization procedures if necessary. """
    global _gstreamer_initialized, _glib_main_loop
    if not _gstreamer_initialized:
        gst_init(NULL, NULL)
        _gstreamer_initialized = True
    if _glib_main_loop == NULL:
        _glib_main_loop = g_main_loop_new(NULL, False)
