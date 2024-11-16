
if __name__ == '__main__':
    from GUIbackend.SARCTab import *
    from GUIbackend.TextureTab import *

    window = Tk()
    window.title("Sega Rally 2 Modding Tools v0.5")
    window.geometry('800x600')

    tab_control = ttk.Notebook(window)

    texture_tab = TextureTab(tab_control)
    sarc_tab = SARCTab(tab_control)

    window.mainloop()
