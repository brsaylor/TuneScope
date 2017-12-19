from tunescope.visualization.spectrogram import spectra_to_pixels
import numpy as np

def test_spectra_to_pixels():

    # row = input value (scaled from 0..1 to 0..4)
    # columns = rgb        # input ranges:
    colormap = np.array([
        [0, 1, 2],         # [0, 0.25)
        [3, 4, 5],         # [0.25, 0.5)
        [6, 7, 8],         # [0.5, 0.75)
        [9, 10, 11],       # [0.75, 1]
    ], dtype=np.uint8)

    # row = time
    # column = bin
    spectra = np.array([
        [0.1, 0.00, 0.25],
        [0.1, 0.50, 1.00],
    ])

    # bottom bin removed:
    # 0.00  0.25
    # 0.50  1.00

    # transposed:
    # 0.00  0.50
    # 0.25  1.00

    # colormap indices:
    # 0  2
    # 1  3

    # row = bin
    # column = time
    expected_pixels = np.array([
        0,1,2, 6,7,8,
        3,4,5, 9,10,11,
    ], dtype=np.uint8) 

    expected_size = (2, 2)

    actual_pixels, actual_size = spectra_to_pixels(spectra, colormap)

    assert actual_pixels.dtype == expected_pixels.dtype
    assert actual_size == expected_size
    assert np.all(actual_pixels == expected_pixels)
