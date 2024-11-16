# Classes of SR2 texture formats
import struct
from bmp_handler import *

def fill_dict_from_bytes_by_format(dictionary: dict, source_bytes: bytes, formatting: str) -> dict:
    value_list = struct.unpack(formatting, source_bytes)
    dictionary = dict(zip(dictionary.keys(), value_list))
    return dictionary

sr2_texture_formats = {
    b"RHBG": {
        "File Header Formatting": "<4s",
        "File Header": {"Signature": b'RHBG'},

        "Texture Header Formatting": "<3I",
        "Texture Header": {
            "Image Width": 0,
            "Image Height": 0,
            "Image Size (in bytes)": 0}},

    b"RTEX": {
        "File Header Formatting":  "<4s2I3Bx",
        "File Header": {
            "Signature": b'RTEX',
            "Texture Count": 0,
            "Palette Count": 0,
            "Palette Index 1": 0,
            "Palette Index 2": 0,
            "Palette Index 3": 0,
            # Padding 1
        },

        "Texture Header Formatting": "<2b2xH2xIB3x",
        "Texture Header": {
            "Color Format": 0,
            "Palette Usage": 0,
            #"No Idea": 0,
            "Image Width": 0,
            "Image Size (in bytes)": 0,
            "Palette Used": 0
        }
    },

    b'RTXR': {
        "File Header Formatting":  "<4sI",
        "File Header": {
            "Signature": b'RTXR',
            "Texture Count": 0,
        },

        "Texture Header Formatting": "<B3x3I",
        "Texture Header": {
            "Color Format": 0,
            "Image Width": 0,
            "Image Height": 0,
            "Image Size (in bytes)": 0
        }
    },

    b'MTEX': {
        "File Header Formatting": "<4sI8x",
        "File Header": {
            "Signature": b'MTEX',
            "Texture Count": 0,
            # Padding 8
        },

        "Texture Header Formatting": "<I2H2I",
        "Texture Header": {
            "Color Format": 0,
            "No Idea": 0,
            "Image Width": 0,
            "Pixel Offset": 0,
            "Image Size (in bytes)": 0,
        }
    }
}


class SR2Texture:

    def __init__(self, file_signature):
        self.texture_format = sr2_texture_formats[file_signature]

        self.file_header = dict.copy(self.texture_format["File Header"])
        self.file_header_formatting = self.texture_format["File Header Formatting"]
        self.file_header_size = struct.calcsize(self.file_header_formatting)

        self.texture_header_list = []
        self.texture_header = dict.copy(self.texture_format["Texture Header"])
        self.texture_header_formatting = self.texture_format["Texture Header Formatting"]
        self.texture_header_size = struct.calcsize(self.texture_header_formatting)

        self.pixel_bytes_list = []

    def pack_and_give(self):
        return b''

    def save(self, output_file_path):
        file_bytes = self.pack_and_give()

        output_file = open(output_file_path, "w+b")
        output_file.write(file_bytes)
        output_file.close()


class RHBG(SR2Texture):
    def __init__(self):
        SR2Texture.__init__(self,  b'RHBG')

    def unpack_from_bytes(self, file_bytes):
        file_header_bytes = file_bytes[:self.file_header_size]

        self.file_header = fill_dict_from_bytes_by_format(self.file_header,
                                                          file_header_bytes,
                                                          self.file_header_formatting)

        texture_header_bytes = file_bytes[self.file_header_size:self.file_header_size + self.texture_header_size]
        texture_specific_header = fill_dict_from_bytes_by_format(self.texture_header,
                                                                 texture_header_bytes,
                                                                 self.texture_header_formatting)

        self.texture_header_list.append(dict.copy(texture_specific_header))

        pyxel_bytes = file_bytes[self.file_header_size + self.texture_header_size:]
        self.pixel_bytes_list.append(pyxel_bytes)

    def unpack_from_file(self, texture_file_path):
        file_bytes = open(texture_file_path, "r+b").read()
        self.unpack_from_bytes(file_bytes)

    def pack_and_give(self):
        file_header_bytes = struct.pack(self.file_header_formatting, *self.file_header.values())
        texture_header_bytes = struct.pack(self.texture_header_formatting, *self.texture_header_list[0].values())
        pixel_bytes = self.pixel_bytes_list[0]

        return file_header_bytes + texture_header_bytes + pixel_bytes

    def setup_bmp(self, texture_id):
        output_bmp = BMP()

        output_bmp.set_resolution(self.texture_header_list[0]["Image Width"],
                                  self.texture_header_list[0]["Image Height"])

        return output_bmp

    def convert_bmp_headers_to_texture_header(self, bmp_input):
        sub_texture_header = dict.copy(self.texture_header)

        sub_texture_header["Image Width"] = bmp_input.image_header["Image Width"]
        sub_texture_header["Image Height"] = bmp_input.image_header["Image Height"]
        sub_texture_header["Image Size (in bytes)"] = len(bmp_input.pixel_bytes)

        # Color Format
        if bmp_input.image_header["BPP"] != 16:
            raise TypeError("Only 16 bit textures are supported (RGB565 format)")

        bmp_color_format = bmp_input.check_color_format()

        match bmp_color_format:
            case "RGB565":
                pass
            case _:
                raise TypeError("Incorrect color format, save BMP as RGB565")

        self.texture_header_list.append(sub_texture_header)


