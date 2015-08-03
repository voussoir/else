import os
from PIL import Image
from PIL import ImageTk
import tkinter

class TextureTile:
    def __init__(self):
        self.windowtitle = 'Texture Tile'

        self.t = tkinter.Tk()
        self.t.title(self.windowtitle)
        self.w = 450
        self.h = 475
        self.screenwidth = self.t.winfo_screenwidth()
        self.screenheight = self.t.winfo_screenheight()
        self.windowwidth = self.w
        self.windowheight = self.h
        self.windowx = (self.screenwidth-self.windowwidth) / 2
        self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
        self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
        self.t.geometry(self.geometrystring)

        self.entry_filename = tkinter.Entry(self.t, font=('Consolas', 12))
        self.button_load = tkinter.Button(self.t, text='Load', command=self.file_load_display)
        self.frame_filearea = tkinter.Frame(self.t)
        self.label_image = tkinter.Label(self.frame_filearea, bg='#222')

        self.t.columnconfigure(0, weight=1)
        self.t.rowconfigure(1, weight=1)
        self.entry_filename.grid(row=0, column=0, sticky='ew')        
        self.button_load.grid(row=0, column=1, sticky='ne')
        self.frame_filearea.grid(row=1, column=0, columnspan=2, sticky='nsew')
        self.label_image.pack(expand=True, fill='both')
        #self.entry_filename.pack(fill='x')
        #self.button_load.pack()
        #self.label_image.pack()

        self.entry_filename.insert(0, os.getcwd())
        self.entry_filename.bind('<Return>', self.file_load_display)
        self.entry_filename.focus_set()

        self.t.mainloop()

    def file_load_display(self, *event):
        filename = self.entry_filename.get()
        # Open file or turn red
        try:
            image = Image.open(filename)
            self.entry_filename.configure(bg='#fff')
        except FileNotFoundError:
            self.entry_filename.configure(bg='#f00')
            return
        
        # 9x the image
        w = image.size[0]
        h = image.size[1]
        expanded = image.copy()
        expanded = expanded.resize((w * 3, h * 3))
        for x in range(3):
            for y in range(3):
                expanded.paste(image, (w*x, h*y))

        # Resize 9x'ed image into frame
        w = expanded.size[0]
        h = expanded.size[1]
        fw = self.label_image.winfo_width()
        fh = self.label_image.winfo_height()
        ratio = min(fw/w, fh/h)
        
        w = int(w * ratio)
        h = int(h * ratio)

        expanded = expanded.resize((w, h))
        image = ImageTk.PhotoImage(expanded)
        self.label_image.configure(image=image)
        self.label_image.dont_garbage_me_bro = image

if __name__ == '__main__':
    t = TextureTile()