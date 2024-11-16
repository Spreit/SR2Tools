from tkinter import *
from tkinter import filedialog

sr2_file_types = {
    "SARC": (("Dreamcast SARC file", "*.bin"), ("all files", "*.*")),
    "Images": (("Input images", "*.png *.bmp"), ("all files", "*.*")),
    "Textures": (("Sega Rally 2 texture", "*.txr *.bg *.sky *.tyk *.sea *.sky1 *.sky2"), ("all files", "*.*")),
    "3D Model": (("Sega Rally 2 3D model", "*.mdl"), ("all files", "*.*"))
}


def choose_file_for_entry(entry_to_change, filetypes):
    file_path = filedialog.askopenfilename(filetypes=filetypes)
    entry_to_change.delete(0, END)
    entry_to_change.insert(0, file_path)


def choose_folder_for_entry(path_to_change):
    folder_path = filedialog.askdirectory() + "/"
    path_to_change.delete(0, END)
    path_to_change.insert(0, folder_path)
