# SARC archives are used in the Dreamcast port of the game under .bin file extension, usually for cars
import struct

sarc_file_header_format = "<4sI"
sarc_file_header = {
    "Signature": b"SARC",
    "File Count": 0
}

sarc_packed_file_header_format = "<4xIII256s"
sarc_packed_file_header = {
    "File Size": 0,
    "File Size 2": 0,
    "File Offset": 0,
    "File Path": ""
}


class SARC:
    def __init__(self):
        self.file_header = {}
        self.packed_file_header_list = []
        self.file_bytes_list = []

    def unpack_from_bytes(self, sarc_bytes):
        if sarc_bytes[:4] != b"SARC":
            raise ValueError("Input file is not a SARC archive")

        file_header_values = struct.unpack(sarc_file_header_format, sarc_bytes[:8])
        self.file_header = dict(zip(sarc_file_header.keys(), file_header_values))

        # print(self.file_header)

        for i in range(self.file_header["File Count"]):
            packed_file_header_values = struct.unpack(sarc_packed_file_header_format,
                                                      sarc_bytes[8 + i * 272: 8 + 272 + i * 272])
            packed_file_header = dict(zip(sarc_packed_file_header.keys(), packed_file_header_values))
            self.packed_file_header_list.append(packed_file_header)

            file_offset = packed_file_header["File Offset"]
            file_size = packed_file_header["File Size"]
            file_bytes = sarc_bytes[file_offset:file_offset + file_size]

            self.file_bytes_list.append(file_bytes)

    def unpack_from_file(self, path_to_sarc):
        sarc_bytes = open(path_to_sarc, "r+b").read()
        self.unpack_from_bytes(sarc_bytes)

    def save_files_to_folder(self, output_folder):
        for i in range(self.file_header["File Count"]):
            file_path = self.packed_file_header_list[i]["File Path"]  # 255 bytes
            file_name = file_path[:file_path.find(b'\x00')]  # Remove the padding at the end
            file_name = file_name.decode("cp932")  # Decode text
            file_name = file_name[file_name.rfind('\\') + 1:]  # Keep only the name of the file

            file_bytes = self.file_bytes_list[i]

            output_file = open(output_folder + file_name, "w+b")
            output_file.write(file_bytes)

            print("Saved " + output_folder + file_name)


def extract_sarc(input_archive_path, output_folder):
    sarc_archive = SARC()
    sarc_archive.unpack_from_file(input_archive_path)
    sarc_archive.save_files_to_folder(output_folder)

