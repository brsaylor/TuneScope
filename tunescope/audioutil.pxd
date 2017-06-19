cimport numpy as np

cdef np.ndarray[np.float32_t] pad_block(
        np.ndarray[np.float32_t] block,
        size_t target_size)