class RTEX(SR2Texture):

    def __init__(self):
        self.palette_list = []
        SR2Texture.__init__(self, b'RTEX')

    def add_palette(self, palette_bytes):

        if not (palette_bytes in self.palette_list):
            # 256 colors, 1024 bytes
            self.palette_list.append(palette_bytes)

        palette_count = len(self.palette_list)

        if palette_count == 1:
            self.file_header["Palette Index 1"] = 1
        if palette_count == 2:
            self.file_header["Palette Index 2"] = 2
        if palette_count == 3:
            self.file_header["Palette Index 3"] = 3

        self.file_header["Palette Count"] = palette_count

    def add_texture(self, texture_header, pixel_bytes):
        self.texture_header_list.append(texture_header)
        self.pixel_bytes_list.append(pixel_bytes)
        self.file_header["Texture Count"] += 1

    def unpack_from_file(self, texture_file_path):
        texture_file = open(texture_file_path, "r+b")

        self.file_header = fill_dict_from_bytes_by_format(self.file_header,
                                                          texture_file.read(self.file_header_size),
                                                          self.file_header_formatting)

        # Fill texture_header_list
        for i in range(self.file_header["Texture Count"]):
            texture_specific_header = fill_dict_from_bytes_by_format(self.texture_header,
                                                                     texture_file.read(self.texture_header_size),
                                                                     self.texture_header_formatting)
            # dict.copy, because python uses a reference when it doesn't need to
            self.texture_header_list.append(dict.copy(texture_specific_header))

        # Fill palette_list
        palette_count = self.file_header["Palette Count"]
        if palette_count > 0:
            palette_size = 1024
            for i in range(0, palette_count):
                self.palette_list.append(texture_file.read(palette_size))

            if palette_count >= 2:
                self.file_header["Palette Index 1"] = 1
                self.file_header["Palette Index 2"] = 2
            if palette_count == 3:
                self.file_header["Palette Index 3"] = 3

        # Fill pixel_bytes_list
        pixel_data_offset = 0x1000
        texture_file.seek(pixel_data_offset)
        for texture_header in self.texture_header_list:
            texture_bytes = texture_file.read(texture_header["Image Size (in bytes)"])
            self.pixel_bytes_list.append(texture_bytes)

    def pack_and_give(self):

        file_header_bytes = struct.pack(self.file_header_formatting,*self.file_header.values())

        texture_header_bytes = b''
        for texture_header in self.texture_header_list:
            texture_header_bytes += struct.pack(self.texture_header_formatting, *texture_header.values())

        palette_bytes = b''
        for palette in self.palette_list:
            palette_bytes += palette

        padding_needed = 0x1000 - len(file_header_bytes + texture_header_bytes + palette_bytes)
        padding_bytes = struct.pack(str(padding_needed) + "x")

        all_pixel_bytes = b''
        for pixel_bytes in self.pixel_bytes_list:
            all_pixel_bytes += pixel_bytes

        return file_header_bytes + texture_header_bytes + palette_bytes + padding_bytes + all_pixel_bytes

    def setup_bmp(self, texture_id):
        current_subtexture_header = self.texture_header_list[texture_id]
        output_bmp = BMP()

        output_bmp.set_resolution(current_subtexture_header["Image Width"], current_subtexture_header["Image Width"])

        output_bmp.image_header["BPP"] = 16
        if current_subtexture_header["Color Format"] == 2:
            output_bmp.swapColorFormat("ARGB1555")
        elif current_subtexture_header["Color Format"] == 8:
            output_bmp.swapColorFormat("ARGB4444")
        else:
            output_bmp.swapColorFormat("RGB565")

        if current_subtexture_header["Palette Usage"] == 4:
            output_bmp.image_header["BPP"] = 8
            output_bmp.image_header["Color Count"] = 256

            if len(self.palette_list) > 1:
                palette = self.palette_list[current_subtexture_header["Palette Used"] - 1]
            else:
                palette = self.palette_list[0]

            output_bmp.color_table_bytes = palette

        return output_bmp

    def convert_bmp_headers_to_texture_header(self, bmp_input):
        sub_texture_header = dict.copy(self.texture_header)

        sub_texture_header["Image Width"] = bmp_input.image_header["Image Width"]
        sub_texture_header["Image Size (in bytes)"] = len(bmp_input.pixel_bytes)

        # Color Format
        if bmp_input.image_header["BPP"] > 16 or bmp_input.image_header["BPP"] < 8:
            raise TypeError("Only 16 bit textures are supported (RGB565, ARGB1555 or ARGB4444)")

        bmp_color_format = bmp_input.check_color_format()

        match bmp_color_format:
            case "RGB565":
                sub_texture_header["Color Format"] = 0
            case "ARGB1555":
                sub_texture_header["Color Format"] = 2
            case "ARGB4444":
                sub_texture_header["Color Format"] = 8
            case _:
                raise TypeError("Incorrect color format, save BMP as RGB565, ARGB1555 or ARGB4444")

        # Palette Usage
        if len(bmp_input.color_table_bytes) > 0:
            sub_texture_header["Palette Usage"] = 4  # 4 means palette is used

            if not (bmp_input.color_table_bytes in self.palette_list):
                self.palette_list.append(bmp_input.color_table_bytes)
            sub_texture_header["Palette Used"] = self.palette_list.index(bmp_input.color_table_bytes) + 1

        return sub_texture_header


