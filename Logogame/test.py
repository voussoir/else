import tkinter
from PIL import Image
from PIL import ImageTk

t=tkinter.Tk()

def png(filename):
	im = Image.open('images/%s.png' % filename)
	im = ImageTk.PhotoImage(im)
	return im
	

im = png('jarate')
l = tkinter.Label(t, text="heyo", image=im)
l.im = im
l.pack()

t.mainloop()
