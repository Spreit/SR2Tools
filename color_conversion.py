"""
Conversion functions for RGB565, ARGB1555, ARGB4444 and RGBA8888 color spaces
Split into individual functions for speed. You know what speed is, right, Python?
"""
import numpy

'''
16 bit to RGBA8888
'''


def convertRGB565toRGBA8888(pixel_byte_array) -> numpy.array:
    numpy_pixel_byte_array = numpy.frombuffer(pixel_byte_array, dtype=numpy.uint8)

    # Base convertion
    R_numpy = (numpy_pixel_byte_array[1::2] & 0b11111000)
    G_numpy = ((numpy_pixel_byte_array[1::2] & 0b00000111) << 5) + ((numpy_pixel_byte_array[::2] & 0b11100000) >> 3)
    B_numpy = (numpy_pixel_byte_array[::2] & 0b00011111) << 3
    A_numpy = numpy.full(len(pixel_byte_array)//2, 255, dtype=numpy.uint8)

    # Color correction
    R_numpy = R_numpy + (R_numpy // 8) // 4
    G_numpy = G_numpy + (G_numpy // 4) // 16
    B_numpy = B_numpy + (B_numpy // 8) // 4

    rgba8888_pixel_list_numpy = numpy.stack((R_numpy, G_numpy, B_numpy, A_numpy), axis=1)

    return rgba8888_pixel_list_numpy


def convertARGB1555toRGBA8888(pixel_byte_array) -> numpy.array:
    numpy_pixel_byte_array = numpy.frombuffer(pixel_byte_array, dtype=numpy.uint8)

    # Base convertion
    A_numpy = (numpy_pixel_byte_array[1::2] & 0b10000000) >> 7
    R_numpy = (numpy_pixel_byte_array[1::2] & 0b01111100) << 1
    G_numpy = ((numpy_pixel_byte_array[1::2] & 0b00000011) << 6) + ((numpy_pixel_byte_array[::2] & 0b11100000) >> 2)
    B_numpy = (numpy_pixel_byte_array[::2] & 0b00011111) << 3

    # Color correction
    R_numpy = R_numpy + (R_numpy // 8) // 4
    G_numpy = G_numpy + (G_numpy // 8) // 4
    B_numpy = B_numpy + (B_numpy // 8) // 4
    A_numpy = A_numpy * 255

    rgba8888_pixel_list_numpy = numpy.stack((R_numpy, G_numpy, B_numpy, A_numpy), axis=1)

    return rgba8888_pixel_list_numpy


def convertARGB4444toRGBA8888(pixel_byte_array) -> numpy.array:
    numpy_pixel_byte_array = numpy.frombuffer(pixel_byte_array, dtype=numpy.uint8)

    # Base convertion
    A_numpy = (numpy_pixel_byte_array[1::2] & 0b11110000)
    R_numpy = (numpy_pixel_byte_array[1::2] & 0b00001111) << 4
    G_numpy = (numpy_pixel_byte_array[::2] & 0b11110000)
    B_numpy = (numpy_pixel_byte_array[::2] & 0b00001111) << 4

    # Color correction
    R_numpy = R_numpy + (R_numpy // 16)
    G_numpy = G_numpy + (G_numpy // 16)
    B_numpy = B_numpy + (B_numpy // 16)
    A_numpy = A_numpy + (A_numpy // 16)

    rgba8888_pixel_list_numpy = numpy.stack((R_numpy, G_numpy, B_numpy, A_numpy), axis=1)

    return rgba8888_pixel_list_numpy


'''
RGBA8888 to 16 bit
'''


def convertRGBA8888toRGB565bytes(png_numpy_array) -> bytes:

    color_channel_count = png_numpy_array.shape[2]

    png_flat_numpy_array = png_numpy_array.ravel()

    R_numpy = png_flat_numpy_array[2::color_channel_count]
    G_numpy = png_flat_numpy_array[1::color_channel_count]
    B_numpy = png_flat_numpy_array[0::color_channel_count]

    R_numpy = R_numpy & 0b11111000
    G_numpy = G_numpy & 0b11111100
    B_numpy = B_numpy & 0b11111000

    RG_numpy = (R_numpy >> 3) + (G_numpy << 3)
    GB_numpy = (G_numpy >> 5) + B_numpy

    color_bytes_array = numpy.stack((RG_numpy, GB_numpy), axis=1)

    return color_bytes_array.tobytes()


def convertRGBA8888toARGB1555bytes(png_numpy_array) -> bytes:

    color_channel_count = png_numpy_array.shape[2]

    png_flat_numpy_array = png_numpy_array.ravel()

    R_numpy = png_flat_numpy_array[0::color_channel_count]
    G_numpy = png_flat_numpy_array[1::color_channel_count]
    B_numpy = png_flat_numpy_array[2::color_channel_count]
    A_numpy = png_flat_numpy_array[3::color_channel_count]

    A_numpy = A_numpy & 0b10000000
    R_numpy = R_numpy & 0b11111000
    G_numpy = G_numpy & 0b11111000
    B_numpy = B_numpy & 0b11111000

    ARG_numpy = A_numpy + (R_numpy >> 1) + (G_numpy >> 6)
    GB_numpy = (G_numpy << 2) + (B_numpy >> 3)

    color_bytes_array = numpy.stack((GB_numpy, ARG_numpy), axis=1)

    return color_bytes_array.tobytes()


def convertRGBA8888toARGB4444bytes(png_numpy_array) -> bytes:
    color_channel_count = png_numpy_array.shape[2]

    png_flat_numpy_array = png_numpy_array.ravel()

    R_numpy = png_flat_numpy_array[0::color_channel_count]
    G_numpy = png_flat_numpy_array[1::color_channel_count]
    B_numpy = png_flat_numpy_array[2::color_channel_count]
    A_numpy = png_flat_numpy_array[3::color_channel_count]

    A_numpy = A_numpy & 0b11110000
    R_numpy = R_numpy & 0b11110000
    G_numpy = G_numpy & 0b11110000
    B_numpy = B_numpy & 0b11110000

    AR_numpy = A_numpy + (R_numpy >> 4)
    GB_numpy = G_numpy + (B_numpy >> 4)

    color_bytes_array = numpy.stack((GB_numpy, AR_numpy), axis=1)

    return color_bytes_array.tobytes()

