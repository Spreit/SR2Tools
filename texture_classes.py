"""
Python classes for handling Sega Rally 2 textures
"""
import struct
from bmp_handler import BMPv5
from unyakuza import unyakuza


def fill_dict_from_bytes_by_formatting(dictionary_to_fill: dict, source_bytes: bytes, formatting: str) -> dict:
    value_list = struct.unpack(formatting, source_bytes)
    dictionary_to_fill = dict(zip(dictionary_to_fill.keys(), value_list))
    return dictionary_to_fill


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

    def fill_file_header_from_bytes(self, texture_file_bytes):
        file_header_bytes = texture_file_bytes[:self.file_header_size]

        self.file_header = fill_dict_from_bytes_by_formatting(self.file_header,
                                                              file_header_bytes,
                                                              self.file_header_formatting)

    def fill_texture_headers_from_bytes(self, texture_file_bytes):

        if self.file_header["Signature"] == b'RHBG':
            texture_count = 1
        else:
            texture_count = self.file_header["Texture Count"]

        all_texture_header_bytes = texture_file_bytes[self.file_header_size:
                                                      self.file_header_size + texture_count * self.texture_header_size]

        # Fill texture_header_list
        for i in range(texture_count):
            texture_header_bytes = all_texture_header_bytes[i * self.texture_header_size:
                                                            i * self.texture_header_size + self.texture_header_size]

            texture_header = fill_dict_from_bytes_by_formatting(self.texture_header,
                                                                texture_header_bytes,
                                                                self.texture_header_formatting)
            # dict.copy, because python uses a reference when it doesn't need to
            self.texture_header_list.append(dict.copy(texture_header))

    def fill_pixel_bytes_list(self, texture_file_bytes):

        if self.file_header["Signature"] == b'RHBG':
            pixel_bytes_offset = 0x0010
        else:
            pixel_bytes_offset = 0x1000

        for texture_header in self.texture_header_list:
            texture_bytes = texture_file_bytes[pixel_bytes_offset:
                                               pixel_bytes_offset + texture_header["Image Size (in bytes)"]]
            self.pixel_bytes_list.append(texture_bytes)
            pixel_bytes_offset += texture_header["Image Size (in bytes)"]

    def unpack_from_file(self, texture_file_path):
        texture_file = open(texture_file_path, "r+b")
        texture_file_bytes = texture_file.read()
        texture_file.close()
        self.unpack_from_bytes(texture_file_bytes)

    def pack_file_header(self) -> bytes:
        return struct.pack(self.file_header_formatting, *self.file_header.values())

    def pack_texture_headers(self):
        texture_header_bytes = b''
        for texture_header in self.texture_header_list:
            texture_header_bytes += struct.pack(self.texture_header_formatting, *texture_header.values())
        return texture_header_bytes

    def pack_palette_bytes(self):
        palette_bytes = b''
        for palette in self.palette_list:
            palette_bytes += palette
        return palette_bytes

    def pack_padding(self):
        if self.file_header["Signature"] == b"RHBG":
            return b''

        full_header_size_without_padding = self.file_header_size + self.texture_header_size * self.file_header["Texture Count"]

        try:
            full_header_size_without_padding += len(self.palette_list) * 1024
        except:
            pass

        padding_needed = 0x1000 - full_header_size_without_padding

        padding_bytes = struct.pack(str(padding_needed) + "x")
        return padding_bytes

    def pack_pixel_bytes(self):
        all_pixel_bytes = b''
        for pixel_bytes in self.pixel_bytes_list:
            all_pixel_bytes += pixel_bytes
        return all_pixel_bytes

    def pack_and_return(self):
        return b''

    def save(self, output_file_path):
        file_bytes = self.pack_and_return()

        output_file = open(output_file_path, "w+b")
        output_file.write(file_bytes)
        output_file.close()


