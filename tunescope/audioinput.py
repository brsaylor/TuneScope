import numpy as np
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst


sample_dtype = np.float32


def copy_buffer(src, src_pos, dest, dest_pos, length):
    """ Copy sample frames from a Gst.Buffer into a NumPy array.

    The destination array is assumed to be 2-dimensional, with rows
    representing frames and columns representing channels. The source
    buffer is assumed to contain interleaved samples of the same data type
    as the destination, with the same number of channels.

    The implementation is intended to copy the data exactly once.

    Parameters
    ----------
    src : Gst.Buffer
        The source buffer
    src_pos : int
        Starting frame position in the source buffer
    dest : ndarray
        The destination array
    dest_pos : int
        Starting frame position in the destination array
    length
        Number of frames to copy
    """

    # Map the src buffer so we can get at the data
    success, src_info = src.map(Gst.MapFlags.READ)
    if not success:
        raise RuntimeError("copy_buffer() failed")

    # Create 1-dimensional memoryviews of the bytes in src and dest
    src_mem = memoryview(src_info.data)
    dest_mem = dest.data.cast('B', (dest.data.nbytes,))

    # Calculate src and dest byte offsets
    bytes_per_frame = dest.dtype.itemsize * dest.shape[1]
    length_bytes = length * bytes_per_frame
    s1 = src_pos * bytes_per_frame
    s2 = s1 + length_bytes
    d1 = dest_pos * bytes_per_frame
    d2 = d1 + length_bytes

    # Copy the data (this should be the only copy performed!)
    dest_mem[d1:d2] = src_mem[s1:s2]

    src.unmap(src_info)
