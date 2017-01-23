import math

import numpy as np
import aubio
from audioread.gstdec import GstAudioFile

from .audioinput import AudioQueue, QueueFullError, sample_dtype


# Buffer and queue sizes in sample frames
INITIAL_QUEUE_CAPACITY = 16384
MAX_QUEUE_CAPACITY = INITIAL_QUEUE_CAPACITY * 64
WINDOW_SIZE = 2048  # aubio window size
HOP_SIZE = 512      # aubio hop size (this is the time resolution of the analyses)


class Analyzer(object):
    """ Performs sound/musical analysis on an audio file.

    Parameters
    ----------
    filename : str
        File path to the audio file to analyze

    Attributes
    ----------
    pitch : ndarray
        2-dimensional array where each row represents a detected pitch.
        The first column represents time in seconds.
        The second column represents the pitch as a (possibly non-integer) MIDI note number.
        Will be None until analyze() is called.
    """

    def __init__(self, filename):
        self.filename = filename
        self.pitch = None
        self._reader = None
        self._queue = None

    def analyze(self):
        """ Perform the analysis """

        with GstAudioFile(self.filename, format='F32') as self._reader:

            self._queue = AudioQueue(self._reader.channels, INITIAL_QUEUE_CAPACITY)
            pitch_detector = aubio.pitch('yinfft', WINDOW_SIZE, HOP_SIZE, self._reader.samplerate)
            pitch_detector.set_unit('midi')

            duration_frames = math.ceil(self._reader.duration * self._reader.samplerate)
            duration_hops = math.ceil(duration_frames / HOP_SIZE)

            # Each row contains (time, pitch)
            self.pitch = np.zeros((duration_hops, 2), dtype=np.float32)

            for hop in range(duration_hops):
                frames = self._pull_buffer()
                frames_mono = frames.mean(axis=1)
                self.pitch[hop, 0] = hop * HOP_SIZE / self._reader.samplerate  # time in seconds
                self.pitch[hop, 1] = pitch_detector(frames_mono)[0]

    def _pull_buffer(self):
        """ Retrieve HOP_SIZE sample frames from the file, adapting the buffer size. """

        # While there isn't enough data in the queue, read from the file to fill it
        while self._queue.size < HOP_SIZE:
            try:
                inbuf = self._reader.__next__()
                self._queue.put(inbuf)
            except StopIteration:
                break
            except QueueFullError:
                buffer_frame_count = len(inbuf) // self._reader.channels // sample_dtype().itemsize
                new_capacity = self._queue.capacity + buffer_frame_count
                if new_capacity > MAX_QUEUE_CAPACITY:
                    raise QueueFullError("Queue has exceeded maximum capacity of {} frames".format(MAX_QUEUE_CAPACITY))
                self._queue.expand(new_capacity)
                self._queue.put(inbuf)

        # Queue now has enough (at least HOP_SIZE) sample frames in it,
        # or all remaining frames from the input file.

        if self._queue.size >= HOP_SIZE:
            return self._queue.get(HOP_SIZE)
        else:
            # Handle final (or post-final) buffer by padding remaining data with zeros
            frames_left = self._queue.size
            return np.concatenate((
                self._queue.get(frames_left),
                np.zeros((HOP_SIZE - frames_left, self._queue.channels), dtype=sample_dtype)
            ), axis=0)
