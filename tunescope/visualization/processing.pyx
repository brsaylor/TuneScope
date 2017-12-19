import numpy as np
cimport numpy as np
from libc.math cimport ceil


cpdef np.ndarray[np.float32_t] log_axis(np.ndarray[np.float32_t, ndim=2] input_spectra):
    """
    Given an array of spectra (row=time, col=bin) whose bins are linearly spaced
    in frequency, return new array of the same shape whose bins are
    exponentially spaced in frequency. Output bin 1 (second bin) is centered on
    the same frequency as input bin 1, and the last output bin is centered on
    the same frequency as the last input bin.
    """
    cdef int duration = input_spectra.shape[0]
    cdef int bins = input_spectra.shape[1]
    cdef np.ndarray[np.float32_t, ndim=2]\
            output_spectra = np.zeros((duration, bins), dtype=np.float32)
    cdef float max_bin = bins - 1
    cdef float ratio = max_bin ** (1. / (max_bin - 1)) 
    cdef int ibin  # input bin index
    cdef int obin  # output bin index
    cdef int t     # time
    cdef float ibin_upper_bound, ibin_lower_bound
    cdef float obin_lower_bound, obin_upper_bound

    for obin in range(bins):
        obin_lower_bound = 0 if obin == 0 else ratio ** (obin - 0.5 - 1)
        obin_upper_bound = min(ratio ** (obin + 0.5 - 1), max_bin)

        for ibin in range(<int> obin_lower_bound,
                          <int> ceil(obin_upper_bound) + 1):
            ibin_upper_bound = max(ibin - 0.5, 0)
            ibin_lower_bound = min(ibin + 0.5, max_bin)

            for t in range(duration):
                output_spectra[t,obin] += (
                    input_spectra[t,ibin] / (ibin_lower_bound - ibin_upper_bound)
                    * max(min(obin_upper_bound, ibin_lower_bound)
                           - max(obin_lower_bound, ibin_upper_bound),
                          0))

    return output_spectra
