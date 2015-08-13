import os
from PIL import Image
from PIL import ImageTk
import tkinter

class TextureTile:
    def __init__(self):
        self.windowtitle = 'Texture Tile'

        self.t = tkinter.Tk()
        self.t.title(self.windowtitle)
        self.w = 500
        self.h = 525
        self.screenwidth = self.t.winfo_screenwidth()
        self.screenheight = self.t.winfo_screenheight()
        self.windowwidth = self.w
        self.windowheight = self.h
        self.windowx = (self.screenwidth-self.windowwidth) / 2
        self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
        self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
        self.t.geometry(self.geometrystring)

        self.entry_filename = tkinter.Entry(self.t, font=('Consolas', 12))
        self.spinbox_x = tkinter.Spinbox(self.t, width=2, from_=1, to=2 ** 13)
        self.spinbox_y = tkinter.Spinbox(self.t, width=2, from_=1, to=2 ** 13)
        self.button_load = tkinter.Button(self.t, text='Load', command=self.file_load_display)
        self.frame_filearea = tkinter.Frame(self.t)
        self.label_image = tkinter.Label(self.frame_filearea, bg='#222')

        self.t.columnconfigure(0, weight=1)
        self.t.rowconfigure(1, weight=1)
        self.entry_filename.grid(row=0, column=0, sticky='ew')
        self.spinbox_x.grid(row=0, column=1)
        self.spinbox_y.grid(row=0, column=2)
        self.button_load.grid(row=0, column=3, sticky='ne')
        self.frame_filearea.grid(row=1, column=0, columnspan=4, sticky='nsew')
        self.label_image.pack(expand=True, fill='both')
        #self.entry_filename.pack(fill='x')
        #self.button_load.pack()
        #self.label_image.pack()

        self.entry_filename.insert(0, os.getcwd())
        self.entry_filename.bind('<Return>', self.file_load_display)
        self.entry_filename.focus_set()

        self.spinbox_x.delete(0, 'end')
        self.spinbox_x.insert(0, 3)
        self.spinbox_y.delete(0, 'end')
        self.spinbox_y.insert(0, 3)

        self.t.mainloop()

    def fit_into_bounds(self, iw, ih, fw, fh):
        '''
        Given the w+h of the image and the w+h of the frame,
        return new w+h that fits the image into the frame
        while maintaining the aspect ratio and leaving blank space
        everywhere else
        '''
        ratio = min(fw/iw, fh/ih)

        w = int(iw * ratio)
        h = int(ih * ratio)

        return (w, h)

    def file_load_display(self, *event):
        filename = self.entry_filename.get()
        # I want to check the spinbox values up
        # here so they can crash before wasting
        # a file read.
        xcount = int(self.spinbox_x.get())
        ycount = int(self.spinbox_y.get())
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
        expanded = expanded.resize((w * xcount, h * ycount))
        for x in range(xcount):
            for y in range(ycount):
                expanded.paste(image, (w*x, h*y))

        # Resize 9x'ed image into frame
        w = expanded.size[0]
        h = expanded.size[1]
        fw = self.label_image.winfo_width()
        fh = self.label_image.winfo_height()
        wh = self.fit_into_bounds(w, h, fw, fh)

        expanded = expanded.resize(wh)
        image = ImageTk.PhotoImage(expanded)
        self.label_image.configure(image=image)
        self.label_image.dont_garbage_me_bro = image

if __name__ == '__main__':
    t = TextureTile()