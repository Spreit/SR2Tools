# Classes of SR2 texture formats
import struct
from bmp_handler import *
from unyakuza import uncompress_SR2_subtexture

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
            "Compressed": 0,  # 0 - as is, 1 - Yakuza'ed
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

    def unpack_from_bytes(self, texture_file_bytes):
        pass

    def unpack_from_file(self, texture_file_path):
        texture_file = open(texture_file_path, "r+b")
        texture_file_bytes = texture_file.read()
        texture_file.close()
        self.unpack_from_bytes(texture_file_bytes)

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
        self.file_header_size = 16
        self.subtexture_header_size = 16
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

    def fill_file_header_from_bytes(self, texture_file_bytes):
        file_header_bytes = texture_file_bytes[:self.file_header_size]
        self.file_header = fill_dict_from_bytes_by_format(self.file_header,
                                                          file_header_bytes,
                                                          self.file_header_formatting)

    def fill_subtexture_header_list_from_bytes(self, texture_file_bytes):
        subtexture_header_list_bytes = texture_file_bytes[self.file_header_size:
                                                          self.file_header_size
                                                          + self.file_header["Texture Count"] * self.subtexture_header_size]
        # Fill texture_header_list
        for i in range(self.file_header["Texture Count"]):
            subtexture_header_bytes = subtexture_header_list_bytes[i*self.subtexture_header_size:
                                                                   i*self.subtexture_header_size + self.subtexture_header_size]
            subtexture_header = fill_dict_from_bytes_by_format(self.texture_header,
                                                               subtexture_header_bytes,
                                                               self.texture_header_formatting)
            # dict.copy, because python uses a reference when it doesn't need to
            self.texture_header_list.append(dict.copy(subtexture_header))

    def unpack_from_bytes(self, texture_file_bytes):

        self.fill_file_header_from_bytes(texture_file_bytes)
        self.fill_subtexture_header_list_from_bytes(texture_file_bytes)

        # Fill palette_list
        palette_count = self.file_header["Palette Count"]
        if palette_count > 0:
            palette_offset = self.file_header_size + self.subtexture_header_size * self.file_header["Texture Count"]

            palette_size = 1024
            for i in range(0, palette_count):
                self.palette_list.append(texture_file_bytes[palette_offset + i * palette_size:
                                                            palette_offset + i * palette_size + palette_size])

            if palette_count >= 1:
                self.file_header["Palette Index 1"] = 1
            if palette_count >= 2:
                self.file_header["Palette Index 2"] = 2
            if palette_count == 3:
                self.file_header["Palette Index 3"] = 3

        # Fill pixel_bytes_list
        pixel_bytes_offset = 0x1000
        for texture_header in self.texture_header_list:
            texture_bytes = texture_file_bytes[pixel_bytes_offset:
                                               pixel_bytes_offset + texture_header["Image Size (in bytes)"]]
            self.pixel_bytes_list.append(texture_bytes)
            pixel_bytes_offset += texture_header["Image Size (in bytes)"]

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

        output_bmp.set_resolution(current_subtexture_header["Image Width"],
                                  current_subtexture_header["Image Width"])

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
        self.palette_list = []
        self.index_counter = 0  # For correct tile unpacking
        SR2Texture.__init__(self, b'MTEX')

    def add_palette_if_present(self, full_header_bytes):
        for texture_header in self.texture_header_list:
            if texture_header["Color Format"] > 1024 and len(self.palette_list) == 0:
                palette_bytes = full_header_bytes[0x400:0x800]
                self.palette_list.append(palette_bytes)
                break

    def add_texture(self, generic_texture_header, pixel_bytes):
        self.texture_header_list.append(generic_texture_header)
        self.pixel_bytes_list.append(pixel_bytes)
        self.file_header["Texture Count"] += 1

    def unpack_from_bytes(self, texture_file_bytes):

        file_header_bytes = texture_file_bytes[:self.file_header_size]
        self.file_header = fill_dict_from_bytes_by_format(self.file_header,
                                                          file_header_bytes,
                                                          self.file_header_formatting)

        texture_headers_offset = self.file_header_size
        # Fill texture_header_list
        for i in range(self.file_header["Texture Count"]):
            subtexture_header_bytes = texture_file_bytes[texture_headers_offset:
                                                         texture_headers_offset + self.texture_header_size]

            subtexture_header = fill_dict_from_bytes_by_format(self.texture_header,
                                                               subtexture_header_bytes,
                                                               self.texture_header_formatting)
            # dict.copy, because python uses a reference when it doesn't need to
            self.texture_header_list.append(dict.copy(subtexture_header))

            texture_headers_offset += self.texture_header_size

        self.add_palette_if_present(texture_file_bytes[:0x1000])

        # print(self.texture_header_list)
        subtexture_data_offset = 0x1000
        for texture_header in self.texture_header_list:

            if texture_header["Pixel Offset"] != 0:
                subtexture_data_offset = texture_header["Pixel Offset"]

            subtexture_bytes = texture_file_bytes[subtexture_data_offset:
                                                  subtexture_data_offset + texture_header["Image Size (in bytes)"]]

            complete_texture_size = (texture_header["Image Width"] * texture_header["Image Width"] * 16) // 8
            unyakuzaed_size = int.from_bytes(subtexture_bytes[4:8], "little")

            # This trims first 16 bytes, since they are an "archive" header
            if texture_header["Compressed"] == 1:
                subtexture_bytes = uncompress_SR2_subtexture(subtexture_bytes)

            paletted = texture_header["Color Format"] > 1024

            #print(texture_header)

            # Fill tile_list and index_list
            if paletted:
                # No tiles, palette indexes in their place
                self.flat_index_list = list.copy([subtexture_bytes[index] for index in range(len(subtexture_bytes))])
                tile_bytes = subtexture_bytes
            elif unyakuzaed_size == complete_texture_size:
                # If it's just compressed, then every 2x2 fragment is a tile and go in sequential order
                index_amount = (texture_header["Image Width"] // 2) ** 2
                self.flat_index_list = list.copy([i for i in range(index_amount)])
                tile_bytes = subtexture_bytes
            else:
                # If uses tile compression
                index_bytes_size = ((texture_header["Image Width"] // 2) ** 2)
                index_bytes = subtexture_bytes[-index_bytes_size:]
                self.flat_index_list = list.copy([index_bytes[i] for i in range(index_bytes_size)])
                tile_bytes = subtexture_bytes[:-index_bytes_size]

            self.unpacked_index_list = [[0 for x in range(texture_header["Image Width"] // 2)] for y in
                                        range(texture_header["Image Width"] // 2)]

            if paletted:
                pixel_bytes = self.assemble_paletted_pixel_bytes(texture_header)
            else:
                # Split tile_bytes into individual 2x2 16 bit tiles
                individual_tile_list = [tile_bytes[index * 8:index * 8 + 8] for index in range(len(tile_bytes) // 8)]

                self.tile_list.append(individual_tile_list)
                self.index_list.append(self.flat_index_list)

                pixel_bytes = self.assemble_pixel_bytes_from_tiles(texture_header, individual_tile_list)

            subtexture_data_offset += texture_header["Image Size (in bytes)"]

            self.pixel_bytes_list.append(pixel_bytes)

    # (Un)Twiddling
    def untwiddle_flat_index_list_into_unpacked_index_list(self, row, column, group_size):
        if group_size > 1:
            group_size = group_size // 2
            self.untwiddle_flat_index_list_into_unpacked_index_list(row, column, group_size)  # Top Left
            self.untwiddle_flat_index_list_into_unpacked_index_list(row + group_size, column, group_size)  # Bottom Left
            self.untwiddle_flat_index_list_into_unpacked_index_list(row, column + group_size, group_size)  # Top Right
            self.untwiddle_flat_index_list_into_unpacked_index_list(row + group_size, column + group_size, group_size)  # Bottom Right
        elif group_size == 1:
            self.unpacked_index_list[row][column] = self.flat_index_list[self.index_counter]
            self.index_counter += 1

    def assemble_paletted_pixel_bytes(self, texture_header):

        self.unpacked_index_list = [[0 for x in range(texture_header["Image Width"])] for y in
                                    range(texture_header["Image Width"])]

        self.index_counter = 0
        self.untwiddle_flat_index_list_into_unpacked_index_list(0, 0, texture_header["Image Width"])

        pixel_bytes = b''
        # Fill pixel_bytes_list
        for row in self.unpacked_index_list:
            for index in row:
                pixel_bytes += index.to_bytes(1, "little")

        return pixel_bytes

    def assemble_pixel_bytes_from_tiles(self, texture_header, individual_tile_list):

        self.index_counter = 0
        self.untwiddle_flat_index_list_into_unpacked_index_list(0, 0, texture_header["Image Width"] // 2)

        pixel_bytes = b''
        # Fill pixel_bytes_list
        for row in self.unpacked_index_list:
            # print(row)
            first_line = b''
            second_line = b''
            for index in row:
                first_line += individual_tile_list[index][:2] + individual_tile_list[index][4:6]
                second_line += individual_tile_list[index][2:4] + individual_tile_list[index][6:8]

            pixel_bytes += first_line
            pixel_bytes += second_line

        return pixel_bytes

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
        current_subtexture_header = self.texture_header_list[texture_id]
        output_bmp = BMP()

        output_bmp.set_resolution(current_subtexture_header["Image Width"],
                                  current_subtexture_header["Image Width"])

        paletted = current_subtexture_header["Color Format"] > 1024

        if not paletted:
            output_bmp.image_header["BPP"] = 16
            if (current_subtexture_header["Color Format"] & 0b00001111) == 2:
                output_bmp.swapColorFormat("ARGB1555")
            elif (current_subtexture_header["Color Format"] & 0b00001111) == 8:
                output_bmp.swapColorFormat("ARGB4444")
            else:
                output_bmp.swapColorFormat("RGB565")
        else:
            output_bmp.color_table_bytes = self.palette_list[0]
            output_bmp.image_header["BPP"] = 8
            output_bmp.image_header["Color Count"] = 256

        return output_bmp

    def convert_bmp_headers_to_texture_header(self, bmp_input):
        raise LookupError("MTEX textures can't be made from bmps")
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

    def uncompress_pixel_bytes(self):
        pass

    def unpack_from_bytes(self, texture_file_bytes):

        self.file_header = fill_dict_from_bytes_by_format(self.file_header,
                                                          texture_file_bytes[self.file_header_size:],
                                                          self.file_header_formatting)

        print(self.file_header)
        texture_offset = self.file_header_size
        # Fill texture_header_list and pixel_bytes_list
        for i in range(self.file_header["Texture Count"]):
            texture_header = fill_dict_from_bytes_by_format(self.texture_header,
                                                            texture_file_bytes[texture_offset:
                                                                               texture_offset+self.texture_header_size],
                                                            self.texture_header_formatting)
            # dict.copy, because python uses a reference when it doesn't need to
            self.texture_header_list.append(dict.copy(texture_header))
            print(texture_header)

            texture_offset += self.texture_header_size

            texture_bytes = texture_file_bytes[texture_offset:
                                               texture_offset + texture_header["Image Size (in bytes)"]]
            self.pixel_bytes_list.append(texture_bytes)

            texture_offset += texture_header["Image Size (in bytes)"]

    def pack_and_give(self):
        # Texture Header and Compressed Pixel Bytes are stored in pairs

        file_header_bytes = struct.pack(self.file_header_formatting, *self.file_header.values())

        texture_header_and_pixel_bytes = b''
        for i in range(len(self.texture_header_list)):
            texture_header_bytes = struct.pack(self.texture_header_formatting,
                                                          *self.texture_header_list[i].values())
            compressed_pixel_bytes = self.pixel_bytes_list[i]

            texture_header_and_pixel_bytes += (texture_header_bytes + compressed_pixel_bytes)

        return file_header_bytes + texture_header_and_pixel_bytes
