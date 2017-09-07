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
    speed = BoundedNumericProperty(1.0, min=0.1, max=2.0)   # Playback speed ratio
    transpose = BoundedNumericProperty(0, min=-12, max=12)  # Semitones component of pitch
    tuning = BoundedNumericProperty(0, min=-50, max=50)     # Cents component of pitch

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
        self._time_stretcher.eos_callback = self.on_eos
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

        self._decoder_buffer_previous_position = 0

    def on_playing(self, instance, value):
        """ Play or pause playback. Called when `playing` property changes """
        if self._audio_output is None:
            return
        if value:
            self._audio_output.play()
            self._enable_position_sync()
        else:
            self._audio_output.pause()
            self._disable_position_sync()

    def on_speed(self, instance, value):
        """ Change the speed of the time stretcher. Called when `speed` property changes """
        if self._time_stretcher is not None:
            self._time_stretcher.speed = value

    def increment_transpose(self, semitones):
        try:
            self.transpose += semitones
        except ValueError:
            pass

    def on_transpose(self, instance, value):
        self._update_pitch()

    def on_tuning(self, instance, value):
        if value > -1 and value < 1:
            self.tuning = 0
        self._update_pitch()

    def on_slider_seek_begin(self):
        """ Called when user starts dragging the position slider """
        self._disable_position_sync()

    def on_slider_seek_end(self):
        """ Called when the user releases the position slider """
        self.seek(self.position)
        if self.playing:
            self._enable_position_sync()

    def on_eos(self):
        """ Called when end of stream is reached """
        self.playing = False

    def seek(self, position):
        """ Seek to the given position in the file.
        This is not done automatically when the `position` property changes
        so that dragging the position slider doesn't cause an immediate seek.
        """
        if self._decoder_buffer is None:
            return
        success = self._decoder_buffer.seek(position)
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
        position_change = self._decoder_buffer.position - self._decoder_buffer_previous_position
        if position_change == 0 and self.playing:
            # Interpolate position between pipeline position updates.
            # (The precision of the pipeline position is limited by the audio
            # output buffer size.)
            self.position += dt * self._time_stretcher.speed
        else:
            self.position = self._decoder_buffer.position
        self._decoder_buffer_previous_position = self._decoder_buffer.position

    def _enable_position_sync(self):
        """ Enable periodic updates of the `position` property from the audio pipeline """
        if not self._position_sync_interval:
            self._position_sync_interval = Clock.schedule_interval(self._sync_position, 1 / 60)

    def _disable_position_sync(self):
        """ Disable the above periodic updates, which should be disabled while user is dragging the slider """
        if self._position_sync_interval:
            self._position_sync_interval.cancel()
            self._position_sync_interval = None

    def _update_pitch(self):
        """ Update the pitch scale of the time stretcher from `transpose` and `tuning`. """
        if self._time_stretcher is not None:
            self._time_stretcher.pitch = self.transpose + self.tuning / 100.0
