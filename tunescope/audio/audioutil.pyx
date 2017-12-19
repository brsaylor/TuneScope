import numpy as np
cimport numpy as np
from libc.math cimport ceil


cpdef np.ndarray[np.float32_t] pad_block(
        np.ndarray[np.float32_t] block,
        size_t target_size):
    """ Return a new, zero-padded array whose initial elements are a copy of `block`. """
    cdef np.ndarray[np.float32_t] padded_block = np.empty(target_size, dtype=np.float32)
    padded_block[:len(block)] = block
    padded_block[len(block):] = 0
    return padded_block
