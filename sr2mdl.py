import struct
import array
import io
import math
import mathutils

import bmesh
import bpy

from bpy.props import (StringProperty,
                       PointerProperty,
                       )

from bpy.types import (Panel,
                       PropertyGroup,
                       )

bl_info = {
    "name": "Sega Rally 2 MDL importer/exporter",
    "description": "Allows editing of Sega Rally 2 models",
    "author": "Spreit, chmcl95",
    "version": (0, 0, 6),
    "blender": (4, 0, 0),
    "category": "Import-Export",
}


def fill_dict_from_bytes_by_formatting(dictionary_to_fill: dict, source_bytes: bytes, formatting: str) -> dict:
    value_list = struct.unpack(formatting, source_bytes)
    dictionary_to_fill = dict(zip(dictionary_to_fill.keys(), value_list))
    return dictionary_to_fill


"""
When you install/run the script, a side panel will appear (where Item, Tool, View, etc are)

SR2MDL and relevant classes handle MDL file unpacking and packing.
load and generate_mesh functions turn unpacked data into a Blender collection with nodes and meshes.
Blender collection and its Nodes have Custom Properties that store necessary data.

Save function
- Makes a new SR2MDL
- Takes Blender collection
- Fill SR2MDL with data from collection
- SR2MDL packs the data and saves it
"""


"""
    TODO
- Refactor code

? Redo the way additional data is shared between Blender and SR2MDL and SR2Node
? Make Blender object heirarchy in the same way they are in node.relation? 

    Missing
- Update Node Scale and Position when saving
- Material representation?
- Special Node Handling (some MDL may not open)

    Usability
- Add import button to Blender import submenu

    Textures
- Auto load textures, if present
- Auto flip the texture

    QOL
- Flip UVs for easy editing
- Rotate entire model on load. Pivot at the world origin
- Scale X axis of all parts by -1 to have correct texture display
(Don't forget to undo the above while saving)

- Load entire car folder

- Figure out how to open levels
"""


SR2MDL_file_header_dict = {
    "File Size": 0,
    "Header Size": 0x20,
    "Relation Offset": 0,
    "Road count": 0,

    "Unk2": 0,
    "Unk3": 0,
    "Unk4": 0,
    "Unk5": 0,
}

SR2MDL_material = {
    # Color 0
    "R0": 0,
    "G0": 0,
    "B0": 0,
    "A0": 0,

    # Color 1
    "R1": 0,
    "G1": 0,
    "B1": 0,
    "A1": 0,

    "unk_0x08": 0.0,
    "unk_0x0C": 0.0,
    "unk_0x10": 0.0,

    "unk_0x14": 0.0,
    "unk_0x18": 0.0,
    "unk_0x1C": 0.0,
}

SR2MDL_vertex = {
    "Position": [0.0, 0.0, 0.0],
    "Normal": [0.0, 0.0, 0.0],
    "UV": [0.0, 0.0]
}

SR2MDL_model_pointers = {
    "Vertex Offset": 0,
    "Face Offset": 0,
    "Material Offset": 0,

    "Vertex Count": 0,
    "Face Count": 0,
    "Material Count": 0,
    "unk_0x18": 0,
    "unk_0x1C": 0,
}

SR2MDL_draw_options = {
    "unk_0x00": 0,
    "unk_0x04": 0,

    "unk_0x08": 0.0,
    "unk_0x0C": 0.0,
    "unk_0x10": 0.0,
    "unk_0x14": 0.0,

    "unk_0x18": 0,
    "unk_0x1C": 0,
}

SR2MDL_node_transform = {
    "Model Pointers Offset": 0,
    "Draw Options Offset": 0,
    "Node Index": 0,
    "unk_0x0C": 0.0,

    "unk_0x10": 0.0,
    "unk_0x14": 0.0,
    "unk_0x18": 0.0,
    "unk_0x1C": 0.0,

    "Position X": 0.0,
    "Position Y": 0.0,
    "Position Z": 0.0,
    "unk_0x2C": 0,

    "Rotation X": 0,
    "unk_0x32": 0,
    "Rotation Y": 0,
    "unk_0x36": 0,
    "Rotation Z": 0,
    "unk_0x3A": 0,
    "unk_0x3C": 0,

    "Scale X": 0.0,
    "Scale Y": 0.0,
    "Scale Z": 0.0,
    "unk_0x4C": 0,

    "unk_0x50": 0,
    "unk_0x54": 0,
    "unk_0x58": 0,
    "unk_0x5C": 0,
}

SR2MDL_node_relation = {
    "Parent Offset": 0,
    "Child Offset": 0,
    "unk_0x08": 0,
    "unk_0x0C ": 0,

    "unk_0x10 ": 0,
    "unk_0x14 ": 0,
    "unk_0x18 ": 0,
    "unk_0x1C ": 0,
}