class RHBG(SR2Texture):
    def __init__(self):
        SR2Texture.__init__(self,  b'RHBG')

    def unpack_from_bytes(self, texture_file_bytes):
        self.fill_file_header_from_bytes(texture_file_bytes)
        self.fill_texture_headers_from_bytes(texture_file_bytes)
        self.fill_pixel_bytes_list(texture_file_bytes)

    def pack_and_return(self):
        file_header_bytes = self.pack_file_header()
        texture_header_bytes = self.pack_texture_headers()
        pixel_bytes = self.pixel_bytes_list[0]

        return file_header_bytes + texture_header_bytes + pixel_bytes

    def setup_bmp(self, texture_id):
        output_bmp = BMPv5()

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

        if bmp_color_format != "RGB565":
            raise TypeError("Incorrect color format, save BMP as RGB565")

        self.texture_header_list.append(sub_texture_header)


class RTEX(SR2Texture):

    def __init__(self):
        SR2Texture.__init__(self, b'RTEX')

        self.palette_list = []

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

    def RTEX_fill_palette_list_from_bytes(self, texture_file_bytes):
        PALETTE_SIZE = 1024
        palette_count = self.file_header["Palette Count"]

        if palette_count > 0:
            palette_offset = self.file_header_size + self.texture_header_size * self.file_header["Texture Count"]

            for i in range(0, palette_count):
                self.palette_list.append(texture_file_bytes[palette_offset + i * PALETTE_SIZE:
                                                            palette_offset + i * PALETTE_SIZE + PALETTE_SIZE])

            if palette_count >= 1:
                self.file_header["Palette Index 1"] = 1
            if palette_count >= 2:
                self.file_header["Palette Index 2"] = 2
            if palette_count == 3:
                self.file_header["Palette Index 3"] = 3

    def unpack_from_bytes(self, texture_file_bytes):
        self.fill_file_header_from_bytes(texture_file_bytes)
        self.fill_texture_headers_from_bytes(texture_file_bytes)
        self.RTEX_fill_palette_list_from_bytes(texture_file_bytes)
        self.fill_pixel_bytes_list(texture_file_bytes)

    def pack_and_return(self):
        file_header_bytes = self.pack_file_header()
        all_texture_header_bytes = self.pack_texture_headers()
        all_palette_bytes = self.pack_palette_bytes()
        padding_bytes = self.pack_padding()

        all_pixel_bytes = self.pack_pixel_bytes()

        return file_header_bytes + all_texture_header_bytes + all_palette_bytes + padding_bytes + all_pixel_bytes

    def setup_bmp(self, texture_id):
        current_subtexture_header = self.texture_header_list[texture_id]
        output_bmp = BMPv5()

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


def unyakuza_subtexture(subtexture_bytes) -> bytes:
    # Mini header
    compression_header = subtexture_bytes[:16]

    if int.from_bytes(compression_header[:4], "little") == 1:
        uncompressed_size = int.from_bytes(compression_header[4:8], "little")
        compressed_size = int.from_bytes(compression_header[8:12], "little")

        subtexture_bytes = unyakuza(subtexture_bytes[16:], compressed_size - 16, uncompressed_size)
        subtexture_bytes = bytes(subtexture_bytes)

    return subtexture_bytes


