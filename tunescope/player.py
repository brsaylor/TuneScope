from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, BoundedNumericProperty, BooleanProperty, StringProperty
from kivy.clock import Clock
import numpy as np

from .audiometadata import AudioMetadata
from .audiodecoder import AudioDecoder
from .buffering import DecoderBuffer
from .looper import Looper
from .timestretcher import TimeStretcher
from .audiooutput import AudioOutput


_FRAMERATE = 60.0
_POSITION_INTERPOLATION_THRESHOLD = 0.2
_POSITION_CORRECTION_FRAMES = 60.0


class Player(EventDispatcher):
    """ Audio player engine """

    playing = BooleanProperty(False)  # Set to True to play, False to pause
    position = NumericProperty(0.0)   # Current playback position in file in seconds
    duration = NumericProperty(0.0)   # Duration of file in seconds
    speed = BoundedNumericProperty(1.0, min=0.1, max=2.0)   # Playback speed ratio
    transpose = BoundedNumericProperty(0, min=-12, max=12)  # Semitones component of pitch
    tuning = BoundedNumericProperty(0, min=-50, max=50)     # Cents component of pitch
    looping_enabled = BooleanProperty(False)
    loop_start = NumericProperty(0.0)
    loop_end = NumericProperty(0.0)

    # File metadata
    title = StringProperty("Title")
    artist = StringProperty("Artist")
    album = StringProperty("Album")

    def __init__(self, **kwargs):
        super(Player, self).__init__(**kwargs)

        self._audio_decoder = None
        self._decoder_buffer = None
        self._looper = None
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
        self._looper = Looper(self._decoder_buffer)
        self._time_stretcher = TimeStretcher(self._looper)
        self._time_stretcher.eos_callback = self.on_eos
        self._audio_output = AudioOutput(self._time_stretcher)

        self._previous_pipeline_position = 0.0
        self._position_error = 0.0
        self._position_correction_increment = 0.0

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
        if self._audio_output is None:
            return
        if value:
            self._audio_output.play()
            self._enable_position_sync()
        else:
            self._audio_output.pause()
            self._disable_position_sync()

    def on_looping_enabled(self, instance, value):
        if not self._looper:
            return False
        if self.loop_start >= self.loop_end or self.loop_end > self.duration:
            self.loop_start = 0
            self.loop_end = self.duration
        self._update_looper()

    def on_loop_start(self, instance, value):
        self.loop_start = min(self.duration - 1, self.loop_start)
        self.loop_end = max(self.loop_start + 1, self.loop_end)
        self._update_looper()

    def on_loop_end(self, instance, value):
        self.loop_end = max(1.0, self.loop_end)
        self.loop_start = min(self.loop_start, self.loop_end - 1)
        self._update_looper()

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
        def stop_playing(dt):
            self.playing = False
        Clock.schedule_once(stop_playing)

    def seek(self, position):
        """ Seek to the given position in the file.
        This is not done automatically when the `position` property changes
        so that dragging the position slider doesn't cause an immediate seek.
        """
        if self._time_stretcher is None:
            return
        success = self._time_stretcher.seek(position)
        if success:
            self.position = position
        else:
            print("Error: seek failed")

    def close_audio_device(self):
        """ Close the audio device. Must be called before the application exits """
        if self._audio_output is not None:
            self._audio_output.close()

    def _sync_position(self, dt):
        """ Update the `position` property from the pipeline position, using interpolation 
        to correct for infrequent pipeline position updates and jitter """
        pipeline_position = self._time_stretcher.position
        pipeline_position_change = pipeline_position - self._previous_pipeline_position
        if abs(pipeline_position_change) > _POSITION_INTERPOLATION_THRESHOLD:
            # Pipeline position changed significantly; sync `position` directly
            new_position = pipeline_position
        else:
            # Interpolate position, gradually correcting for error between
            # estimated position and pipeline position
            new_position = self.position + dt * self.speed
            if pipeline_position_change != 0:
                # Pipeline position changed; recalculate error
                self._position_error = new_position - pipeline_position
                self._position_correction_increment = (-self._position_error
                                                       / _POSITION_CORRECTION_FRAMES)
            if not np.isclose(self._position_error, 0):
                new_position += self._position_correction_increment
                self._position_error -= self._position_correction_increment
        self._previous_pipeline_position = pipeline_position
        self.position = new_position

    def _enable_position_sync(self):
        """ Enable periodic updates of the `position` property from the audio pipeline """
        if not self._position_sync_interval:
            self._position_sync_interval = Clock.schedule_interval(self._sync_position,
                                                                   1 / _FRAMERATE)

    def _disable_position_sync(self):
        """ Disable the above periodic updates, which should be disabled while user is dragging the slider """
        if self._position_sync_interval:
            self._position_sync_interval.cancel()
            self._position_sync_interval = None

    def _update_pitch(self):
        """ Update the pitch scale of the time stretcher from `transpose` and `tuning`. """
        if self._time_stretcher is not None:
            self._time_stretcher.pitch = self.transpose + self.tuning / 100.0

    def _update_looper(self):
        """ Activate or deactivate the Looper based on looping properties """
        if self.looping_enabled:
            self._looper.activate(self.loop_start, self.loop_end)
        else:
            self._looper.deactivate()
