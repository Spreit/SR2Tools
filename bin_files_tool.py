import os
import texture_classes
import struct

# unpackBINtofolder
# Change a model/texture
# packfoldertoBIN
# Patch the new file sizes in Sega Rally 2.exe and MSelect.dll with exe_dll_patcher.py
#

#   BIN file types
# Have file sizes in first 4 bytes
# MDL, ASCII

# Need special treatment
# SARC
# RTEX
# RTXR

# Implies the use of 25th anniversary version
EXE_address_list = {
    "B_ASCII.BIN" : 0xB1550,  # No idea what it does
    "B_CARMDL.BIN": 0xB1640,  # Menu car models
    "B_CARTEX.BIN": 0xB1730,  # Menu car texture
    "B_REFMDL.BIN": 0xB1820   # Menu car reflection model
}

MSELECT_address_list = {
    "B_CARMDL.BIN": 0xB75A0,  # Menu car models
    "B_CARTEX.BIN": 0xB7690,  # Menu car texture
    "B_REFMDL.BIN": 0xB7780   # Menu car reflection model
}

# Of course, it's different from their order inside B_CARMDL.BIN, why wouldn't it be?
Car_order = [
    0, 1, 26, 2, 3, 4, 5, 6, 7, 8, 9,
    10, 11, 12, 13, 14, 15, 16, -1, 17, 18, 19,
    20, 21, 22, 23, -1, 24, 25, -1
]
# 30 car slots


class BIN:

    def __init__(self):
        self.archive_type = ""
        self.file_byte_list = []

    def detectBINfiletype(self, first4bytes: bytes):
        if first4bytes == b'RTEX':
            return "RTEX"
        elif first4bytes == b'RTXR':
            return "RTXR"
        elif first4bytes == b'MTEX':
            return "MTEX"
        elif first4bytes == b'SARC':
            return "SARC"
        else:
            return "MDL/Other"

    def split_RTEX(self, bin_file_bytes):
        bin_file_size = len(bin_file_bytes)

        texture_file_offset = 0x0
        while texture_file_offset < bin_file_size:
            # Unpack function won't read past the correct size
            texture = texture_classes.RTEX()
            texture.unpack_from_bytes(bin_file_bytes[texture_file_offset:])

            full_texture_file_size = 0x1000  # Full header size
            for texture_header in texture.texture_header_list:
                full_texture_file_size += texture_header["Image Size (in bytes)"]

            packed_texture_bytes = bin_file_bytes[texture_file_offset:texture_file_offset + full_texture_file_size]

            self.file_byte_list.append(packed_texture_bytes)

            texture_file_offset += full_texture_file_size

            # print(full_texture_file_size)

    def split_RTXR(self, bin_file_bytes):
        pass

    def split_MTEX(self, bin_file_bytes):
        pass

    def split_SARC(self, bin_file_bytes):
        pass

    def split_MDL_or_by_size(self, bin_file_bytes):
        bin_file_size = len(bin_file_bytes)
        file_offset = 0x0000

        while file_offset < bin_file_size:
            size_of_packed_file = int.from_bytes(bin_file_bytes[file_offset:file_offset + 4], "little")
            packed_file_bytes = bin_file_bytes[file_offset:file_offset + size_of_packed_file]
            self.file_byte_list.append(packed_file_bytes)

            file_offset += size_of_packed_file

            # No BIN file will realistically have more than 100 files, so it's here as an infinite loop prevention
            if len(self.file_byte_list) > 100:
                raise OverflowError("The BIN file you tried opening is not valid")
                break

    def make_size_list(self):
        # Fill as is
        file_size_list = [len(file_bytes) for file_bytes in self.file_byte_list]
        # print(file_size_list)
        sum_size_list = []

        previous_size = 0
        for file_size in file_size_list:
            sum_size_list.append(previous_size)
            previous_size += file_size

        # print(sum_size_list)

        # Reorder to what the game expects
        index_counter = 0
        size_table = [placeholder_number for placeholder_number in range(30*2)]
        for place in Car_order:

            if place != -1:
                size_table[index_counter] = sum_size_list[place]
                size_table[index_counter + 1] = file_size_list[place]
            else:
                size_table[index_counter] = 0
                size_table[index_counter + 1] = 0

            index_counter += 2

        return size_table

    def make_size_list_bytes(self):
        size_list = self.make_size_list()
        return b''.join([size.to_bytes(4, "little") for size in size_list])

    def unpack_from_bytes(self, bin_file_bytes):
        first4bytes = bin_file_bytes[:4]

        self.archive_type = self.detectBINfiletype(first4bytes)

        if self.archive_type == "RTEX":
            self.split_RTEX(bin_file_bytes)
        elif self.archive_type == "RTXR":
            self.split_RTXR(bin_file_bytes)
        elif self.archive_type == "MTEX":
            self.split_MTEX(bin_file_bytes)
        elif self.archive_type == "SARC":
            self.split_SARC(bin_file_bytes)
        else:
            self.split_MDL_or_by_size(bin_file_bytes)

    def unpack_from_file(self, bin_file_path):
        bin_file = open(bin_file_path, "rb")
        bin_file_bytes = bin_file.read()
        self.unpack_from_bytes(bin_file_bytes)

    def pack_and_give(self):
        # Does BIN specifically add padding at the end to fit 16 bit row?
        return b''.join(self.file_byte_list)

    def save(self, output_path):
        new_bin_file = open(output_path, "w+b")
        new_bin_file.write(self.pack_and_give())
        new_bin_file.close()


def unpackBINtofolder(bin_input_path, output_folder):
    bin_file = BIN()
    bin_file.unpack_from_file(bin_input_path)

    bin_file_title = bin_input_path[bin_input_path.rfind("/") + 1:]

    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    print(bin_file_title)

    file_type = bin_file.detectBINfiletype(bin_file.file_byte_list[0][:4])
    if file_type == "RTEX" or file_type == "RTXR" or file_type == "MTEX":
        file_extension = "TXR"
    else:
        file_extension = "MDL"

    for file_index in range(len(bin_file.file_byte_list)):
        current_file_bytes = bin_file.file_byte_list[file_index]

        new_model_path = output_folder + str(file_index) + "." + bin_file_title[:-3] + file_extension

        print("Saved ", new_model_path)

        with open(new_model_path, "w+b") as new_file:
            new_file.write(current_file_bytes)


# Provide a folder of X.NAME.EXT files
def packfoldertoBIN(unpacked_bin_folder, file_extension, output_bin_path):
    input_folder_list = os.listdir(unpacked_bin_folder)

    new_bin_list = []
    for file_name in input_folder_list:
        if file_name[- len(file_extension):] == file_extension:
            new_bin_list.append(unpacked_bin_folder + file_name)

    # Numbers before the file name allow packing in correct order
    new_bin_list = sorted(new_bin_list, key=len)

    new_binmdl_bytes = b''
    for model_path in new_bin_list:
        with open(model_path, "r+b") as file:
            model_bytes = file.read()
            new_binmdl_bytes += model_bytes

        print("File size", len(model_bytes))

    new_binmdl_file = open(output_bin_path, "w+b")
    new_binmdl_file.write(new_binmdl_bytes)
    new_binmdl_file.close()

    print("Saved ", output_bin_path)


if __name__ == "__main__":
    # size_test()
    unpackBINtofolder("./binpacks/MDL/B_CARMDL.BIN","./binpacks/MDL/B_CARMDL/")

    packfoldertoBIN("./binpacks/MDL/B_CARMDL/", ".MDL", "./binpacks/MDL/new B_CARMDL.BIN")
