import tkinter
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from tkinter import *

import GUIbackend.file_helpers
from SARCextractor import SARC


class SARCTab:
    def __init__(self, tab_control):
        self.sarc_tab = ttk.Frame(tab_control)
        tab_control.add(self.sarc_tab, text='SARC Archive')
        tab_control.pack(expand=1, fill='both')

        list_row = 0
        input_row = 1
        unpack_row = 2

        # Input Line
        self.input_flavour_text = Label(self.sarc_tab, text="Input archive:")
        self.input_flavour_text.grid(column=0, row=input_row)

        entry_width = 75
        self.input_sarc_file = Entry(self.sarc_tab, width=entry_width)
        self.input_sarc_file.grid(column=1, row=input_row)

        self.open_sarc_button = Button(self.sarc_tab,
                                       text="Select",
                                       command=lambda: self.preview_sarc_file())
        self.open_sarc_button.grid(column=2, row=input_row)

        # Unpack button
        self.output_sarc_path = ""
        self.output_sarc_button = Button(self.sarc_tab, text="Unpack to...", command=self.extract_sarc_command)
        self.output_sarc_button.grid(column=1, row=unpack_row)

        # Archive Preview
        columns = ("ID", "File Size", "File Size 2", "File Offset", "File Path", "File Type")
        self.sarc_tree = ttk.Treeview(self.sarc_tab, columns=columns, show="headings")
        self.sarc_tree.grid(columnspan=3, row=list_row)

        for title in columns:
            self.sarc_tree.heading(title, text=title)

        self.sarc_tree.column(0, width=20)

        self.sarc_tree.column(1, width=80)
        self.sarc_tree.column(2, width=80)
        self.sarc_tree.column(3, width=80)

        self.sarc_tree.column(4, width=400)

        self.sarc_tree.column(5, width=80)

    def preview_sarc_file(self):
        GUIbackend.file_helpers.choose_file_for_entry(self.input_sarc_file, GUIbackend.file_helpers.sr2_file_types["SARC"])

        path_to_sarc = self.input_sarc_file.get()

        if path_to_sarc != "":
            with open(path_to_sarc, "r+b") as file:
                file_bytes = file.read()
                file_signature = file_bytes[:4]

                print(file_signature)
                print(file_signature == b'SARC')

                if file_signature == b'SARC':
                    print(file_signature)
                    self.sarc_file = SARC()
                    self.sarc_file.unpack_from_bytes(file_bytes)

                    counter = 0

                    for header in self.sarc_file.packed_file_header_list:
                        row_values = []
                        row_values.append(counter)

                        for key in header:
                            row_values.append(header[key])

                        row_values[3] = hex(row_values[3])

                        file_path = header["File Path"]  # 255 bytes
                        file_path = file_path[:file_path.find(b'\x00')]  # Remove the padding at the end
                        file_path = file_path.decode("cp932")  # Decode text

                        row_values[4] = file_path

                        file_name = file_path[file_path.rfind('\\') + 1:]  # Keep only the name of the file
                        file_extension = file_name[-3:]

                        file_type = "Other"
                        if file_extension in [".bg", "txr", "sky", "tyk"]:
                            file_type = "Texture"
                        elif file_extension == "mdl":
                            file_type = "3D Model"

                        row_values.append(file_type)

                        self.sarc_tree.insert("", tkinter.END, values=row_values)

                        counter += 1
                        # print(header)
                else:
                    messagebox.showwarning('Warning', 'Selected file is not a SARC archive')
                    return

    def extract_sarc_command(self):
        self.output_sarc_path = filedialog.askdirectory() + "/"

        if self.output_sarc_path == "":
            messagebox.showwarning('Warning', 'No output folder selected')
            return

        self.sarc_file.save_files_to_folder(self.output_sarc_path)
        messagebox.showinfo('Success', 'Extracted Successfully')
