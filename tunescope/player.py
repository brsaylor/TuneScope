import kivy.support
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, BoundedNumericProperty, BooleanProperty, StringProperty
from kivy.clock import Clock

from .audiometadata import AudioMetadata
from .audiodecoder import AudioDecoder
from .buffering import DecoderBuffer
from .timestretcher import TimeStretcher
from .audiooutput import AudioOutput

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
        super(Player, self).__init__(**kwargs)

        self._audio_decoder = None
        self._decoder_buffer = None
        self._time_stretcher = None
        self._audio_output = None

        self._position_sync_interval = None  # ClockEvent for position sync

    def open_file(self, filename):
        """ Open an audio file"""

        if self._audio_output is not None:
            self._audio_output.close()

        # Build audio pipeline
        self._audio_decoder = AudioDecoder(filename)
        self._decoder_buffer = DecoderBuffer(self._audio_decoder, 4096)
        self._time_stretcher = TimeStretcher(self._decoder_buffer)
        self._audio_output = AudioOutput(self._time_stretcher)

        metadata = AudioMetadata(filename)
        self.duration = metadata.duration
        self.title = metadata.title
        self.artist = metadata.artist
        self.album = metadata.album

        self.playing = False
        self.seek(0)
        self.speed = 1
        self.pitch = 0

    def on_playing(self, instance, value):
        """ Play or pause playback. Called when `playing` property changes """
        if value:
            self._audio_output.play()
            self._enable_position_sync()
        else:
            self._audio_output.pause()
            self._disable_position_sync()

    def on_speed(self, instance, value):
        """ Change the speed of the time stretcher. Called when `speed` property changes """
        self._time_stretcher.speed = value

    def on_pitch(self, instance, value):
        """ Change the pitch scale of the time stretcher. Called when `pitch` property changes """
        self._time_stretcher.pitch = value

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
        if self._audio_decoder is None:
            return
        success = self._audio_decoder.seek(position)
        if success:
            self.position = position
            if self._time_stretcher.is_eos():
                self._time_stretcher.reset()
        else:
            print("Error: seek failed")

    def close_audio_device(self):
        """ Close the audio device. Must be called before the application exits """
        if self._audio_output is not None:
            self._audio_output.close()

    def _sync_position(self, dt):
        """ Get the current playback position of the pipeline and update the `position` property """
        self.position = self._audio_decoder.position

    def _enable_position_sync(self):
        """ Enable periodic updates of the `position` property from the audio pipeline """
        if not self._position_sync_interval:
            self._position_sync_interval = Clock.schedule_interval(self._sync_position, 1 / 60)

    def _disable_position_sync(self):
        """ Disable the above periodic updates, which should be disabled while user is dragging the slider """
        if self._position_sync_interval:
            self._position_sync_interval.cancel()
            self._position_sync_interval = None
