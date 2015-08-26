import sys
import syshub
import tkinter

class EntryWithHistory(tkinter.Entry):
    def __init__(self, master, submithook, *args, **kwargs):
        super(EntryWithHistory, self).__init__(master, *args, **kwargs)
        self.previousinputs = []
        self.previousinputstep = 0

        self.submithook = submithook

        self.bind('<Return>', self.submit)
        self.bind('<Escape>', lambda b: self.delete(0, 'end'))
        self.bind('<Up>', self.previous_back)
        self.bind('<Down>', self.previous_forward)

    def submit(self, *b):
        x = self.get()
        x = x.lower()
        noskip = '!' in x
        if 2 < len(x) < 21:
            if len(self.previousinputs) == 0 or self.previousinputs[-1] != x:
                self.previousinputs.append(x)
            self.previousinputstep = 0
        self.submithook(x)
        self.delete(0, 'end')

    def previous_back(self, *b):
        self.previous_step(-1)

    def previous_forward(self, *b):
        self.previous_step(1)

    def previous_step(self, direction):
        self.previousinputstep += direction
        if abs(self.previousinputstep) > len(self.previousinputs):
            self.previousinputstep -= direction
            return
        self.delete(0, 'end')
        if self.previousinputstep >= 0:
            self.previousinputstep = 0
            return
        self.insert(0, self.previousinputs[self.previousinputstep])

class InterpreterWindow(tkinter.Frame):
    def __init__(self, master, module, *args, **kwargs):
        super(InterpreterWindow, self).__init__(master, *args, **kwargs)

        self.module = module

        self.frame = tkinter.Frame(master, height=512)
        self.display = tkinter.Label(self.frame, anchor='sw', justify='left', font=('Terminal',10))
        self.display.configure(wraplength=self.display.winfo_width(), bg='#272822', fg='#e6db74')
        self.input = EntryWithHistory(self.frame, self.input_text, font=('Terminal', 10), bg='#000', fg='#e6db74')
        self.input.configure(insertbackground='#e6db74')
        
        self.frame.bind('<Configure>', self.update_wraplength)

        self.display_buffer = ['wtf', 'w']
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.display.grid(row=0, column=0, sticky='news')
        self.input.grid(row=1, column=0, sticky='ew')
        master.update()
        self.frame.pack_propagate(0)
        self.frame.grid_propagate(0)

        self.update_display()

    def update_display(self):
        display = '\n'.join(self.display_buffer)
        self.display.configure(text=display)
        self.display.update()

    def input_text(self, text):
        text = text.strip()
        if text is '':
            return
        d = '>>> ' + text
        self.display_buffer.append(d)
        self.update_display()
        self.input.configure(state='disabled')
        self.input.update()
        self.module.execit(text)
        self.input.configure(state='normal')

    def update_wraplength(self, *trash):
        self.display.configure(wraplength=self.display.winfo_width())

    def syshub_receiver(self, text):
        text = text.strip()
        if text is '':
            return
        self.display_buffer.append(text)
        self.update_display()

    def previous_back(self, *b):
        self.previous_step(-1)

    def previous_forward(self, *b):
        self.previous_step(1)

    def previous_step(self, direction):
        self.previousinputstep += direction
        if abs(self.previousinputstep) > len(self.previousinputs):
            self.previousinputstep -= direction
            return
        self.input.delete(0, 'end')
        if self.previousinputstep >= 0:
            self.previousinputstep = 0
            return
        self.input.insert(0, self.previousinputs[self.previousinputstep])

    def pack(self, *args, **kwargs):
        self.frame.pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)

    def place(self, *args, **kwargs):
        self.frame.place(*args, **kwargs)

class QuadTK:
    def __init__(self):
        self.windowtitle = 'QuadTK'

        self.t = tkinter.Tk()
        self.t.title(self.windowtitle)
        self.w = 800
        self.h = 525
        self.screenwidth = self.t.winfo_screenwidth()
        self.screenheight = self.t.winfo_screenheight()
        self.windowwidth = self.w
        self.windowheight = self.h
        self.windowx = (self.screenwidth-self.windowwidth) / 2
        self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
        self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
        self.t.geometry(self.geometrystring)

        self.build_gui_manager()

        self.t.mainloop()

p = sys.path[0]

sys.path[0] = 'C:/git/reddit/subredditbirthdays/'
import sb
sys.path[0] = 'C:/git/reddit/usernames/'
import un
sys.path[0] = 'C:/git/reddit/t3/'
import t3

t = tkinter.Tk()
t.columnconfigure(0, weight=1)
t.rowconfigure(0, weight=1)
t.rowconfigure(1, weight=1)
t.rowconfigure(2, weight=1)

sbi = InterpreterWindow(t, sb)
sbi.grid(row=0, column=0, sticky='news')
syshub.register(module=sb, calltype='out', method=sbi.syshub_receiver)

uni = InterpreterWindow(t, un)
uni.grid(row=1, column=0, sticky='news')
syshub.register(module=un, calltype='out', method=uni.syshub_receiver)

t3i = InterpreterWindow(t, t3)
t3i.grid(row=2, column=0, sticky='news')
syshub.register(module=t3, calltype='out', method=t3i.syshub_receiver)

t.mainloop()