class MTEX(SR2Texture):

    def __init__(self):
        SR2Texture.__init__(self, b'MTEX')

        self.tile_list = []
        self.index_list = []
        self.palette_list = []

        self.index_counter = 0  # For correct tile unpacking
        self.unpacked_index_list = []

    def MTEX_add_palette_if_present(self, full_header_bytes):
        for texture_header in self.texture_header_list:
            if texture_header["Color Format"] > 1024 and len(self.palette_list) == 0:
                palette_bytes = full_header_bytes[0x400:0x800]
                self.palette_list.append(palette_bytes)
                break

    def untwiddle_flat_index_list_into_unpacked_index_list(self, row, column, group_size):
        if group_size > 1:
            group_size = group_size // 2
            self.untwiddle_flat_index_list_into_unpacked_index_list(row, column, group_size)  # Top Left
            self.untwiddle_flat_index_list_into_unpacked_index_list(row + group_size, column, group_size)  # Bottom Left
            self.untwiddle_flat_index_list_into_unpacked_index_list(row, column + group_size, group_size)  # Top Right
            self.untwiddle_flat_index_list_into_unpacked_index_list(row + group_size, column + group_size, group_size)  # Bottom Right
        elif group_size == 1:
            self.unpacked_index_list[row][column] = self.index_list[self.index_counter]
            self.index_counter += 1

    # (Un)Twiddling
    def assemble_paletted_pixel_bytes(self):
        pixel_bytes = b''

        for row in self.unpacked_index_list:
            for index in row:
                pixel_bytes += index.to_bytes(1, "little")

        return pixel_bytes

    def assemble_pixel_bytes_from_tiles(self, individual_tile_list):
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

    def MTEX_split_pixel_bytes_by_sizes_in_header(self, texture_file_bytes):
        subtexture_data_offset = 0x1000
        for texture_header in self.texture_header_list:
            if texture_header["Pixel Offset"] != 0:
                subtexture_data_offset = texture_header["Pixel Offset"]

            subtexture_bytes = texture_file_bytes[subtexture_data_offset:
                                                  subtexture_data_offset + texture_header["Image Size (in bytes)"]]

            subtexture_data_offset += texture_header["Image Size (in bytes)"]

            self.pixel_bytes_list.append(subtexture_bytes)

    def uncompress_compressed_texture_bytes(self):
        for texture_index in range(len(self.texture_header_list)):
            # This trims first 16 bytes, since they are an "archive" header
            if self.texture_header_list[texture_index]["Compressed"] == 1:
                self.pixel_bytes_list[texture_index] = unyakuza_subtexture(self.pixel_bytes_list[texture_index])

    def unpack_from_bytes(self, texture_file_bytes):
        self.fill_file_header_from_bytes(texture_file_bytes[:self.texture_header_size])
        self.fill_texture_headers_from_bytes(texture_file_bytes[:0x1000])
        self.MTEX_add_palette_if_present(texture_file_bytes[:0x1000])

        # Just split the sub texture bytes
        self.MTEX_split_pixel_bytes_by_sizes_in_header(texture_file_bytes)

        self.uncompress_compressed_texture_bytes()

        # Untwiddle, untile. Idk, make it presentable
        for sub_texture_index in range(len(self.texture_header_list)):

            texture_header = self.texture_header_list[sub_texture_index]

            twiddled = ((texture_header["Color Format"] & 0b11110000) >> 4)
            twiddled = (twiddled == 2) or (twiddled == 8)

            paletted = texture_header["Color Format"] > 1024

            subtexture_bytes = self.pixel_bytes_list[sub_texture_index]

            complete_texture_size = texture_header["Image Width"] * texture_header["Image Width"] * 2

            # Fill tile_list and index_list
            if paletted:
                # No tiles, palette indexes in their place
                self.index_list = list.copy([subtexture_bytes[index] for index in range(len(subtexture_bytes))])
                tile_bytes = subtexture_bytes
            elif len(subtexture_bytes) == complete_texture_size:
                # If it's just compressed, then every 2x2 fragment is a tile and go in sequential order
                index_amount = (texture_header["Image Width"] // 2) ** 2
                self.index_list = list.copy([i for i in range(index_amount)])
                tile_bytes = subtexture_bytes
            else:
                # Regular 256 2x2 tile compression
                index_bytes_size = ((texture_header["Image Width"] // 2) ** 2)
                index_bytes = subtexture_bytes[-index_bytes_size:]
                self.index_list = list.copy([index_bytes[i] for i in range(index_bytes_size)])
                tile_bytes = subtexture_bytes[:-index_bytes_size]

            if twiddled:

                if paletted:
                    unpack_index_list_size = texture_header["Image Width"]
                else:
                    unpack_index_list_size = texture_header["Image Width"] // 2

                self.unpacked_index_list = [[0 for x in range(unpack_index_list_size)]
                                               for y in range(unpack_index_list_size)]

                self.index_counter = 0
                self.untwiddle_flat_index_list_into_unpacked_index_list(0, 0, unpack_index_list_size)

                if paletted:
                    pixel_bytes = self.assemble_paletted_pixel_bytes()
                else:
                    # Split tile_bytes into individual 2x2 16 bit tiles
                    individual_tile_list = [tile_bytes[index * 8:index * 8 + 8] for index in range(len(tile_bytes) // 8)]

                    self.tile_list.append(individual_tile_list)

                    pixel_bytes = self.assemble_pixel_bytes_from_tiles(individual_tile_list)
            else:
                # Simply compressed and not twiddled, then it's done
                pixel_bytes = subtexture_bytes

            self.pixel_bytes_list[sub_texture_index] = pixel_bytes

    def add_texture(self, generic_texture_header, pixel_bytes):
        self.texture_header_list.append(generic_texture_header)
        self.pixel_bytes_list.append(pixel_bytes)
        self.file_header["Texture Count"] += 1

    def pack_and_return(self):
        file_header_bytes = self.pack_file_header()
        texture_header_bytes = self.pack_texture_headers()
        padding_bytes = self.pack_padding()

        all_pixel_bytes = self.pack_pixel_bytes()

        return file_header_bytes + texture_header_bytes + padding_bytes + all_pixel_bytes

    def setup_bmp(self, texture_id):
        current_subtexture_header = self.texture_header_list[texture_id]
        output_bmp = BMPv5()

        output_bmp.set_resolution(current_subtexture_header["Image Width"],
                                  current_subtexture_header["Image Width"])

        paletted = current_subtexture_header["Color Format"] > 1024

        actual_color_format = (current_subtexture_header["Color Format"] & 0b00001111)

        if not paletted:
            output_bmp.image_header["BPP"] = 16
            if actual_color_format == 2:
                output_bmp.swapColorFormat("ARGB1555")
            elif actual_color_format == 8:
                output_bmp.swapColorFormat("ARGB4444")
            else:
                output_bmp.swapColorFormat("RGB565")

            # For one of few textures that needs this exception
            if current_subtexture_header["Color Format"] == 0:
                output_bmp.swapColorFormat("ARGB1555")
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
        SR2Texture.__init__(self, b'RTXR')
        # Uses unknown compression

    def uncompress_pixel_bytes(self):
        pass

    def unpack_from_bytes(self, texture_file_bytes):
        self.fill_file_header_from_bytes(texture_file_bytes)

        texture_offset = self.file_header_size
        # Fill texture_header_list and pixel_bytes_list
        for i in range(self.file_header["Texture Count"]):
            texture_header = fill_dict_from_bytes_by_formatting(self.texture_header,
                                                                texture_file_bytes[texture_offset:
                                                                                   texture_offset + self.texture_header_size],
                                                                self.texture_header_formatting)
            # dict.copy, because python uses a reference when it doesn't need to
            self.texture_header_list.append(dict.copy(texture_header))
            print(texture_header)

            texture_offset += self.texture_header_size

            texture_bytes = texture_file_bytes[texture_offset:
                                               texture_offset + texture_header["Image Size (in bytes)"]]
            self.pixel_bytes_list.append(texture_bytes)

            texture_offset += texture_header["Image Size (in bytes)"]

    def pack_and_return(self):
        # Texture Header and Compressed Pixel Bytes are stored in pairs

        file_header_bytes = struct.pack(self.file_header_formatting, *self.file_header.values())

        texture_header_and_pixel_bytes = b''
        for i in range(len(self.texture_header_list)):
            texture_header_bytes = struct.pack(self.texture_header_formatting,
                                                          *self.texture_header_list[i].values())
            compressed_pixel_bytes = self.pixel_bytes_list[i]

            texture_header_and_pixel_bytes += (texture_header_bytes + compressed_pixel_bytes)

        return file_header_bytes + texture_header_and_pixel_bytes
