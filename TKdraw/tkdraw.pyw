import tkinter

class TKDraw():
	def __init__(self):
		self.windowtitle = 'Tkdraw'

		self.ismousedown = False
		self.minwidth = 1
		self.maxwidth = 5

		self.t = tkinter.Tk()
		self.t.title(self.windowtitle)
		self.w = 450
		self.h = 350
		self.screenwidth = self.t.winfo_screenwidth()
		self.screenheight = self.t.winfo_screenheight()
		self.windowwidth = self.w
		self.windowheight = self.h
		self.windowx = (self.screenwidth-self.windowwidth) / 2
		self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
		self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
		self.t.geometry(self.geometrystring)

		self.canvas = tkinter.Canvas(self.t, bg='#000')
		self.canvas.pack(expand=True, fill='both')
		#print(help(self.canvas.bind))
		self.canvas.bind('<ButtonPress>', self.mousedown)
		self.canvas.bind('<ButtonRelease>', self.mouseup)
		self.canvas.bind('<Motion>', self.mousedraw)
		self.prevx = None
		self.prevy = None

	def mainloop(self):
		self.t.mainloop()

	def mousedown(self, *b):
		self.ismousedown = True

	def mouseup(self, *b):
		self.ismousedown = False
		self.prevx = None
		self.prevy = None

	def mousedraw(self, event):
		if self.ismousedown is False:
			return
		x = event.x
		y = event.y
		if self.prevx is not None:
			distance = ((self.prevx - x)**2) + ((self.prevy - y) ** 2)
			distance = distance ** 0.5
			distance = max(self.minwidth, distance)
			distance = min(self.maxwidth, distance)
			self.canvas.create_line(self.prevx, self.prevy, x, y, width=distance, fill='#fff')
		self.prevx = x
		self.prevy = y

tkd = TKDraw()
tkd.mainloop()