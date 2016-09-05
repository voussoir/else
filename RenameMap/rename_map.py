import os
import tkinter


class Application:
    def __init__(self):
        self.windowtitle = 'Rename Map'

        self.t = tkinter.Tk()
        self.t.title(self.windowtitle)
        w = 800
        h = 525
        screenwidth = self.t.winfo_screenwidth()
        screenheight = self.t.winfo_screenheight()
        windowwidth = w
        windowheight = h
        windowx = (screenwidth-windowwidth) / 2
        windowy = ((screenheight-windowheight) / 2) - 27
        self.geometrystring = '%dx%d+%d+%d' % (windowwidth, windowheight, windowx, windowy)
        self.t.geometry(self.geometrystring)

        self.create_mainframe()
        self.build_gui_mainmenu()

    def annihilate(self):
        self.mainframe.destroy()
        self.create_mainframe()

    def build_gui_mainmenu(self):
        self.annihilate()
        font = ('Consolas', 15)

        self.entry_left = tkinter.Entry(self.mainframe, font=font)
        self.entry_right = tkinter.Entry(self.mainframe, font=font)
        self.entry_left.grid(row=0, column=0, sticky='ew')
        self.entry_right.grid(row=1, column=0, sticky='ew')
        self.entry_left.insert(0, 'Left path')
        self.entry_right.insert(0, 'Right path')

        button_start = tkinter.Button(self.mainframe, text='Go', command=self.build_gui_mapper)
        button_start.grid(row=2, column=0, sticky='ew')
        self.mainframe.rowconfigure(0, weight=1)
        self.mainframe.rowconfigure(1, weight=1)
        self.mainframe.columnconfigure(0, weight=1)

    def build_gui_mapper(self):
        left_path = self.entry_left.get()
        right_path = self.entry_right.get()
        self.annihilate()
        left_files = os.listdir(left_path)
        right_files = os.listdir(right_path)
        print(left_files)
        print(right_files)


    def create_mainframe(self):
        self.mainframe = tkinter.Frame(self.t)
        self.mainframe.pack(fill='both', expand=True)

    def mainloop(self):
        self.t.mainloop()

if __name__ == '__main__':
    a = Application()
    a.mainloop()