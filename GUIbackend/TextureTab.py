import tkinter
from tkinter import messagebox
from tkinter import ttk

import PIL.Image
from PIL import ImageTk

from GUIbackend.file_helpers import *
from bmp_to_png import *
from texture_tool import *

import multiprocessing

png_converter_pool = multiprocessing.Pool()

class TextureTab:
    def __init__(self, tab_control):
        self.texture_tab = ttk.Frame(tab_control)
        tab_control.add(self.texture_tab, text='Texture Tab')

        self.bmp_texture_list = []  # For conversion and export
        self.png_texture_list = []  # For export and display

        # Input row
        self.input_texture_file_title = ""
        self.setup_input_row(self.texture_tab)

        # Left Panel
        self.left_frame = ttk.Frame(self.texture_tab, relief=GROOVE, borderwidth=2)
        self.left_frame.grid(column=0, row=1)

        # Sub-Texture Info
        self.setup_texture_info_box(self.left_frame)
        self.setup_texture_id_list(self.left_frame)
        self.setup_edit_buttons(self.left_frame)

        # Texture Preview
        self.unpacked_texture = SR2Texture  # SR2 texture class, for info

        self.empty_image = ImageTk.PhotoImage(Image.new("RGB", (1, 1)))
        self.display_image = self.empty_image
        self.setup_texture_preview(self.display_image, 1, 1)

        # Saving options
        self.output_folder = ""
        self.setup_export_buttons(self.texture_tab, 1, 4)

    # = = = = =
    #   GUI
    # = = = = =
    def setup_input_row(self, texture_tab):
        self.input_frame = Frame(texture_tab)
        self.input_frame.grid(column=1, row=0)

        self.input_texture_label = Label(self.input_frame, text="Input texture:")
        self.input_texture_label.grid(column=0, row=0)

        self.entry_width = 75
        self.input_texture_entry = Entry(self.input_frame, width=self.entry_width)
        self.input_texture_entry.grid(column=1, row=0)

        self.open_input_texture_button = Button(self.input_frame, text="Select", command=self.open_texture_file)
        self.open_input_texture_button.grid(column=2, row=0)

    # Left Panel
    def setup_texture_info_box(self, parent_frame):
        self.texture_info_box_frame = ttk.Frame(parent_frame)
        self.texture_info_box_frame.grid(column=0, row=0)

        self.texture_info_labels = {
            "Description": [],
            "Value": []
        }

        self.texture_file_format_label = Label(self.texture_info_box_frame, text="Texture Format")
        self.texture_file_format_label.grid(column=0, row=0)

        self.texture_file_format_value = Label(self.texture_info_box_frame, text="")
        self.texture_file_format_value.grid(column=1, row=0)

        self.texture_parameters = {
            "ID": 0,
            "Width": 0,
            "Height": 0,
            "Color Format": "",
            "File Offset": 0,
            "Size (in bytes)": 0
        }

        row_counter = 1
        for key in self.texture_parameters:
            info_label = Label(self.texture_info_box_frame, text=key)
            info_label.grid(column=0, row=row_counter)
            self.texture_info_labels["Description"].append(info_label)

            # Update the values
            value_label = Label(self.texture_info_box_frame, text=0)
            value_label.grid(column=1, row=row_counter)
            self.texture_info_labels["Value"].append(value_label)

            row_counter += 1

    def setup_texture_id_list(self, parent_frame):
        self.update_id_list(1)

        self.texture_id_listbox = Listbox(parent_frame, listvariable=self.id_list_var)
        self.texture_id_listbox.grid(column=0, row=1)
        self.texture_id_listbox.bind("<<ListboxSelect>>", self.on_id_select)

    def setup_edit_buttons(self, parent_frame):
        self.edit_buttons_frame = Frame(parent_frame)
        self.edit_buttons_frame.grid(column=0, row=2)

        '''
        self.add_subtexture_button = (Button(self.edit_buttons_frame,
                                             text=" + ",
                                             command=lambda: self.add_subtexture_at_id(self.selected_id)))
        self.add_subtexture_button.grid(column=0, row=0)
        '''

        self.replace_subtexture_button = (Button(self.edit_buttons_frame,
                                                 text="Replace with...",
                                                 command=lambda: self.replace_subtexture_at_id(self.selected_id)))
        self.replace_subtexture_button.grid(column=1, row=0)

        '''
        self.delete_subtexture_button = (Button(self.edit_buttons_frame,
                                             text=" - ",
                                             command=lambda: self.delete_subtexture_at_id(self.selected_id)))
        self.delete_subtexture_button.grid(column=2, row=0)
        '''

    def setup_texture_preview(self, png_image, column, row):
        self.texture_preview_frame = Frame(self.texture_tab, relief=GROOVE, borderwidth=2)
        self.texture_preview_frame.grid(column=column, row=row)

        self.texture_border = Label(self.texture_preview_frame, text='Titled Border')
        self.texture_border.place(relx=.06, rely=0.125, anchor=W)

        self.image_canvas = Canvas(self.texture_preview_frame, width=512, height=512)
        self.image_canvas.grid(column=0, row=0)

        self.image_container = self.image_canvas.create_image(0, 0, anchor=NW, image=self.display_image)

        '''
        self.image_preview_scroll = Scrollbar(self.preview_frame, orient='vertical', command=self.image_canvas.yview)
        self.image_preview_scroll.grid(column=1, row=0, sticky='ns')

        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"),
                                    yscrollcommand=self.image_preview_scroll.set)
        '''

    def setup_export_buttons(self, parent_frame, column, row):
        self.export_frame = Frame(parent_frame)
        self.export_frame.grid(column=column, row=row)

        self.export_label = Label(self.export_frame, text="Export as")
        self.export_label.grid(column=0, row=0)

        self.export_image_format = StringVar(value="png")

        self.bmp_radiobutton = Radiobutton(self.export_frame, text="bmp", value="bmp",
                                           variable=self.export_image_format)
        self.bmp_radiobutton.grid(column=1, row=0)

        self.png_radiobutton = Radiobutton(self.export_frame, text="png", value="png",
                                           variable=self.export_image_format)
        self.png_radiobutton.grid(column=2, row=0)

        '''
        self.export_subtexture_button = (Button(self.export_frame,
                                         text="Export this to...",
                                         command=self.export_texture))
        self.export_subtexture_button.grid(column=3, row=0)
        '''

        self.export_all_button = (Button(self.export_frame,
                                         text="Export all to...",
                                         command=self.export_texture))
        self.export_all_button.grid(column=4, row=0, padx=10)

        self.save_texture_as_button = (Button(self.export_frame,
                                         text="Save TXR as...",
                                         command=self.save_texture))
        self.save_texture_as_button.grid(column=5, row=0, padx=10)

    # = = = = =
    # Functionality
    # = = = = =
    def on_id_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.selected_id = event.widget.get(index)
            self.update_texture_info(self.selected_id)
            self.update_texture_preview(self.selected_id)
            # print(self.selected_id)
        else:
            self.selected_id = 0
            # print("None Selected")

    def add_subtexture_at_id(self, subtexture_id):
        image_path = filedialog.askopenfilename(filetypes=sr2_file_types["Images"])

        # TODO
        # Make a pop up window for choosing subtexture_format
        #

    def replace_subtexture_at_id(self, subtexture_id):
        image_path = filedialog.askopenfilename(filetypes=sr2_file_types["Images"])

        if image_path == "":
            return

        subtexture_format = self.texture_info_labels["Value"][3]["text"]
        print(subtexture_format)

        if image_path[-3:] == "png":
            png = PIL.Image.open(image_path)
            bmp = PNGtoBMP(png, subtexture_format)
        elif image_path[-3:] == "bmp":
            bmp = BMP()
            bmp.unpack_from_file(image_path)
            png = BMPtoPNG(bmp)
        else:
            tkinter.messagebox.showwarning(title="Incorrect Input", message="Choose a PNG or BMP file")
            return

        self.bmp_texture_list[subtexture_id] = bmp
        self.png_texture_list[subtexture_id] = png

        #print(bmp.image_header)
        # Replace in unpacked texture, can be offloaded to the texture classes
        self.unpacked_texture.texture_header_list[subtexture_id]["Image Width"] = bmp.image_header["Image Width"]

        if "Image Height" in self.unpacked_texture.texture_header_list[subtexture_id]:
            self.unpacked_texture.texture_header_list[subtexture_id]["Image Height"] = bmp.image_header["Image Height"]

        self.unpacked_texture.texture_header_list[subtexture_id]["Image Size (in bytes)"] = len(bmp.pixel_bytes)

        # Skipping palette conversion, if you are import paletted BMP through GUI you can also make a proper PNG
        if "Palette Usage" in self.unpacked_texture.texture_header_list[subtexture_id]:
            self.unpacked_texture.texture_header_list[subtexture_id]["Palette Usage"] = 0
            self.unpacked_texture.texture_header_list[subtexture_id]["Palette Used"] = 0

        self.unpacked_texture.pixel_bytes_list[subtexture_id] = bmp.pixel_bytes

        # print(self.unpacked_texture.texture_header_list[subtexture_id])

    def delete_subtexture_at_id(self, subtexture_id):
        pass
        # TODO
        # Easy to implement but useless without add_subtexture_at_id
        #

    def update_texture_preview(self, sub_texture_index):
        try:
             self.png_texture_list = self.pool_png_result.get(2)
        except:
            pass

        new_display_image = ImageTk.PhotoImage(self.png_texture_list[sub_texture_index])
        self.image_canvas.itemconfig(self.image_container, image=new_display_image)
        self.image_canvas.imgref = new_display_image

    def update_id_list(self, id_count):
        self.selected_id = 0
        self.id_list = [i for i in range(id_count)]
        self.id_list_var = Variable(value=self.id_list)

    def open_texture_file(self):
        choose_file_for_entry(self.input_texture_entry, sr2_file_types["Textures"])
        texture_path = self.input_texture_entry.get()

        if texture_path != "":
            self.input_texture_file_title = texture_path[texture_path.rfind("/") + 1:]

            self.unpacked_texture = detect_texture_type(texture_path)
            self.unpacked_texture.unpack_from_file(texture_path)

            with open(texture_path, 'r+b') as f:
                file_signature = f.read(4)

                if file_signature == b'RTXR' or file_signature == b'MTEX':
                    tkinter.messagebox.showerror(title="Error", message="Can't open RTXR textures. MTEX can be partially exported through code.")
                    return

            # Convert subtextures into BMP and PNG for export and preview
            self.bmp_texture_list = convertTXRtoBMPlist(texture_path)
            self.png_texture_list = [self.empty_image for i in range(len(self.bmp_texture_list))]

            # Run proper PNG conversion in async mode, so you wouldn't have to wait for 10 minutes for 4k textures to load
            self.pool_png_result = png_converter_pool.map_async(BMPtoPNG, self.bmp_texture_list)
            # Thought you still need to wait if you want previews

            self.update_id_list(len(self.unpacked_texture.pixel_bytes_list))
            self.texture_id_listbox.configure(listvariable=self.id_list_var)

            self.update_texture_info(0)
            self.update_texture_preview(0)
            # print(self.input_texture_file_title)

    def update_texture_info(self, texture_index):
        current_texture_header = self.unpacked_texture.texture_header_list[texture_index]

        self.texture_file_format_value["text"] = self.unpacked_texture.file_header["Signature"].decode("UTF-8")

        self.texture_info_labels["Value"][0]["text"] = texture_index
        self.texture_info_labels["Value"][1]["text"] = current_texture_header["Image Width"]

        if "Image Height" in current_texture_header:
            self.texture_info_labels["Value"][2]["text"] = current_texture_header["Image Height"]
        else:
            self.texture_info_labels["Value"][2]["text"] = current_texture_header["Image Width"]

        try:
            color_format_value = current_texture_header["Color Format"]
        except:
            color_format_value = 0

        match color_format_value:
            case 0:
                color_format_string = "RGB565"
            case 2:
                color_format_string = "ARGB1555"
            case 8:
                color_format_string = "ARGB4444"
            case _:
                color_format_string = "RGB565"

        self.texture_info_labels["Value"][3]["text"] = color_format_string
        self.texture_info_labels["Value"][4]["text"] = 0  # Subtexture offset
        self.texture_info_labels["Value"][5]["text"] = len(self.unpacked_texture.pixel_bytes_list[texture_index])

    def export_texture(self):
        # print(self.export_image_format.get())
        self.output_folder = filedialog.askdirectory() + "/"

        if self.output_folder == "/":
            return

        subtexture_index_counter = 0
        if self.export_image_format.get() == "png":
            self.pool_png_result.wait()
            self.png_texture_list = self.pool_png_result.get()
            for png in self.png_texture_list:
                png.save(self.output_folder + self.input_texture_file_title + "." + str(subtexture_index_counter) + ".png")
                subtexture_index_counter += 1
        elif self.export_image_format.get() == "bmp":
            for bmp in self.bmp_texture_list:
                bmp.save(self.output_folder + self.input_texture_file_title + "." + str(subtexture_index_counter) + ".bmp")
                subtexture_index_counter += 1

        tkinter.messagebox.showinfo(title="Success", message="Successfully extracted to", detail=self.output_folder)

    def save_texture(self):
        file = filedialog.asksaveasfile(filetypes=sr2_file_types["Textures"])

        if file is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return

        # Why can't TKinter have an option to open a file as binary?
        saved_file_path = file.name
        file.close()
        self.unpacked_texture.save(saved_file_path)