class MTEX(SR2Texture):

    def __init__(self):
        self.tile_list = []
        self.index_list = []
        self.index_counter = 0  # For correct tile unpacking
        SR2Texture.__init__(self,b'MTEX')

    def add_palette(self, palette_bytes):
        pass

    def add_texture(self, generic_texture_header, pixel_bytes):
        self.texture_header_list.append(generic_texture_header)
        self.pixel_bytes_list.append(pixel_bytes)
        self.file_header["Texture Count"] += 1

    def unpack_from_file(self, texture_file_path):
        texture_file = open(texture_file_path, "r+b")

        self.file_header = fill_dict_from_bytes_by_format(self.file_header,
                                                          texture_file.read(self.file_header_size),
                                                          self.file_header_formatting)
        # print(self.file_header)
        # Fill texture_header_list
        for i in range(self.file_header["Texture Count"]):
            texture_specific_header = fill_dict_from_bytes_by_format(self.texture_header,
                                                                     texture_file.read(self.texture_header_size),
                                                                     self.texture_header_formatting)
            # dict.copy, because python uses a reference when it doesn't need to
            self.texture_header_list.append(dict.copy(texture_specific_header))
            # print(texture_specific_header)

        def fill_tile_indexes(row, column, group_size):
            if group_size > 1:
                group_size = group_size // 2
                fill_tile_indexes(row, column, group_size)  # Top Left
                fill_tile_indexes(row + group_size, column, group_size)  # Bottom Left
                fill_tile_indexes(row, column + group_size, group_size)  # Top Right
                fill_tile_indexes(row + group_size, column + group_size, group_size)  # Bottom Right
            elif group_size == 1:
                unpacked_index_list[row][column] = index_bytes[self.index_counter]
                self.index_counter += 1

        # Fill tile_list and index_list
        pixel_data_offset = 0x1000
        texture_file.seek(pixel_data_offset)
        for texture_header in self.texture_header_list:
            if texture_header["No Idea"] == 0:
                texture_bytes = texture_file.read(texture_header["Image Size (in bytes)"])

                index_size = ((texture_header["Image Width"] // 2) ** 2)
                print(texture_header)
                index_bytes = texture_bytes[-index_size:]
                tile_bytes = texture_bytes[:-index_size]

                split_tile_list = [tile_bytes[index*8:index*8+8] for index in range(len(tile_bytes)//8)]
                print(len(split_tile_list))

                self.tile_list.append(split_tile_list)
                self.index_list.append(index_bytes)

                pixel_bytes = b''
                unpacked_index_list = [[0 for x in range(texture_header["Image Width"] // 2)] for y in range(texture_header["Image Width"] // 2)]
                self.index_counter = 0
                fill_tile_indexes(0, 0, texture_header["Image Width"] // 2)

                # Fill pixel_bytes_list
                for row in unpacked_index_list:
                    print(row)
                    first_line = b''
                    second_line = b''
                    for index in row:
                        first_line += split_tile_list[index][:2] + split_tile_list[index][4:6]
                        second_line += split_tile_list[index][2:4] + split_tile_list[index][6:8]

                    pixel_bytes += first_line
                    pixel_bytes += second_line
            if texture_header["No Idea"] == 1:
                texture_bytes = texture_file.read(texture_header["Image Size (in bytes)"])
                pixel_bytes = texture_bytes

            self.pixel_bytes_list.append(pixel_bytes)

    def pack_and_give(self):

        file_header_bytes = struct.pack(self.file_header_formatting,*self.file_header.values())

        texture_header_bytes = b''
        for texture_header in self.texture_header_list:
            texture_header_bytes += struct.pack(self.texture_header_formatting,*texture_header.values())

        padding_needed = 0x1000 - len(file_header_bytes + texture_header_bytes)
        padding_bytes = struct.pack(str(padding_needed) + "x")

        all_pixel_bytes = b''
        for pixel_bytes in self.pixel_bytes_list:
            all_pixel_bytes += pixel_bytes

        return file_header_bytes + texture_header_bytes + padding_bytes + all_pixel_bytes

    def setup_bmp(self, texture_id):
        current_sub_texture = self.texture_header_list[texture_id]
        output_bmp = BMP()

        output_bmp.image_header["BPP"] = 16
        if (current_sub_texture["Color Format"] & 0b00001111) == 2:
            output_bmp.swapColorFormat("ARGB1555")
        elif (current_sub_texture["Color Format"] & 0b00001111) == 8:
            output_bmp.swapColorFormat("ARGB4444")
        else:
            output_bmp.swapColorFormat("RGB565")

        return output_bmp

    def convert_bmp_headers_to_texture_header(self, bmp_input):
        raise LookupError("MTEX textures can't be exported from bmps")
        sub_texture_header = dict.copy(self.texture_header)

        sub_texture_header["Image Width"] = bmp_input.image_header["Image Width"]
        sub_texture_header["Image Size (in bytes)"] = len(bmp_input.pixel_bytes)

        # Color Format
        if bmp_input.image_header["BPP"] > 16:
            raise TypeError("Only 16 bit textures are supported (RGB565, ARGB1555 or ARGB4444)")

        bmp_color_format = bmp_input.check_color_format()

        match bmp_color_format:
            case "RGB565":
                sub_texture_header["Color Format"] = 0
            case "ARGB1555":
                sub_texture_header["Color Format"] = 2
            case "ARGB4444":
                sub_texture_header["Color Format"] = 8
            case _:
                raise TypeError("Incorrect color format, save BMP as RGB565, ARGB1555 or ARGB4444")

        return sub_texture_header


class RTXR(SR2Texture):
    def __init__(self):
        # Uses unknown compression
        SR2Texture.__init__(self, b'RTXR')

    def unpack_from_file(self, texture_file_path):
        texture_file = open(texture_file_path, "r+b")

        self.file_header = fill_dict_from_bytes_by_format(self.file_header,
                                                          texture_file.read(self.file_header_size),
                                                          self.file_header_formatting)
        print(self.file_header)
        # Fill texture_header_list and pixel_bytes_list
        for i in range(self.file_header["Texture Count"]):
            texture_header = fill_dict_from_bytes_by_format(self.texture_header,
                                                            texture_file.read(self.texture_header_size),
                                                            self.texture_header_formatting)
            # dict.copy, because python uses a reference when it doesn't need to
            self.texture_header_list.append(dict.copy(texture_header))
            print(texture_header)

            texture_bytes = texture_file.read(texture_header["Image Size (in bytes)"])
            self.pixel_bytes_list.append(texture_bytes)

    def pack_and_give(self):

        file_header_bytes = struct.pack(self.file_header_formatting, *self.file_header.values())

        texture_header_and_pixel_bytes = b''
        for i in range(len(self.texture_header_list)):
            texture_header_and_pixel_bytes += struct.pack(self.texture_header_formatting,
                                                          *self.texture_header_list[i].values())
            texture_header_and_pixel_bytes += self.pixel_bytes_list[i]

        return file_header_bytes + texture_header_and_pixel_bytes
