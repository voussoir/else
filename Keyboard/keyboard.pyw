import tkinter

class Keyboard:
    def __init__(self):
        self.windowtitle = 'Keyboard'

        self.keywidth = 30
        self.keyspace = 5
        self.keys = self.build_keydict()

        self.t = tkinter.Tk()
        self.t.title(self.windowtitle)
        self.w = (self.keywidth + self.keyspace) * 16
        self.h = (self.keywidth + self.keyspace) * 6
        self.screenwidth = self.t.winfo_screenwidth()
        self.screenheight = self.t.winfo_screenheight()
        self.windowwidth = self.w
        self.windowheight = self.h
        self.windowx = (self.screenwidth-self.windowwidth) / 2
        self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
        self.geometrystring = '%dx%d+%d+%d' % (
            self.windowwidth, self.windowheight, self.windowx, self.windowy)
        self.t.geometry(self.geometrystring)

        self.c = tkinter.Canvas(self.t)
        self.c.pack(expand=True, fill='both')

        self.build_qwerty()

        self.t.bind('<KeyPress>', self.press)
        self.t.bind('<KeyRelease>', self.release)

    def mainloop(self):
        self.t.mainloop()

    def press(self, event):
        c = event.char.lower()
        if c in self.keys:
            self.c.itemconfig(self.keys[c], fill='#f00')

    def release(self, event):
        c = event.char.lower()
        if c in self.keys:
            self.c.itemconfig(self.keys[c], fill='systembuttonface')

    def build_keydict(self):
        mainy = self.keywidth
        w = self.keywidth + self.keyspace
        rows = [
        {'c':'`1234567890-=',  'x':w,     'y':mainy},
        {'c':'qwertyuiop[]\\', 'x':w*1.5, 'y':mainy+w},
        {'c':'asdfghjkl;\'',   'x':w*1.8, 'y':mainy+(w*2)},
        {'c':'zxcvbnm,./',     'x':w*2.4, 'y':mainy+(w*3)},
        {'c':' ',              'x':w,     'y':mainy+(w*4)}
        ]

        keys = {}
        for row in rows:
            for ki in range(len(row['c'])):
                k = row['c'][ki]
                keys[k] = (row['x'] + ((self.keywidth + self.keyspace) * ki), row['y'])
        return keys

    def build_qwerty(self):
        w = self.keywidth
        for k in self.keys:
            x = self.keys[k][0]
            y = self.keys[k][1]
            self.keys[k] = self.c.create_rectangle(x, y, x+w, y+w)
            self.c.create_text(x+(w/2), y+(w/2), text=k)



k = Keyboard()
k.mainloop()