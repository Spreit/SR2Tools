if __name__ == '__main__':
    import tkinter
    from tkinter import ttk

    from GUIbackend.TextureTab import TextureTab
    from GUIbackend.SARCTab import SARCTab

    window = tkinter.Tk()
    window.title("Sega Rally 2 Modding Tools v0.5.4")
    window.geometry('800x600')

    tab_control = ttk.Notebook(window)

    texture_tab = TextureTab(tab_control)
    sarc_tab = SARCTab(tab_control)

    window.mainloop()
