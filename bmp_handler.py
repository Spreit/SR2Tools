# BMP Class
import struct

BITMAPFILEHEADER = {
    "Signature": b'BM',
    "File Size": 0,  # image_size + header_size
    "Reserved1": 0,
    "Offset to PixelArray": 0  # header_size
}

BITMAPV5HEADER = {
    "DIB Header Size": 124,
    "Image Width": 0,
    "Image Height": 0,
    "Planes": 1,  # Always 1. 2 bytes
    "BPP": 16,  # 2 bytes
    "Compression": 3,  # 0 - BI_RGB, 3 - BI_BITMAP

    "Image Size": 1,
    "X Pixels Per Meter": 0,
    "Y Pixels Per Meter": 0,
    "Color Count": 0,
    "Important Colors": 0,

    "R Bitmask": 0b1111100000000000,  # 63488
    "G Bitmask": 0b0000011111100000,  # 2016
    "B Bitmask": 0b0000000000011111,  # 31
    "A Bitmask": 0b0000000000000000,

    "Color Space Type": b'BGRs',
    #"Color Space Endpoints": 0,  # 36 bytes, no idea what it does
    "R Gamma": 1,
    "G Gamma": 0,
    "B Gamma": 0,
    "Intent": 2,

    "ICC Profile Data": 0,
    "ICC Profile Size": 0,
    "Reserved2": 0,
}

ColorTable = {
    "Color0": [b'00F0', 4],
    "Color1": [b'E000', 4],
    "Color15": [b'0000', 4],
    "Color16": [b'E000', 4]
}


def fill_dict_from_bytes_by_format(dictionary: dict, source_bytes: bytes, formatting: str) -> dict:
    value_list = struct.unpack(formatting, source_bytes)
    dictionary = dict(zip(dictionary.keys(), value_list))
    return dictionary


class BMP:
    def __init__(self):
        # Header structure
        self.file_header_size = 14
        self.bmp_file_header_format = "<2s3I"  # 14

        self.image_header_size = 124
        self.bmp_image_header_format = "<2Ii2hI" + "I2i2I" + "4I" + "4s36x4I" + "3I"  # 124

        # Content
        self.file_header = dict.copy(BITMAPFILEHEADER)
        self.image_header = dict.copy(BITMAPV5HEADER)
        self.color_table_bytes = b''
        self.pixel_bytes = b''

        self.update_file_size_and_pixel_offset()

    def set_resolution(self, image_width, image_height):
        self.image_header["Image Width"] = image_width
        self.image_header["Image Height"] = image_height

        self.image_header["X Pixels Per Meter"] = image_width
        self.image_header["Y Pixels Per Meter"] = image_height

    def check_color_format(self):
        if self.image_header["Compression"] == 0:
            if self.image_header["BPP"] <= 8:
                return "Palette"
            elif self.image_header["BPP"] == 24:
                return "RGB888"
            elif self.image_header["BPP"] == 32:
                return "ARGB8888"
            else:
                return "Other"
        elif self.image_header["Compression"] == 3:
            if self.image_header["BPP"] == 32:
                return "ARGB8888"
            if self.image_header["R Bitmask"] == 0b1111100000000000 \
                    and self.image_header["G Bitmask"] == 0b0000011111100000 \
                    and self.image_header["B Bitmask"] == 0b0000000000011111 \
                    and self.image_header["A Bitmask"] == 0b0000000000000000:
                return "RGB565"
            elif self.image_header["R Bitmask"] == 0b0111110000000000 \
                    and self.image_header["G Bitmask"] == 0b0000001111100000 \
                    and self.image_header["B Bitmask"] == 0b0000000000011111 \
                    and self.image_header["A Bitmask"] == 0b1000000000000000:
                return "ARGB1555"
            elif self.image_header["R Bitmask"] == 0b0000111100000000 \
                    and self.image_header["G Bitmask"] == 0b0000000011110000 \
                    and self.image_header["B Bitmask"] == 0b0000000000001111 \
                    and self.image_header["A Bitmask"] == 0b1111000000000000:
                return "ARGB4444"
            else:
                return "Other"

    def update_file_size_and_pixel_offset(self):
        self.file_header["File Size"] = (self.file_header_size
                                         + self.image_header_size
                                         + len(self.color_table_bytes)
                                         + len(self.pixel_bytes))

        self.file_header["Offset to PixelArray"] = (self.file_header_size
                                                    + self.image_header_size
                                                    + len(self.color_table_bytes))

    def swapColorFormat(self, color_format):
        if color_format == "RGB565":
            self.image_header["R Bitmask"] = 0b1111100000000000
            self.image_header["G Bitmask"] = 0b0000011111100000
            self.image_header["B Bitmask"] = 0b0000000000011111
            self.image_header["A Bitmask"] = 0b0000000000000000
        elif color_format == "ARGB1555":
            self.image_header["R Bitmask"] = 0b0111110000000000
            self.image_header["G Bitmask"] = 0b0000001111100000
            self.image_header["B Bitmask"] = 0b0000000000011111
            self.image_header["A Bitmask"] = 0b1000000000000000
        elif color_format == "ARGB4444":
            self.image_header["R Bitmask"] = 0b0000111100000000
            self.image_header["G Bitmask"] = 0b0000000011110000
            self.image_header["B Bitmask"] = 0b0000000000001111
            self.image_header["A Bitmask"] = 0b1111000000000000
        else:
            raise ValueError("Incorrect BMP Color Format")

    def unpack_from_bytes(self, bitmap_bytes):

        self.file_header = fill_dict_from_bytes_by_format(self.file_header,
                                                          bitmap_bytes[:self.file_header_size],
                                                          self.bmp_file_header_format)

        self.image_header = fill_dict_from_bytes_by_format(self.image_header,
                                                           bitmap_bytes[self.file_header_size:self.file_header_size + self.image_header_size],
                                                           self.bmp_image_header_format)

        # Read palette if present
        if self.file_header["Offset to PixelArray"] - (self.file_header_size + self.image_header_size) > 0:
            self.color_table_bytes = bitmap_bytes[self.file_header_size + self.image_header_size:self.file_header["Offset to PixelArray"]]

        self.pixel_bytes = bitmap_bytes[self.file_header["Offset to PixelArray"]:]

    def unpack_from_file(self, bitmap_path: str):
        bitmap_file = open(bitmap_path, "r+b")
        bitmap_bytes = bitmap_file.read()
        self.unpack_from_bytes(bitmap_bytes)
        bitmap_file.close()

    def pack_and_give(self):
        self.update_file_size_and_pixel_offset()

        file_header_bytes = struct.pack(self.bmp_file_header_format, *list(self.file_header.values()))
        image_header_bytes = struct.pack(self.bmp_image_header_format, *list(self.image_header.values()))

        return file_header_bytes + image_header_bytes + self.color_table_bytes + self.pixel_bytes

    def save(self, output_path):
        bin_data = self.pack_and_give()

        output_file = open(output_path, "w+b")
        output_file.write(bin_data)
        output_file.close()
