import tkinter
from PIL import Image
from PIL import ImageTk

t=tkinter.Tk()


im = Image.open('images/swirl_00.png')
im = ImageTk.PhotoImage(im)
l = tkinter.Label(t, text="heyo", image=im)
l.im = im
l.pack()

t.mainloop()
