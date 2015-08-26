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
t = tkinter.Tk()
e=EntryWithHistory(t, print)
e.pack()
t.mainloop()