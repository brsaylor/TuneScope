cimport numpy as np

cpdef np.ndarray[np.float32_t] pad_block(
        np.ndarray[np.float32_t] block,
        size_t target_size)
