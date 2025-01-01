# You would think that BMP would be supported in everything since it exists since forever, but nope.
import numpy
from PIL import Image
import color_conversion
from bmp_handler import BMP


def BMPtoPNG(unpacked_bmp: BMP) -> Image:
    """
    Unpack BMP image using BMP class
    Convert 16-bit pixel bytes into RGBA8888 array
    Turn the array into PIL Image
    """
    bmp_bpp = unpacked_bmp.image_header["BPP"]
    bmp_color_format = unpacked_bmp.check_color_format()
    bmp_pixel_bytes = unpacked_bmp.pixel_bytes

    png_pixel_array = []

    # print("BMP Color Format is " + bmp_color_format)
    # print("Palette length " + str(len(unpacked_bmp.color_table_bytes)))

    color_channel_count = 4

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
    else:
        if bmp_bpp == 16:
            if bmp_color_format == "RGB565":
                png_pixel_array = color_conversion.convertRGB565toRGBA8888(bmp_pixel_bytes)
            elif bmp_color_format == "ARGB1555":
                png_pixel_array = color_conversion.convertARGB1555toRGBA8888(bmp_pixel_bytes)
            elif bmp_color_format == "ARGB4444":
                png_pixel_array = color_conversion.convertARGB4444toRGBA8888(bmp_pixel_bytes)

        elif bmp_bpp == 24:
            color_channel_count = 3
            for pixel_byte_index in range(0, len(bmp_pixel_bytes), 3):
                # print(pixel_byte_index)
                r = bmp_pixel_bytes[pixel_byte_index+2]
                g = bmp_pixel_bytes[pixel_byte_index+1]
                b = bmp_pixel_bytes[pixel_byte_index]
                png_pixel_array.append((r, g, b))
        elif bmp_bpp == 32:
            for pixel_byte_index in range(0, len(bmp_pixel_bytes), 4):
                # print(pixel_byte_index)
                b = bmp_pixel_bytes[pixel_byte_index]
                g = bmp_pixel_bytes[pixel_byte_index+1]
                r = bmp_pixel_bytes[pixel_byte_index+2]
                a = bmp_pixel_bytes[pixel_byte_index+3]
                png_pixel_array.append((r, g, b, a))
        else:
            raise ValueError("Wrong BPP")

    width = unpacked_bmp.image_header["Image Width"]
    height = unpacked_bmp.image_header["Image Height"]

    png_pixel_array = numpy.array(png_pixel_array, dtype=numpy.uint8)
    png_pixel_array = png_pixel_array.reshape(abs(height), width, color_channel_count)
    png_pixel_array = numpy.flip(png_pixel_array, 0)

    png_output = Image.fromarray(png_pixel_array)

    return png_output


def PNGtoBMP(unpacked_png, output_color_format) -> BMP:
    """
    Turn PNG into pixel array
    Convert the array into 16-bit pixel bytes
    Assemble BMP out of it
    """
    width, height = unpacked_png.size
    png_array = numpy.asarray(unpacked_png)
    numpy.flip(png_array)
    png_array = png_array.tolist()
    #png_array = png_array[::-1]

    converted_pixel_bytes = b''

    if output_color_format == "RGB565":
        converted_pixel_bytes = color_conversion.convertARGB8888toRGB565bytes(png_array)
    elif output_color_format == "ARGB1555":
        converted_pixel_bytes = color_conversion.convertARGB8888toRGBA1555bytes(png_array)
    elif output_color_format == "ARGB4444":
        converted_pixel_bytes = color_conversion.convertARGB8888toARGB4444bytes(png_array)

    output_bmp = BMP()
    output_bmp.set_resolution(width, height)
    output_bmp.swapColorFormat(output_color_format)
    output_bmp.pixel_bytes = converted_pixel_bytes

    return output_bmp

