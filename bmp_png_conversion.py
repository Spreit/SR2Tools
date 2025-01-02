# You would think that BMP would be supported in everything since it exists since forever, but nope.
import numpy
from PIL import Image

import color_conversion
from bmp_handler import BMPv5


def BMPtoPNG(unpacked_bmp: BMPv5) -> Image:
    """
    Unpack BMP image using BMP class
    Convert 16-bit pixel bytes into RGBA8888 array
    Turn the array into PIL Image
    """
    bmp_bpp = unpacked_bmp.image_header["BPP"]
    bmp_color_format = unpacked_bmp.check_color_format()
    bmp_pixel_bytes = unpacked_bmp.pixel_bytes

    png_pixel_array = []

    if len(unpacked_bmp.color_table_bytes) > 0:
        color_palette_bytes = unpacked_bmp.color_table_bytes
        color_palette_array = numpy.frombuffer(color_palette_bytes, dtype=numpy.uint8)
        color_palette_array = color_palette_array.reshape(1, 256, 4).copy()

        for color_array_index in range(len(color_palette_array[0])):
            R = color_palette_array[0, color_array_index, 2]
            G = color_palette_array[0, color_array_index, 1]
            B = color_palette_array[0, color_array_index, 0]

            color_palette_array[0, color_array_index, 0] = R
            color_palette_array[0, color_array_index, 1] = G
            color_palette_array[0, color_array_index, 2] = B
            color_palette_array[0, color_array_index, 3] = 255

        if bmp_color_format == "ARGB1555":
            color_palette_array[0, 0, 3] = 0  # First color is transparent

        # print(color_palette_array)

        for color_index_byte in bmp_pixel_bytes:
            pixel_array = color_palette_array[0][color_index_byte]
            png_pixel_array.append(pixel_array)

        png_pixel_array = numpy.array(png_pixel_array, dtype=numpy.uint8)
    else:
        if bmp_bpp == 16:
            if bmp_color_format == "RGB565":
                png_pixel_array = color_conversion.convertRGB565toRGBA8888(bmp_pixel_bytes)
            elif bmp_color_format == "ARGB1555":
                png_pixel_array = color_conversion.convertARGB1555toRGBA8888(bmp_pixel_bytes)
            elif bmp_color_format == "ARGB4444":
                png_pixel_array = color_conversion.convertARGB4444toRGBA8888(bmp_pixel_bytes)

        elif bmp_bpp == 24:
            numpy_pixel_byte_array = numpy.frombuffer(bmp_pixel_bytes, dtype=numpy.uint8)

            R_numpy = numpy_pixel_byte_array[2::3]
            G_numpy = numpy_pixel_byte_array[1::3]
            B_numpy = numpy_pixel_byte_array[::3]
            A_numpy = numpy.full(len(bmp_pixel_bytes) // 2, 255, dtype=numpy.uint8)

            png_pixel_array = numpy.stack((R_numpy, G_numpy, B_numpy, A_numpy), axis=1)

        elif bmp_bpp == 32:
            numpy_pixel_byte_array = numpy.frombuffer(bmp_pixel_bytes, dtype=numpy.uint8)

            R_numpy = numpy_pixel_byte_array[2::4]
            G_numpy = numpy_pixel_byte_array[3::4]
            B_numpy = numpy_pixel_byte_array[::4]
            A_numpy = numpy_pixel_byte_array[1::4]

            png_pixel_array = numpy.stack((R_numpy, G_numpy, B_numpy, A_numpy), axis=1)
        else:
            raise ValueError("Wrong BPP")

    width = unpacked_bmp.image_header["Image Width"]
    height = unpacked_bmp.image_header["Image Height"]

    png_pixel_array = png_pixel_array.reshape(abs(height), width, 4)

    # GIMP flips the image by flipping pixel bytes.
    # SR2 Tools doesn't and instead sets negative height in the header like it supposed to be done.
    # GIMP doesn't like this and will show an error every time you open a BMP like this
    if height < 0:
        numpy.flip(png_pixel_array)

    png_output = Image.fromarray(png_pixel_array)

    return png_output


def PNGtoBMP(unpacked_png: Image, output_color_format) -> BMPv5:
    """
    Turn PNG into pixel array
    Convert the array into 16-bit pixel bytes
    Assemble BMP out of it
    """
    width, height = unpacked_png.size
    png_numpy_array = numpy.asarray(unpacked_png, dtype=numpy.uint8)
    numpy.flip(png_numpy_array)

    converted_pixel_bytes = b''

    if output_color_format == "RGB565":
        converted_pixel_bytes = color_conversion.convertRGBA8888toRGB565bytes(png_numpy_array)
    elif output_color_format == "ARGB1555":
        converted_pixel_bytes = color_conversion.convertRGBA8888toARGB1555bytes(png_numpy_array)
    elif output_color_format == "ARGB4444":
        converted_pixel_bytes = color_conversion.convertRGBA8888toARGB4444bytes(png_numpy_array)

    output_bmp = BMPv5()
    output_bmp.set_resolution(width, height)
    output_bmp.swapColorFormat(output_color_format)
    output_bmp.pixel_bytes = converted_pixel_bytes

    return output_bmp
