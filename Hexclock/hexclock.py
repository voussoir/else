import math
import tkinter
import time

SHIFT_SPEED = 0.2

degree = 359
r = 0
g = 0
b = 0

def cval(degree, hueshift):
    y = math.sin(math.pi*(degree+hueshift)/180)
    # Anything above 50% becomes 100%
    # 0 - 50% will scale as if it was 50 - 100%
    y = (y+0.5) * 256
    y = min(255, y)
    y = max(0, y)
    y = round(y)
    return y
    
def clocking():
    x = time.time()
    x *= SHIFT_SPEED
    r = cval(x, 90)
    g = cval(x, 210)
    b = cval(x, 330)
    rgb = '#%02x%02x%02x' % (r,g,b)
    #print(x, rgb)
    #t.configure(bg=rgb)
    l.configure(text=rgb, bg=rgb)
    t.after(50, clocking)

t = tkinter.Tk()
l = tkinter.Label(text='')
l.pack(expand=True, fill='both')
w = 450
h = 350
screenwidth = t.winfo_screenwidth()
screenheight = t.winfo_screenheight()
windowwidth = w
windowheight = h
windowx = (screenwidth-windowwidth) / 2
windowy = ((screenheight-windowheight) / 2) - 27
geometrystring = '%dx%d+%d+%d' % (windowwidth, windowheight, windowx, windowy)
t.geometry(geometrystring)
clocking()
t.mainloop()