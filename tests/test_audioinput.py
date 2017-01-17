import pytest
import numpy as np
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

from tunescope.audioinput import *


Gst.init(None)


def test_copy_buffer():

    dtype = np.int32

    # Make source Gst.Buffer
    src_array = np.array([
        [10, 20],
        [30, 40],
    ], dtype=dtype)
    src_bytes = src_array.tobytes()
    src = Gst.Buffer.new_wrapped(src_bytes)

    # Need a new dest array for each test
    def make_dest_array():
        return np.array([
            [1, 2],
            [3, 4],
            [5, 6],
        ], dtype=dtype)

    # Copy first frame of src to first frame of dest
    dest = make_dest_array()
    copy_buffer(src, 0, dest, 0, 1)
    assert np.all(dest == np.array([
        [10, 20],
        [3, 4],
        [5, 6]
    ]))

    # Copy both frames of src to start of dest
    dest = make_dest_array()
    copy_buffer(src, 0, dest, 0, 2)
    assert np.all(dest == np.array([
        [10, 20],
        [30, 40],
        [5, 6]
    ]))

    # Copy both frames of src to end of dest
    dest = make_dest_array()
    copy_buffer(src, 0, dest, 1, 2)
    assert np.all(dest == np.array([
        [1, 2],
        [10, 20],
        [30, 40]
    ]))

    # Try to copy past end of dest
    dest = make_dest_array()
    with pytest.raises(ValueError):
        copy_buffer(src, 0, dest, 2, 2)

    # Try to copy more frames from src than it contains
    dest = make_dest_array()
    with pytest.raises(ValueError):
        copy_buffer(src, 0, dest, 0, 3)
