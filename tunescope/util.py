import os.path
import sys


def bind_properties(properties, callback):
    """ Bind multiple properties to a callback.

    `properties`: a list of tuples indicating the objects and their properties
    to bind. The first element of each tuple is an EventDispatcher instance. The
    remaining elements of the tuple are the names of the properties of that
    EventDispatcher to bind.

    `callback`: a function that will be called whenever any of the properties
    change. The EventDispatchers will be passed as positional arguments.
    """
    dispatchers = [p[0] for p in properties]

    def bound_callback(*args):
        callback(*dispatchers)

    for p in properties:
        dispatcher, prop_names = p[0], p[1:]
        for prop_name in prop_names:
            dispatcher.bind(**{prop_name: bound_callback})


def get_data_dir():
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        return os.path.join(sys._MEIPASS, 'data')
    else:
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')


def format_time(t):
    minutes = int(t) // 60
    seconds = t - 60 * minutes
    return "{}:{:05.2f}".format(minutes, seconds)


def decode_file_path(file_path):
    """ Decode the given file path string and return a unicode string. No-op if
    file_path is already unicode """
    # FIXME: assumes python2
    if isinstance(file_path, unicode):
        return file_path
    return unicode(file_path, sys.getfilesystemencoding())


def encode_file_path(file_path):
    """ Inverse of decode_file_path """
    if not isinstance(file_path, unicode):
        return file_path
    return file_path.encode(sys.getfilesystemencoding())
