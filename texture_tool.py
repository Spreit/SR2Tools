# Texture converter
import os
from texture_classes import *
from PIL import Image
import numpy
import bmp_png_conversion


def detect_texture_type(input_texture_path: str):
    with open(input_texture_path, 'r+b') as f:
        file_signature = f.read(4)

    match file_signature:
        case b'RTEX':
            input_texture = RTEX()
        case b'RHBG':
            input_texture = RHBG()
        case b'RTXR':
            input_texture = RTXR()
        case b'MTEX':
            input_texture = MTEX()
        case _:
            raise ValueError("Not a texture file / Can't be exported")

    return input_texture


def convertTXRtoBMPlist(input_texture_path: str) -> list:
    output_bmp_list = []
    input_texture = detect_texture_type(input_texture_path)
    input_texture.unpack_from_file(input_texture_path)

    for texture_id in range(len(input_texture.texture_header_list)):
        output_bmp = input_texture.setup_bmp(texture_id)

        image_width = input_texture.texture_header_list[texture_id]["Image Width"]
        try:
            image_height = input_texture.texture_header_list[texture_id]["Image Height"]
        except KeyError:
            image_height = image_width

        output_bmp.set_resolution(image_width, image_height)
        output_bmp.pixel_bytes = input_texture.pixel_bytes_list[texture_id]
        output_bmp_list.append(output_bmp)

    return output_bmp_list


# With smart path system
def convertTXRtoBMP(input_path, output_path, png_export=False):

    if input_path == "":
        raise ValueError("Invalid input_path")

    input_texture_list = []

    # Fill input_texture_list
    if os.path.isdir(input_path):
        if output_path[output_path.rfind("."):] == ".bmp":
            print("Input path: " + input_path)
            print("Output path: " + output_path)
            raise ValueError("A folder can't be extracted into a bmp, only into another folder")

        for filename in os.listdir(input_path):
            if os.path.isfile(input_path + filename):
                input_texture_list.append(input_path + filename)
    elif os.path.isfile(input_path):
        input_texture_list.append(input_path)

    # Iterate through the texture list and export each
    for texture_path in input_texture_list:

        # Set up output file name
        bmp_path = output_path

        if not output_path:
            bmp_path = texture_path
        elif os.path.isdir(output_path) or output_path[output_path.rfind("."):] != ".bmp":
            texture_path_file_title = texture_path[texture_path.rfind("/") + 1:]
            bmp_path = output_path + texture_path_file_title
            os.makedirs(os.path.dirname(bmp_path), exist_ok=True)

        file_signature = open(texture_path, "rb").read(4)

        if ((file_signature != b'RTEX' and file_signature != b'RHBG' and file_signature != b'MTEX')
                or (texture_path[-4:] == ".BIN" or texture_path[-4:] == ".bin")):
            print("Not a texture file / Can't be exported")
            continue

        input_texture_file = detect_texture_type(texture_path)
        input_texture_file.unpack_from_file(texture_path)

        for subtexture_id in range(len(input_texture_file.texture_header_list)):

            output_bmp = input_texture_file.setup_bmp(subtexture_id)

            output_bmp.pixel_bytes = input_texture_file.pixel_bytes_list[subtexture_id]

            bmp_formated_path = bmp_path + '.{}.bmp'.format(subtexture_id)

            os.makedirs(os.path.dirname(bmp_formated_path), exist_ok=True)

            if png_export:
                png_formated_path = bmp_formated_path[:-3] + "png"
                png = bmp_png_conversion.BMPtoPNG(output_bmp)
                png.save(png_formated_path)
                print("Saved " + png_formated_path)
            else:
                output_bmp.save(bmp_formated_path)
                print("Saved " + bmp_formated_path)


def scanDirectoryForFilesByExtension(directory_path, file_extension):
    file_list = []

    if os.path.isfile(directory_path):
        if directory_path[directory_path.rfind("."):] != file_extension:
            print("Input file is not supported")
            return
        file_list.append(directory_path)
    elif os.path.isdir(directory_path):
        for filename in os.listdir(directory_path):
            if filename[filename.rfind("."):] == file_extension:
                file_list.append(directory_path + filename)
    else:
        print(directory_path)
        raise ValueError("Invalid input file/folder")

    return file_list


def groupImagesByFileName(input_image_list):
    group_dictionary = {}

    # Group input images by their title
    # ./folder/input.txr.0.bmp -> ./folder/input.txr
    for image_path in input_image_list:
        extension_dot = image_path[1:].find(".") + 1
        index_dot = image_path[extension_dot + 1:].find(".") + 1
        texture_group_path = image_path[:extension_dot + index_dot]

        if texture_group_path not in group_dictionary:
            group_dictionary[texture_group_path] = []

        group_dictionary[texture_group_path].append(image_path)

    return group_dictionary


