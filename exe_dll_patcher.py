import bin_files_tool


def patch_bytes_at(original_bytes, patch_bytes, replace_at_address) -> bytes:
    pre_patch_bytes  = original_bytes[:replace_at_address]
    post_patch_bytes = original_bytes[replace_at_address + len(patch_bytes):]
    return pre_patch_bytes + patch_bytes + post_patch_bytes


# what_file_has_changed refers to EXE_address_list in bin_files_tool
def patch_size_in_EXE_or_DLL(bin_file_path, path_to_exe_or_mselect, what_file_has_changed, output_path):
    original_file = open(path_to_exe_or_mselect, "r+b")
    original_file_bytes = original_file.read()
    original_file.close()

    bin_file = open(bin_file_path, "r+b")
    bin_file_bytes = bin_file.read()
    bin_file.close()

    unpacked_bin = bin_files_tool.BIN()
    unpacked_bin.unpack_from_bytes(bin_file_bytes)
    size_list_bytes = unpacked_bin.make_size_list_bytes()

    patch_size = 240

    if path_to_exe_or_mselect[-3:] == "exe" or path_to_exe_or_mselect[-3:] == "EXE":
        patch_address = bin_files_tool.EXE_address_list[what_file_has_changed]
    elif path_to_exe_or_mselect[-3:] == "dll" or path_to_exe_or_mselect[-3:] == "DLL":
        patch_address = bin_files_tool.MSELECT_address_list[what_file_has_changed]

    patched_EXE_or_MSELECT_bytes = patch_bytes_at(original_file_bytes, size_list_bytes, patch_address)

    with open(output_path, "w+b") as file:
        file.write(patched_EXE_or_MSELECT_bytes)


def mass_patch_EXE_and_DLL():
    exe_path = "./binpacks/MDL/SEGA RALLY 2 — original.exe"
    dll_path = "./binpacks/MDL/MSelect original.dll"

    b_carmdl_path = "./binpacks/MDL/new B_CARMDL.BIN"
    b_cartex_path = "./binpacks/MDL/B_CARTEX.BIN"
    b_refmdl_path = "./binpacks/MDL/new B_REFMDL.BIN"

    new_exe_path = "./binpacks/MDL/SEGA RALLY 2.exe"
    new_dll_path = "./binpacks/MDL/MSelect.dll"

    # EXE
    patch_size_in_EXE_or_DLL(b_carmdl_path, exe_path, "B_CARMDL.BIN", new_exe_path)
    patch_size_in_EXE_or_DLL(b_cartex_path, new_exe_path, "B_CARTEX.BIN", new_exe_path)
    patch_size_in_EXE_or_DLL(b_refmdl_path, new_exe_path, "B_REFMDL.BIN", new_exe_path)
    print("Patched ", exe_path, " and saved at ", new_exe_path)

    # DLL
    patch_size_in_EXE_or_DLL(b_carmdl_path, dll_path, "B_CARMDL.BIN", new_dll_path)
    patch_size_in_EXE_or_DLL(b_cartex_path, new_dll_path, "B_CARTEX.BIN", new_dll_path)
    patch_size_in_EXE_or_DLL(b_refmdl_path, new_dll_path, "B_REFMDL.BIN", new_dll_path)
    print("Patched ", dll_path, " and saved at ", new_dll_path)


if __name__ == "__main__":
    mass_patch_EXE_and_DLL()

