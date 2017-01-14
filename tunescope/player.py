import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import kivy.support
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, BoundedNumericProperty, BooleanProperty, StringProperty
from kivy.clock import Clock

_gst_initialized = False  # True if GStreamer has been initialized


class Player(EventDispatcher):
    """ Audio player engine """

    playing = BooleanProperty(False)  # Set to True to play, False to pause
    position = NumericProperty(0.0)   # Current playback position in file in seconds
    duration = NumericProperty(0.0)   # Duration of file in seconds
    speed = BoundedNumericProperty(1.0, min=0.1, max=2.0)  # Playback speed ratio
    pitch = BoundedNumericProperty(0.0, min=-12, max=12)   # Pitch offset in semitones

    # File metadata
    title = StringProperty("Title")
    artist = StringProperty("Artist")
    album = StringProperty("Album")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._position_sync_interval = None  # ClockEvent for position sync

        # Initialize GStreamer
        global _gst_initialized
        if not _gst_initialized:
            _gst_initialized = Gst.init_check(None)
            if not _gst_initialized:
                raise RuntimeError("Error initializing GStreamer")
            kivy.support.install_gobject_iteration()

        # Build pipeline
        self.pipeline = Gst.Pipeline.new(None)
        if not self.pipeline:
            raise RuntimeError("Could not create GStreamer pipeline")
        self.source = Gst.ElementFactory.make('filesrc', None)
        if not self.source:
            raise RuntimeError("Could not create GStreamer filesrc element")
        self.decoder = Gst.ElementFactory.make('decodebin', None)
        if not self.decoder:
            raise RuntimeError("Could not create GStreamer decodebin element")
        self.converter = Gst.ElementFactory.make('audioconvert', None)
        if not self.converter:
            raise RuntimeError("Could not create GStreamer audioconvert element")
        self.stretcher = Gst.ElementFactory.make('rubberband', None)
        if not self.stretcher:
            raise RuntimeError("Could not create GStreamer rubberband element. "
                               "Is gst-rubberband installed in your GST_PLUGIN_PATH?")
        self.sink = Gst.ElementFactory.make('autoaudiosink', None)
        if not self.sink:
            raise RuntimeError("Could not create GStreamer autoaudiosink element")

        bus = self.pipeline.get_bus()
        bus.add_watch(GLib.PRIORITY_DEFAULT, _bus_watch, self)
        bus.unref()

        self.pipeline.add(self.source)
        self.pipeline.add(self.decoder)
        self.pipeline.add(self.converter)
        self.pipeline.add(self.stretcher)
        self.pipeline.add(self.sink)

        self.source.link(self.decoder)
        self.converter.link(self.stretcher)
        self.stretcher.link(self.sink)

        self.decoder.connect('pad-added', _on_decoder_pad_added, self.converter)

        print("GStreamer pipeline created")

    def open_file(self, filename):
        """ Open an audio file"""
        self.pipeline.set_state(Gst.State.READY)  # required before setting location property
        self.source.set_property('location', filename)
        self.pipeline.set_state(Gst.State.PAUSED)  # Makes the bus send tag events so we can read the tags
        self.playing = False
        self.seek(0)

    def on_playing(self, instance, value):
        """ Play or pause the GStreamer pipeline. Called when `playing` property changes """
        if value:
            self.pipeline.set_state(Gst.State.PLAYING)
            self._enable_position_sync()
        else:
            self.pipeline.set_state(Gst.State.PAUSED)
            self._disable_position_sync()

    def on_speed(self, instance, value):
        """ Change the time ratio of the rubberband element. Called when `speed` property changes """
        self.stretcher.set_property('time-ratio', 1 / value)

    def on_pitch(self, instance, value):
        """ Change the pitch scale of the rubberband element. Called when `pitch` property changes """
        self.stretcher.set_property('pitch-scale', 2 ** (value / 12))

    def on_slider_seek_begin(self):
        """ Called when user starts dragging the position slider """
        self._disable_position_sync()

    def on_slider_seek_end(self):
        """ Called when the user releases the position slider """
        self.seek(self.position)
        if self.playing:
            self._enable_position_sync()

    def seek(self, position):
        """ Seek to the given position in the file.
        This is not done automatically when the `position` property changes
        so that dragging the position slider doesn't cause an immediate seek.
        """
        self.position = position
        success = self.decoder.seek_simple(Gst.Format.TIME,
                                           Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                           self.position * Gst.SECOND)
        if not success:
            print("Error: seek failed")

    def _sync_position(self, dt):
        """ Get the current playback position of the pipeline and update the `position` property """
        success, position = self.decoder.query_position(Gst.Format.TIME)
        if success:
            self.position = position / Gst.SECOND

    def _enable_position_sync(self):
        """ Enable periodic updates of the `position` property from the position of the GStreamer pipeline """
        if not self._position_sync_interval:
            self._position_sync_interval = Clock.schedule_interval(self._sync_position, 1 / 60)

    def _disable_position_sync(self):
        """ Disable the above periodic updates, which should be disabled while user is dragging the slider """
        if self._position_sync_interval:
            self._position_sync_interval.cancel()
            self._position_sync_interval = None


def _bus_watch(bus, message, player):
    """ Process a message from the pipeline bus """

    if message.type == Gst.MessageType.EOS:
        print("End of stream")

    elif message.type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        raise RuntimeError("GStreamer error: {}\nDebug message: {}".format(
            err, debug))

    elif message.type == Gst.MessageType.TAG:
        tag_list = message.parse_tag()
        exists, value = tag_list.get_string('title')
        if exists:
            player.title = value
        exists, value = tag_list.get_string('artist')
        if exists:
            player.artist = value
        exists, value = tag_list.get_string('album')
        if exists:
            player.album = value

    elif message.type == Gst.MessageType.ASYNC_DONE:
        # duration may now be available
        success, duration = player.decoder.query_duration(Gst.Format.TIME)
        if success:
            player.duration = duration / Gst.SECOND
        else:
            print("Could not get duration of file")

    return True


def _on_decoder_pad_added(element, pad, converter):
    """ Connect decoder to converter when decoder pad appears """
    sinkpad = converter.get_static_pad("sink")
    pad.link(sinkpad)