SR2MDL_Road = {
    "Index": 0,
    "Node Offset": 0,
    "Unk_2": 0,
    "Unk_3": 0,

    "Unk_4": 0,
    "Unk_5": 0,
    "Unk_6": 0,
    "Unk_7": 0,

    "Unk_8": 0,
    "Unk_9": 0,
    "Unk_10": 0,
    "Unk_11": 0,

    "Unk_12": 0,
    "Unk_13": 0,
    "Unk_14": 0,
    "Unk_15": 0,

    "Unk_16": 0,
    "Unk_17": 0,
    "Unk_18": 0,
    "Unk_19": 0,

    "Unk_20": 0,
    "Unk_21": 0,
    "Unk_22": 0,
    "Unk_23": 0,
}


class Vertex:
    format = '<8f'
    
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.uv = [0.0, 0.0]

    def unpack_from_float_bytes(self, eight_floats_in_bytes):
        float_list = struct.unpack_from(self.format, eight_floats_in_bytes, 0)

        self.position = [float_list[0], float_list[1], float_list[2]]
        self.normal = [float_list[3], float_list[4], float_list[5]]
        self.uv = [float_list[6], float_list[7]]


class Mesh:
    material_format = "<8B" + "6f"
    format_face = '<{0}h'
    format_model_pointers = '<8I'
    draw_options_format = '<2I' + '4f' + '2I'
    
    def __init__(self):
        self.offset = 0
        self.total_size = 0

        self.material = {}
        self.vertexes = []
        self.faces = []
        self.model_pointers = {}
        self.draw_options = {}

        # Used for packing
        self.sizes = {
            "Material": 0x20,
            "Vertex": 0,
            "Face": 0,
            "ModelPointers": 0x20,
            "DrawOptions": 0x20
        }

    def update_sizes(self):
        vertex_size = len(self.vertexes) * 4 * 8

        # Add padding to face size, so it would be aligned to 32-bytes
        face_size = len(self.faces) * 2
        if face_size % 32 != 0:
            face_size = (((face_size//32) + 1) * 32)

        self.sizes["Vertex"] = vertex_size
        self.sizes["Face"] = face_size

        self.total_size = 0x20 + vertex_size + face_size + 0x20 + 0x20

    """ Unpacking """

    def unpack_material_from_bytes(self, full_model_file_bytes, material_offset):
        if self.model_pointers["Material Count"] > 1:
            print("!!! MULTIPLE MATERIALS PRESENT !!!... or the data was read incorrectly")

        material_size_in_bytes = self.model_pointers["Material Count"] * 0x20
        material_bytes = full_model_file_bytes[material_offset:
                                               material_offset + material_size_in_bytes]

        self.material = fill_dict_from_bytes_by_formatting(SR2MDL_material,
                                                           material_bytes,
                                                           self.material_format)

    def unpack_vertexes_from_bytes(self, full_model_file_bytes, vertex_offset, vertex_count):
        # One vertex contains 8 floats (3 position, 3 normal, 2 uv)
        vertex_size_in_bytes = 32  # 4*3 + 4*3 + 4*2
        vertex_array_size_in_bytes = vertex_count * vertex_size_in_bytes

        if vertex_offset > 0 and vertex_offset != 0xffffff:
            vertex_bytes = full_model_file_bytes[vertex_offset:
                                                 vertex_offset + vertex_array_size_in_bytes]

            for vertex_index in range(0, vertex_count):
                vertex = Vertex()
                current_vertex_offset = vertex_index * vertex_size_in_bytes
                vertex.unpack_from_float_bytes(vertex_bytes[current_vertex_offset:
                                                            current_vertex_offset + vertex_size_in_bytes])
                self.vertexes.append(vertex)

    def unpack_faces_from_bytes(self, full_model_file_bytes, face_offset, face_count):
        # A face (triangle) is defined by 3 vertices. Vertex index is only 2 bytes long
        one_face_size_in_bytes = 6  # 2*3
        face_array_size_in_bytes = face_count * one_face_size_in_bytes

        face_bytes = full_model_file_bytes[face_offset:
                                           face_offset + face_array_size_in_bytes]

        fmt_faces = self.format_face.format(face_count)
        self.faces = struct.unpack_from(fmt_faces, face_bytes, 0)

    def unpack_model_pointers_from_bytes(self, full_model_file_bytes, model_pointer_offset):
        model_pointers_size_in_bytes = 0x20
        model_pointers_bytes = full_model_file_bytes[model_pointer_offset:
                                                     model_pointer_offset + model_pointers_size_in_bytes]

        self.model_pointers = fill_dict_from_bytes_by_formatting(SR2MDL_model_pointers,
                                                                 model_pointers_bytes,
                                                                 self.format_model_pointers)

    def unpack_draw_options_from_bytes(self, full_model_file_bytes, draw_options_offset):
        draw_option_size_in_bytes = 0x20

        draw_option_bytes = full_model_file_bytes[draw_options_offset:
                                                  draw_options_offset + draw_option_size_in_bytes]

        self.draw_options = fill_dict_from_bytes_by_formatting(SR2MDL_draw_options,
                                                               draw_option_bytes,
                                                               self.draw_options_format)

    def unpack_from_bytes(self, full_model_file_bytes, model_pointer_offset):
        """
        Material
        Vertex[]
        Face[]
        ModelPointers
        DrawOptions
        """
        # Unpack Model Pointers first because it has offsets to other things
        self.unpack_model_pointers_from_bytes(full_model_file_bytes, model_pointer_offset)

        self.unpack_material_from_bytes(full_model_file_bytes, self.model_pointers["Material Offset"])

        self.unpack_vertexes_from_bytes(full_model_file_bytes,
                                        self.model_pointers["Vertex Offset"],
                                        self.model_pointers["Vertex Count"])

        self.unpack_faces_from_bytes(full_model_file_bytes,
                                     self.model_pointers["Face Offset"],
                                     self.model_pointers["Face Count"])
        # Unpack Draw Options
        model_pointers_size_in_bytes = 0x20
        self.unpack_draw_options_from_bytes(full_model_file_bytes,
                                            model_pointer_offset + model_pointers_size_in_bytes)

    """ Packing """

    def pack_material(self) -> bytes:
        return struct.pack(self.material_format, *self.material.values())

    def pack_vertexes(self) -> bytes:
        vertex_bytes = b''

        for vertex in self.vertexes:
            position_bytes = struct.pack("<3f", *vertex.position)
            normal_bytes = struct.pack("<3f", *vertex.normal)
            uv_bytes = struct.pack("<2f", *vertex.uv)

            vertex_bytes += position_bytes + normal_bytes + uv_bytes

        return vertex_bytes

    def pack_faces(self) -> bytes:
        # Faces need to be packed with 32-byte alignment
        face_format_with_amount = self.format_face.format(len(self.faces))
        face_bytes = struct.pack(face_format_with_amount, *self.faces)

        face_bytes_size_in_bytes = len(face_bytes)

        if face_bytes_size_in_bytes % 32 != 0:
            total_size_needed = (((face_bytes_size_in_bytes//32) + 1) * 32)
            padding_needed = total_size_needed - face_bytes_size_in_bytes

            face_bytes += struct.pack("{}x".format(padding_needed))

        return face_bytes

    def pack_model_pointers(self):
        return struct.pack(self.format_model_pointers, *self.model_pointers.values())

    def pack_draw_options(self):
        return struct.pack(self.draw_options_format, *self.draw_options.values())

    def pack_and_return(self):
        """
            Model
        Material
        Vertex[]
        Face[]
        ModelPointer
        DrawOption
        """
        self.update_sizes()

        material_bytes = self.pack_material()
        vertex_bytes = self.pack_vertexes()
        faces_bytes = self.pack_faces()
        model_pointers_bytes = self.pack_model_pointers()
        draw_options_bytes = self.pack_draw_options()

        return material_bytes + vertex_bytes + faces_bytes + model_pointers_bytes + draw_options_bytes


some_data = {
    "0": 0.0,
    "1": 0.0,
    "2": 0.0,
    "3": 0.0,

    "4": 0.0,
    "5": 0.0,
    "6": 0.0,
    "7": 0.0,
}


class SomeData:
    format = '<8f'

    def __init__(self):
        self.data = dict.copy(some_data)

    def unpack_from_bytes(self, data_bytes, offset):

        some_data_bytes = data_bytes[offset:
                                     offset + 0x20]

        self.data = fill_dict_from_bytes_by_formatting(self.data,
                                                       some_data_bytes,
                                                       self.format)

    def pack_and_return(self):
        return struct.pack(self.format, *self.data.values())


SR2Node_extra = {
        "Offset": 0,
        "Relation Offset": 0,
        "Index": 0,
        "Parent Index": -1,
        "Child Index": -1
}


class SR2Node:
    format_transform = '<3I' + '5f' + '3f' + '1I' + '6H' + '1I' + '3f' + '5I'
    format_relation = '<8I'

    format = '<4I' + '4f' + '3f' + '5I' + '3f' + "5I" + '8I'
    #  4I  4f   4f    4f     3f     20x    8I'
    # 0-3, 4-7, 8-11, 12-15, 16-18, 19-29, 30-38

    def __init__(self):
        self.node_transform_size = 0x60
        self.node_relation_size = 0x20

        self.transform = {}
        self.relation = {}
        self.some_data = {}

        self.mesh_offset = 0x00
        self.draw_ops_offset = 0x00

        self.position = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.scale = [0, 0, 0]

        # Put these values into a dictionary to be able to store it in the blender file
        self.extra = dict.copy(SR2Node_extra)

        """
        self.offset = 0x00
        self.relation_offset = 0x00

        # Index refers to the position in SR2MDL.nodes
        self.index = 0
        self.parent_index = -1
        self.child_index = -1
        """

    def unpack_from_bytes(self, node_bytes):
        self.transform = fill_dict_from_bytes_by_formatting(SR2MDL_node_transform,
                                                            node_bytes[:self.node_transform_size],
                                                            self.format_transform)

        self.relation = fill_dict_from_bytes_by_formatting(SR2MDL_node_relation,
                                                           node_bytes[self.node_transform_size:],
                                                           self.format_relation)

        self.mesh_offset = self.transform["Model Pointers Offset"]
        self.draw_ops_offset = self.transform["Draw Options Offset"]

        self.position = [self.transform["Position X"],
                         self.transform["Position Y"],
                         self.transform["Position Z"]]
        self.rotation = [self.transform["Rotation X"],
                         self.transform["Rotation Y"],
                         self.transform["Rotation Z"]]
        self.scale = [self.transform["Scale X"],
                      self.transform["Scale Y"],
                      self.transform["Scale Z"]]

    def pack_and_return(self):
        node_transform_bytes = b''

        if self.transform != {}:
            node_transform_bytes = struct.pack(self.format_transform, *self.transform.values())

        node_relation_bytes = struct.pack(self.format_relation, *self.relation.values())

        return node_transform_bytes + node_relation_bytes


class SR2RoadSegment:
    format_road = "<24I"

    def __init__(self):
        self.road = dict.copy(SR2MDL_Road)
        self.road_size = 0x60

    # Included for speed
    def unpack_from_road_bytes(self, road_bytes):
        self.road = fill_dict_from_bytes_by_formatting(self.road,
                                                       road_bytes,
                                                       self.format_road)

    def unpack_from_bytes(self, file_bytes, offset):
        road_bytes = file_bytes[offset, offset + self.road_size]

        self.road = fill_dict_from_bytes_by_formatting(self.road,
                                                       road_bytes,
                                                       self.format_road)


class SR2MDL:
    def __init__(self):
        self.file_header = dict.copy(SR2MDL_file_header_dict)
        self.file_header_formatting = '<8I'
        self.file_header_size = struct.calcsize(self.file_header_formatting)

        self.meshes = []
        self.nodes = []
        self.roads = []

    def fill_file_header_from_bytes(self, model_file_bytes):
        file_header_bytes = model_file_bytes[:self.file_header_size]

        self.file_header = fill_dict_from_bytes_by_formatting(self.file_header,
                                                              file_header_bytes,
                                                              self.file_header_formatting)

    def unpack_level_model_from_bytes(self, model_file_bytes):
        self.fill_file_header_from_bytes(model_file_bytes[:self.file_header_size])

        node_transform_size = 0x60
        node_relation_size = 0x20
        node_size = node_relation_size + node_transform_size

        # Read Road segment and relevant Nodes and then relevant Mesh

        # Read Road segments
        road_count = self.file_header["Road count"]
        road_size_in_bytes = 0x60
        road_offset = self.file_header["Relation Offset"] + 0x20

        # All Road bytes, for speed
        road_bytes_chunk = model_file_bytes[road_offset:
                                            road_offset + road_size_in_bytes * road_count]

        for road_offset_in_chunk in range(0, len(road_bytes_chunk), road_size_in_bytes):
            new_road = SR2RoadSegment()

            road_bytes = road_bytes_chunk[road_offset_in_chunk:
                                          road_offset_in_chunk + road_size_in_bytes]

            new_road.unpack_from_road_bytes(road_bytes)

            self.roads.append(new_road)

        # Read Node that Road references
        # Then Mesh that Node references
        for road in self.roads:
            node_offset = road.road["Node Offset"]
            node_bytes = model_file_bytes[node_offset:
                                          node_offset + node_size]

            new_node = SR2Node()
            new_node.unpack_from_bytes(node_bytes)

            self.nodes.append(new_node)

            new_mesh = Mesh()

            new_mesh.unpack_from_bytes(model_file_bytes, new_node.transform["Model Pointers Offset"])

            self.meshes.append(new_mesh)

    def unpack_from_bytes(self, model_file_bytes):
        self.fill_file_header_from_bytes(model_file_bytes[:self.file_header_size])

        print('File size: {0:#X}'.format(self.file_header["File Size"]))
        print('Node offset: {0:#X}'.format(self.file_header["Relation Offset"]))

        # Check if it's a level file
        if self.file_header["File Size"] > self.file_header["Relation Offset"] + 0x20:
            self.unpack_level_model_from_bytes(model_file_bytes)
            return

        # Unpack node and related mesh
        # 1. Calculate the total size of nodes + mesh
        # 2. Go through each node + mesh and subtract their sizes from the total size
        # 3. Once the total size hits zero, the reading is complete

        node_transform_size = 0x60
        node_relation_size = 0x20
        node_size = node_relation_size + node_transform_size

        total_mesh_node_size = self.file_header["Relation Offset"] + node_relation_size - self.file_header_size

        # Unpack nodes and related mesh, if exist
        # If a node has 0xFFFFFFFF at unk_0x0C, then it doesn't have mesh, but other data

        first_node_relation_offset = self.file_header["Relation Offset"]

        # MDL file header has the first node relation offset
        # Nodes after that are placed before the first one

        bytes_left = total_mesh_node_size
        current_node_relation_offset = first_node_relation_offset

        while bytes_left > 0:
            print("\n")
            print("Total bytes left : {}".format(bytes_left))

            mesh_present = True

            # Unpack node
            node = SR2Node()

            node_bytes = model_file_bytes[current_node_relation_offset - node_transform_size:
                                          current_node_relation_offset - node_transform_size + node_size]
            node.unpack_from_bytes(node_bytes)

            print("unk 0x0C value", node.transform["unk_0x0C"])

            if math.isnan(node.transform["unk_0x0C"]):
                print("Node without Mesh detected")
                mesh_present = False

            node.index = len(self.nodes)  # len(self.nodes) will increase as Nodes are added

            node.extra["Offset"] = current_node_relation_offset - node_transform_size
            node.extra["Relation Offset"] = current_node_relation_offset

            self.nodes.append(node)

            # Go back through the file
            current_node_relation_offset -= node_size
            bytes_left -= node_size

            # Doesn't have mesh attached or something?
            # Still needs to be included or else the game crashes
            if node_size == 0x20:
                continue

            """
            if (math.isnan(node.transform["unk_0x0C"])  # NAN is 0xFFFFFFFF in float
                    and node.transform["unk_0x2C"] == 0x00
                    and node.transform["Rotation X"] == 0x00):
                continue
            """

            if ((node.relation["unk_0x08"] == 1)
                    and node.transform["unk_0x2C"] == 0x00
                    and node.transform["Rotation X"] == 0x00):
                continue

            # Unpack mesh
            if mesh_present:
                mesh_offset = node.mesh_offset

                mesh = Mesh()
                mesh.unpack_from_bytes(model_file_bytes, mesh_offset)
                mesh.update_sizes()

                bytes_left -= mesh.total_size

                self.meshes.append(mesh)

                print("Mesh at {}".format(current_node_relation_offset))
                print("Mesh size: {}".format(mesh.total_size))
            else:
                some_data_size = 0x20
                tmp_some_data = SomeData()

                tmp_some_data.unpack_from_bytes(model_file_bytes, node.transform["Model Pointers Offset"])

                # Attach to node, instead of array like mesh
                node.some_data = tmp_some_data.data

                bytes_left -= some_data_size

            print("Total bytes left after substraction: {}".format(bytes_left))

        self.find_node_index_relations_by_node_relation_offsets()

        for node in self.nodes:
            print("\n")
            print("Node Index", node.transform["Node Index"])
            print("Parent Index", node.extra["Parent Index"])
            print("Child Index", node.extra["Child Index"])

    def find_node_index_relations_by_node_relation_offsets(self):
        # Find Node parent and sibling by index for easy offset calculation
        print("\nFinding Relationships between Nodes")
        for node_index, node in enumerate(self.nodes):
            for check_node_index, check_node in enumerate(self.nodes):
                print("\n")
                print("Parent Offset", self.nodes[node_index].relation["Parent Offset"])
                print("Child Offset", self.nodes[node_index].relation["Child Offset"])
                print("Check Node offset",  check_node.extra["Offset"])

                if check_node.extra["Offset"] == self.nodes[node_index].relation["Parent Offset"]:
                    self.nodes[node_index].extra["Parent Index"] = check_node_index

                if check_node.extra["Offset"] == self.nodes[node_index].relation["Child Offset"]:
                    self.nodes[node_index].extra["Child Index"] = check_node_index

    def unpack_from_file(self, file_path):
        with open(file_path, "r+b") as file:
            file_bytes = file.read()
            self.unpack_from_bytes(file_bytes)

    def calculate_total_node_size(self):
        return len(self.nodes) * 0x80

    def update_sizes(self):
        """
        Header
        Mesh[]
        Node[]
        """

        for mesh in self.meshes:
            mesh.update_sizes()

        total_mesh_size = 0
        for mesh in self.meshes:
            total_mesh_size += mesh.total_size

        total_node_size = self.calculate_total_node_size()

        total_some_data_size = 0

        for node in self.nodes:
            if node.some_data != {}:
                total_some_data_size += 0x20

        total_file_size = self.file_header_size + total_mesh_size + total_some_data_size + total_node_size

        self.file_header["File Size"] = total_file_size

    def update_relation_offset_in_header(self):
        self.update_sizes()

        first_node_relation_offset = self.file_header_size

        for mesh in self.meshes:
            first_node_relation_offset += mesh.total_size

        for node in self.nodes:
            if node.some_data != {}:
                first_node_relation_offset += 0x20

        # Go the end of all nodes and then go back a little
        first_node_relation_offset += self.calculate_total_node_size()
        first_node_relation_offset -= 0x20

        self.file_header["Relation Offset"] = first_node_relation_offset

    def update_model_pointers_offsets(self):
        current_mesh_offset = self.file_header_size
        for mesh in self.meshes:
            mesh.offset = current_mesh_offset

            mesh.model_pointers["Vertex Offset"] = current_mesh_offset + mesh.sizes["Material"]
            mesh.model_pointers["Face Offset"] = current_mesh_offset + mesh.sizes["Material"] + mesh.sizes["Vertex"]
            mesh.model_pointers["Material Offset"] = current_mesh_offset

            current_mesh_offset += mesh.total_size

    def update_node_offset_to_model_pointers(self):
        for node_index in range(len(self.nodes)):
            node = self.nodes[node_index]

            print("Transform", node.transform["unk_0x0C"], float('-nan'))
            if not math.isnan(node.transform["unk_0x0C"]):
                mesh = self.meshes[node_index]

                node.transform["Model Pointers Offset"] = (mesh.offset + mesh.sizes["Material"]
                                                           + mesh.sizes["Vertex"] + mesh.sizes["Face"])
                node.transform["Draw Options Offset"] = node.transform["Model Pointers Offset"] + 0x20

    def update_node_offsets(self):
        self.update_node_offset_to_model_pointers()
        pass

    def update_offsets(self):
        """
            Opening:
        + Record Node address during unpacking
        + Calculate Node index relations based on it

            Saving
        + Update Node's own addresses
        + Update relation addresses based on index relations
        """
        self.update_sizes()

        self.update_relation_offset_in_header()

        self.update_model_pointers_offsets()

        self.update_node_offsets()

        total_mesh_and_header_size = self.file_header_size

        for mesh in self.meshes:
            total_mesh_and_header_size += mesh.total_size

        for node in self.nodes:
            if node.some_data != {}:
                total_mesh_and_header_size += 0x20

        # Node offsets
        new_node_offset = total_mesh_and_header_size

        # Calculate new offset of each node (in reverse order since that's how they are stored)
        node_size = 0x80
        for node_index in range(len(self.nodes) - 1, 0, -1):
            print("New node offset", new_node_offset)
            self.nodes[node_index].extra["Offset"] = new_node_offset
            new_node_offset += node_size

        # Go through each node and fill in new offsets
        print(len(self.nodes))
        for node in self.nodes:
            print("Updating offsets for Node", node.transform["Node Index"], "with offset", node.extra["Offset"])

            parent_index = node.extra["Parent Index"]
            print("Parent Node index", parent_index)

            if node.extra["Parent Index"] != -1:
                print("Previous Parent Offset", node.relation["Parent Offset"])

                node.relation["Parent Offset"] = self.nodes[parent_index].extra["Offset"]

                print("New Parent offset", node.relation["Parent Offset"])

            child_index = node.extra["Child Index"]
            print("Child Node index", child_index)

            if node.extra["Child Index"] != -1:
                print("Previous Child Offset", self.nodes[child_index].extra["Offset"])

                node.relation["Child Offset"] = self.nodes[child_index].extra["Offset"]

                print("New Child offset", node.relation["Child Offset"])

    def pack_file_header(self):
        return struct.pack(self.file_header_formatting, *self.file_header.values())

    def pack_and_return(self):
        self.update_offsets()
        header_bytes = self.pack_file_header()

        mesh_bytes = b''
        for mesh in self.meshes:
            mesh_bytes += mesh.pack_and_return()

        some_data_bytes = b''
        for node in self.nodes:
            if node.some_data != {}:
                some_data_bytes += struct.pack("<8f", *node.some_data.values())

        # Nodes are stored in the reverse order of the list
        node_bytes = b''
        for node in self.nodes:
            node_bytes = node.pack_and_return() + node_bytes

        return header_bytes + mesh_bytes + some_data_bytes + node_bytes

    def save(self, file_path):
        SR2MDL_bytes = self.pack_and_return()

        new_file = open(file_path, "w+b")
        new_file.write(SR2MDL_bytes)
        new_file.close()


def turnSR2MeshIntoBlenderMesh(model_mesh, bl_mesh):
    temp_blender_mesh = bmesh.new()

    # Make an empty blender mesh, fill with vertices and faces
    bl_vertex_array = []

    normals = []
    uvs = []

    for vertex in model_mesh.vertexes:
        bl_vertex = temp_blender_mesh.verts.new(vertex.position)
        bl_vertex_array.append(bl_vertex)
        normals.append(vertex.normal)
        #flip V-coordinate
        flipped_v = -(vertex.uv[1] - 1.0)
        flipped_uv = [ vertex.uv[0], flipped_v ]
        uvs.append(flipped_uv)

    for face_index in range(0, len(model_mesh.faces), 3):
        v0 = bl_vertex_array[model_mesh.faces[face_index]]
        v1 = bl_vertex_array[model_mesh.faces[face_index + 1]]
        v2 = bl_vertex_array[model_mesh.faces[face_index + 2]]
        temp_blender_mesh.faces.new((v0, v1, v2))

    # Transfer all the data to bl_mesh attached to bl_obj
    temp_blender_mesh.to_mesh(bl_mesh)
    temp_blender_mesh.free()

    # If UV doesn't exist, generate new one
    channel_name = "uv0"
    try:
        bl_mesh.uv_layers[channel_name].data
    except Exception:
        bl_mesh.uv_layers.new(name=channel_name)

    for i, loop in enumerate(bl_mesh.loops):
        bl_mesh.uv_layers[channel_name].data[i].uv = uvs[loop.vertex_index]

    # Apply normals
    bl_mesh.normals_split_custom_set_from_vertices(normals)


def generate_mesh(node: SR2Node, model_mesh: Mesh, index: int, global_matrix: mathutils.Matrix, model_collection):
    """ Make an empty Blender object and fill it with extracted MDL data """

    # Make an empty Blender object
    node_name = 'node_{0:04}'.format(index)
    mesh_name = 'mesh_{0:04}'.format(index)

    # Make and apply custom properties to enable saving
    bl_mesh = bpy.data.meshes.new(mesh_name)

    bl_obj = bpy.data.objects.new(node_name, bl_mesh)
    bl_obj["Node Transform"] = node.transform
    bl_obj["Node Relation"] = node.relation

    bl_obj["Extra"] = node.extra

    # Attach all of this to bl_obj instead of bl_mesh to allow copying mesh from other places
    bl_obj["Material"] = model_mesh.material
    bl_obj["Model Pointers"] = model_mesh.model_pointers
    bl_obj["Draw Options"] = model_mesh.draw_options

    model_collection.objects.link(bl_obj)

    # Select the new empty Blender object
    bpy.context.view_layer.objects.active = bl_obj
    bl_obj.select_set(True)
    bl_mesh = bpy.context.object.data

    # Apply Transforms
    euler = mathutils.Euler(mathutils.Vector((node.rotation[0]/0x7FFF*math.pi, node.rotation[1]/0x7FFF*math.pi, node.rotation[2]/0x7FFF*math.pi)), 'XYZ')
    local_mtx = mathutils.Matrix.LocRotScale(node.position, euler, node.scale)
    bl_obj.matrix_local = local_mtx

    turnSR2MeshIntoBlenderMesh(model_mesh, bl_mesh)

    # Switch to Object Mode and Applying Parent of Node Transform
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    inv_mtx = mathutils.Matrix.inverted(global_matrix)
    bpy.context.object.matrix_world = inv_mtx @ bpy.context.object.matrix_world


def load(filepath: str, global_matrix: mathutils.Matrix):
    # Unpack the model, then make Blender object(s) out of it
    SR2_model = SR2MDL()
    SR2_model.unpack_from_file(filepath)

    # Create a collection for the model parts
    if filepath.rfind("/") == -1:
        file_name = filepath[filepath.rfind("\\") + 1:filepath.rfind(".")]
    else:
        file_name = filepath[filepath.rfind("/") + 1:filepath.rfind(".")]

    model_collection = bpy.data.collections.new(name=file_name)
    bpy.context.scene.collection.children.link(model_collection)

    # Attach file header as collection property to support saving
    model_collection["SR2MDL file header"] = SR2_model.file_header

    # Turn every node into a blender object and attach mesh to it, if present
    for index, node in enumerate(SR2_model.nodes):
        if index < len(SR2_model.meshes):
            mdl_mesh = SR2_model.meshes[index]
            generate_mesh(node, mdl_mesh, index, global_matrix, model_collection)
        else:
            node_name = 'node_{0:04}'.format(index)
            bl_obj = bpy.data.objects.new(node_name, None)

            if node.some_data != {}:
                bl_obj["Node Transform"] = node.transform
                bl_obj["Extra"] = node.extra
                bl_obj["Some Data"] = node.some_data

            bl_obj["Node Relation"] = node.relation
            model_collection.objects.link(bl_obj)


def isSR2MDLcollection(blender_collection):
    if isinstance(blender_collection, bpy.types.Collection):
        # print(blender_collection.name + " is a collection")
        try:
            blender_collection["SR2MDL file header"]
            return True
        except:
            return False
    else:
        return False


def collectSR2Collections(base_collection):
    collection_children = base_collection.children

    sr2_model_collections = []

    for collection in collection_children:
        if isSR2MDLcollection(collection):
            print(collection.name + " is a SR2MDL collection")
            sr2_model_collections.append(collection)

    return sr2_model_collections


def convertBlenderVertexesToSR2Vertexes(blender_mesh):
    vertexes = []

    # Position and normals
    for vertex_index in range(len(blender_mesh.vertices)):
        blender_vertex = blender_mesh.vertices[vertex_index]
        blender_normal = blender_vertex.normal

        SR2_vertex = Vertex()
        SR2_vertex.position = [blender_vertex.co.x,
                               blender_vertex.co.y,
                               blender_vertex.co.z]

        SR2_vertex.normal = list(blender_normal)

        SR2_vertex.normal[0] = round(SR2_vertex.normal[0], 3)
        SR2_vertex.normal[1] = round(SR2_vertex.normal[1], 3)
        SR2_vertex.normal[2] = round(SR2_vertex.normal[2], 3)

        vertexes.append(SR2_vertex)

    # UVs and Custom-Split Normals
    for i, loop in enumerate(blender_mesh.loops):
        # UV
        fliped_uv = [blender_mesh.uv_layers["uv0"].data[i].uv[0], blender_mesh.uv_layers["uv0"].data[i].uv[1]]
        # flip V-coordinate
        fliped_uv[1] = -(fliped_uv[1] - 1.0)
        vertexes[loop.vertex_index].uv = fliped_uv
        # Custom-Split Normals
        #vertexes[loop.vertex_index].normal = loop.normal


    return vertexes


def save(output_folder_path: str):
    # Collect all data from a collection and fill SR2_model with it

    # Select the base "Scene Collection" and get all child collections that have SR2MDL file header attached to them
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    sr2_model_collections = collectSR2Collections(bpy.data.scenes['Scene'].collection)
    print("Found", len(sr2_model_collections), "SR2 Collections")

    # Make a SR2MDL class instance for each SR2MDL collection and save each file
    for sr2_collection in sr2_model_collections:
        SR2_model = SR2MDL()

        SR2_model.file_header = sr2_collection["SR2MDL file header"]

        # Go through each object and make a SR2Node and Mesh out of its data
        print(sr2_collection.name, "has", len(sr2_collection.objects), "objects")

        for bl_object in sr2_collection.objects:
            new_node = SR2Node()

            new_node.transform = bl_object["Node Transform"]
            # Apply Blender Inspector Values
            locRotScale = bl_object.matrix_local.decompose()
            # Position
            new_node.transform["Position X"] = locRotScale[0][0]
            new_node.transform["Position Y"] = locRotScale[0][1]
            new_node.transform["Position Z"] = locRotScale[0][2]
            # Rotation
            euler = locRotScale[1].to_euler('XYZ')
            new_node.transform["Scale X"] = euler[0]/math.pi*0x7FFF
            new_node.transform["Scale Y"] = euler[1]/math.pi*0x7FFF
            new_node.transform["Scale Z"] = euler[2]/math.pi*0x7FFF
            # Scale
            new_node.transform["Scale X"] = locRotScale[2][0]
            new_node.transform["Scale Y"] = locRotScale[2][1]
            new_node.transform["Scale Z"] = locRotScale[2][2]

            new_node.relation = bl_object["Node Relation"]

            if bl_object.get("Extra"):
                new_node.extra = bl_object["Extra"]

            if bl_object.get("Some Data"):
                new_node.some_data = bl_object["Some Data"]

            SR2_model.nodes.append(new_node)

            # Fill Mesh, if exist
            if bl_object.data:
                SR2_mesh = Mesh()

                blender_mesh = bl_object.data

                SR2_mesh.material = bl_object["Material"]

                SR2_mesh.vertexes = convertBlenderVertexesToSR2Vertexes(blender_mesh)

                for face in blender_mesh.polygons:
                    SR2_mesh.faces.extend(face.vertices)

                SR2_mesh.model_pointers = bl_object["Model Pointers"]
                SR2_mesh.model_pointers["Vertex Count"] = len(SR2_mesh.vertexes)
                SR2_mesh.model_pointers["Face Count"] = len(SR2_mesh.faces)  # Triangle count

                SR2_mesh.draw_options = bl_object["Draw Options"]

                SR2_model.meshes.append(SR2_mesh)

        output_file_path = output_folder_path + sr2_collection.name + ".mdl"
        SR2_model.save(output_file_path + " repack")
        print("Saved at " + output_file_path + " repack")


""" UI stuff """


class SR2PanelProperties(PropertyGroup):

    path_to_input: StringProperty(
        name="MDL path",
        description="Path to MDl file",
        default="",
        maxlen=1024,
        subtype='FILE_PATH')

    path_to_output: StringProperty(
        name="Output path",
        description="Path to output folder",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')


class SaveOperator(bpy.types.Operator):
    """Save"""
    bl_label = "Save"
    bl_idname = "sr2mdl.save"

    def execute(self, context):
        save_path = bpy.context.scene.sr2_panel_props.path_to_output

        if save_path != "":
            save(save_path)

        return {'FINISHED'}


class LoadOperator(bpy.types.Operator):
    """Load"""
    bl_label = "Load"
    bl_idname = "sr2mdl.load"

    def execute(self, context):
        load_path = bpy.context.scene.sr2_panel_props.path_to_input
        print("Load path", load_path)

        if load_path != "":
            load(load_path, mathutils.Matrix())

        return {'FINISHED'}


class SR2MDLSidebarPanel(bpy.types.Panel):
    """Creates a custom panel in the sidebar"""
    bl_label = "SR2 MDL"
    bl_idname = "SR2_sidebar"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "SR2MDL"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        my_props = scene.sr2_panel_props

        # top_row = layout.row()
        # top_row.label(text="Path to file")

        layout.prop(my_props, "path_to_input", text="Path to MDL")

        layout.operator("sr2mdl.load", text="Load")

        row = layout.row()
        row.label(text="Don't forget to triangulate faces (CTRL + T)!")

        layout.prop(my_props, "path_to_output", text="Output folder")
        layout.operator("sr2mdl.save", text="Save")


# List of classes to register
classes = (
    SR2PanelProperties,
    SaveOperator,
    LoadOperator,
    SR2MDLSidebarPanel,
)


# Registration and unregistration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sr2_panel_props = bpy.props.PointerProperty(type=SR2PanelProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.sr2_panel_props

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