def convertBMPtoTXR(input_path, output_path, png_input=False):

    if png_input:
        input_image_extension = ".png"
    else:
        input_image_extension = ".bmp"

    # Find all input images
    input_image_list = scanDirectoryForFilesByExtension(input_path, input_image_extension)
    input_image_list = sorted(input_image_list, key=len)

    grouped_bmp_dict = groupImagesByFileName(input_image_list)

    for bmp_group in grouped_bmp_dict:

        # Avoid unpacking B_CARTEX.BIN, because of course there is a single file that ruins everything
        if bmp_group[-4:] == ".bin" or bmp_group[-4:] == ".BIN":
            continue

        output_format = b'RTEX'
        txr_output = RTEX()

        if ((bmp_group[-3:] == ".bg" or bmp_group[-3:] == ".BG")
                or (output_path.find(".bg") or output_path.find(".BG"))):
            output_format = b'RHBG'
            txr_output = RHBG()

        for image_path in grouped_bmp_dict[bmp_group]:

            if png_input:
                probably_correct_texture_format = guessColorFormatfromPNG(image_path)
                png_input = Image.open(image_path)
                bmp_input = bmp_png_conversion.PNGtoBMP(png_input, probably_correct_texture_format)
            else:
                bmp_input = BMPv5()
                bmp_input.unpack_from_file(image_path)

            if output_format == b'RHBG':
                txr_output.convert_bmp_headers_to_texture_header(bmp_input)

                if bmp_input.image_header["Image Height"] > 0:
                    bmp_input.pixel_bytes = flip_pixel_bytes_vertically(bmp_input.pixel_bytes,
                                                                        bmp_input.image_header["Image Width"],
                                                                        abs(bmp_input.image_header["Image Height"]),
                                                                        bmp_input.image_header["BPP"])

                txr_output.pixel_bytes_list.append(bmp_input.pixel_bytes)
                break

            bmp_color_format = bmp_input.check_color_format()

            # Color Format
            if bmp_input.image_header["BPP"] > 16 or bmp_input.image_header["BPP"] < 8:
                print(image_path)
                raise TypeError("Only 16 bit textures are supported (RGB565, ARGB1555 or ARGB4444) or paletted 8bit")

            subtexture_texture_header = dict.copy(txr_output.texture_header)

            if bmp_input.image_header["Compression"] == 0:
                subtexture_texture_header["Color Format"] = 2
            elif bmp_input.image_header["Compression"] == 3:
                if bmp_color_format == "RGB565":
                    subtexture_texture_header["Color Format"] = 0
                elif bmp_color_format == "ARGB1555":
                    subtexture_texture_header["Color Format"] = 2
                elif bmp_color_format == "ARGB4444":
                    subtexture_texture_header["Color Format"] = 8
                else:
                    raise TypeError("Incorrect color format, save BMP as RGB565, ARGB1555 or ARGB4444")
            else:
                raise TypeError("Incorrect compression")

            # If palette is present in BMP
            if len(bmp_input.color_table_bytes) > 0:
                subtexture_texture_header["Palette Usage"] = 4  # 4 means palette is used
                txr_output.add_palette(bmp_input.color_table_bytes)
                subtexture_texture_header["Palette Used"] = txr_output.palette_list.index(bmp_input.color_table_bytes) + 1

            subtexture_texture_header["Image Width"] = bmp_input.image_header["Image Width"]
            subtexture_texture_header["Image Size (in bytes)"] = len(bmp_input.pixel_bytes)

            if bmp_input.image_header["Image Height"] > 0:
                bmp_input.pixel_bytes = flip_pixel_bytes_vertically(bmp_input.pixel_bytes,
                                                                    bmp_input.image_header["Image Width"],
                                                                    abs(bmp_input.image_header["Image Height"]),
                                                                    bmp_input.image_header["BPP"])

            txr_output.add_texture(subtexture_texture_header, bmp_input.pixel_bytes)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if os.path.isdir(output_path):
            output_texture_path = bmp_group.replace(input_path, output_path)
        elif output_path == "":
            output_texture_path = bmp_group
        else:
            output_texture_path = output_path

        txr_output.save(output_texture_path)
        print("Saved " + output_texture_path)


# SR2Tools-converted BMP have correct color formats, so you can just use check_color_format with them
# PNG
# RGB565   - if all alpha channels are 255 or if there is no alpha channel
# ARGB1555 - if alpha channel values are only either 255 or 0
# ARGB4444 - else
def guessColorFormatfromPNG(png_path):
    unpacked_png = Image.open(png_path)
    png_array = numpy.asarray(unpacked_png)
    channel_count = png_array.shape[2]

    if channel_count == 3:
        return "RGB565"

    alpha_array = png_array[:, :, 3]

    min_alpha_value = numpy.min(alpha_array)

    if min_alpha_value == 255:
        return "RGB565"

    max_alpha_value = numpy.max(alpha_array)

    if min_alpha_value != 0 or max_alpha_value != 255:
        return "ARGB4444"

    if True in ((alpha_array > 0) & (alpha_array < 255)):
        return "ARGB4444"
    else:
        return "ARGB1555"


def flip_pixel_bytes_vertically(pixel_bytes, image_width, image_height, bpp):
    image_line_byte_size = (image_width * bpp) // 8
    flipped_pixel_bytes = b''.join(reversed([pixel_bytes[i:i + image_line_byte_size] for i in range(0, (image_width*image_height*bpp)//8, image_line_byte_size)]))
    return flipped_pixel_bytes


def flip_pixel_bytes_horizontally(pixel_bytes, image_width, image_height, bpp):
    flipped_pixel_bytes = b''.join(reversed([pixel_bytes[i:i + 2] for i in range(0, len(pixel_bytes), 2)]))
    return flipped_pixel_bytes
