# Example script on how to use code interface
import os.path
from texture_tool import *


def unpackBINDATAtextures(bindata_folder, bindata_output_folder, png_export=False):
    file_list = []
    # Scan all included folders
    for path, subdirs, files in os.walk(bindata_folder):
        for name in files:
            file_list.append(os.path.join(path, name))
            # print(os.path.join(path, name))

    # Convert all texture files and save at a different folder
    for file_path in file_list:
        if os.path.isfile(file_path):
            # print(file_path)
            convertTXRtoBMP(file_path, bindata_output_folder, png_export)


def packBINDATAtextures(unpacked_bindata_folder, pack_textures_to_folder, png_input=False):
    folder_list = []

    for path, subdirs, files in os.walk(unpacked_bindata_folder):
        folder_list.append(path)
        # print(path)

    for input_folder in folder_list:
        output_folder = input_folder.replace(unpacked_bindata_folder, pack_textures_to_folder)
        # print(output_folder)
        os.makedirs(os.path.dirname(output_folder), exist_ok=True)
        convertBMPtoTXR(input_folder + '/', output_folder + '/', png_input)

# Unpack all texture from the entire game directory and put them at bindata_output_folder (with folders)
# To unpack as PNG change png_export=False to png_export=True
bindata_folder = "./BINDATA/"
bindata_output_folder = "./Extracted BINDATA bmp/"
# unpackBINDATAtextures(bindata_folder, bindata_output_folder, png_export=False)

# Repack extracted textures
# To pack PNGs instead of BMPs change png_input=False to png_input=True
unpacked_bindata_folder = "./Extracted BINDATA bmp/"
pack_textures_to_folder = "./Packed BINDATA bmp/"
# packBINDATAtextures(unpacked_bindata_folder, pack_textures_to_folder, png_input=False)
