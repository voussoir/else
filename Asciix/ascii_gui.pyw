import os
import tkinter
import ascii
import threading

help_file = """The file or URL to ASCII.
If you only put a name, it must be in the same
folder as this program. Otherwise, include a 
file path.
"""

help_resolution = """The characterpixel resolution.
Each ASCII character will represent x•y pixels
of the original image. 
Lower numbers produce higher detail.
"""

help_contrast = """The character smoothing.
At 1, the image may use all 95 characters.
At 2, the image may use every other character
At 3, every third character, etc.
Higher numbers produce flatter images."""

help_table = """The table of ASCII characters.
Full = all 95 characters
Min = 41 characters
Min may produce cleaner images from photos
Lower Smoothing to accommodate"""

help_blank = "\n\n\n\n"

class Ascii:
	def ticker(self, status):
		self.label_ticker.config(text=status)

	def startthread(self):
		self.processthread = threading.Thread(name="Ascii converter", target=self.start)
		self.processthread.daemon=True
		self.processthread.start()
		
	def start(self):
		self.enter_file.configure(bg="#fff")
		self.enter_file.configure(fg="#000")
		self.enter_resolution_x.configure(bg="#fff")
		self.enter_resolution_y.configure(bg="#fff")
		self.enter_contrast.configure(bg="#fff")
		filename = self.enter_file.get()
		xvalue = int(self.enter_resolution_x.get())
		yvalue = int(self.enter_resolution_y.get())
		contrast = int(self.enter_contrast.get())
		tickfunction = self.ticker
		try:
			ascii.ascii(filename, xvalue, yvalue, contrast, tickfunction, self.asciitable)
		except FileNotFoundError:
			self.enter_file.configure(bg="#f00")
			self.enter_file.configure(fg="#fff")
		if 'http' in filename and '/' in filename:
			filename = filename.split('/')[-1]
			self.enter_file.delete(0, 'end')
			self.enter_file.insert(0, filename)

	def generatehelp(self, helptype, label):
		def showhelp(self):
			label.configure(text=helptype)
		return showhelp

	def toggletable(self):
		if self.asciitable == ascii.asciitable:
			self.asciitable = ascii.asciitable_min
			self.button_asciitable.configure(text="Min")
		else:
			self.asciitable = ascii.asciitable
			self.button_asciitable.configure(text="Full")

	def clear(self):
		self.enter_file.configure(bg="#fff")
		self.enter_file.configure(fg="#000")
		self.enter_file.delete(0, 'end')
		self.enter_resolution_x.delete(0, 'end')
		self.enter_resolution_x.insert(0, '8')
		self.enter_resolution_y.delete(0, 'end')
		self.enter_resolution_y.insert(0, '17')
		self.enter_contrast.delete(0, 'end')
		self.enter_contrast.insert(0, '8')
		self.asciitable = ascii.asciitable
		self.button_asciitable.configure(text="Full")
		self.label_ticker.config(text="0.00")

	def __init__(self):
		self.t = tkinter.Tk()
		self.t.wm_title("ASCII")

		self.w = 400
		self.h = 275

		self.asciitable = ascii.asciitable

		self.centerframe = tkinter.Frame(self.t, width=self.w, height=self.h)
		self.centerframe.pack_propagate(0)
		self.centerframe.pack(expand=True)

		self.label_help = tkinter.Label(self.centerframe, text=help_blank)
		self.label_file = tkinter.Label(self.centerframe, text="File:")
		self.label_file.help = self.generatehelp(help_file, self.label_help)
		self.label_resolution = tkinter.Label(self.centerframe, text="Resolution:")
		self.label_resolution.help = self.generatehelp(help_resolution, self.label_help)
		self.label_contrast = tkinter.Label(self.centerframe, text="Smoothing:")
		self.label_contrast.help = self.generatehelp(help_contrast, self.label_help)
		self.label_ticker = tkinter.Label(self.centerframe, text="0.00")
		self.label_table = tkinter.Label(self.centerframe, text="Table: ")
		self.label_table.help = self.generatehelp(help_table, self.label_help)
		self.centerframe.help = self.generatehelp(help_blank, self.label_help)

		self.label_file.bind("<Motion>", self.label_file.help)
		self.label_resolution.bind("<Motion>", self.label_resolution.help)
		self.label_contrast.bind("<Motion>", self.label_contrast.help)
		self.centerframe.bind("<Motion>", self.centerframe.help)
		self.label_table.bind("<Motion>", self.label_table.help)

		self.enter_file = tkinter.Entry(self.centerframe, width=30)
		self.enter_resolution_x = tkinter.Spinbox(self.centerframe, from_=1, to=9999, width=5)
		self.enter_resolution_y = tkinter.Spinbox(self.centerframe, from_=1, to=9999, width=5)
		self.enter_resolution_x.delete(0, 'end')
		self.enter_resolution_y.delete(0, 'end')
		self.enter_resolution_x.insert(0, 8)
		self.enter_resolution_y.insert(0, 17)
		self.enter_contrast = tkinter.Spinbox(self.centerframe, from_=1, to=95, width=2)
		self.enter_contrast.delete(0, 'end')
		self.enter_contrast.insert(0, 8)
		self.button_start = tkinter.Button(self.centerframe, text="Go", command= self.startthread)
		self.button_start.configure(bg="#76E22E", activebackground="#46E22E", relief="flat", width=15)
		self.button_clear = tkinter.Button(self.centerframe, text="clear", command= self.clear)
		self.button_clear.configure(bg="#e23939", activebackground="#b82e2e", relief="flat", width=4)
		self.button_asciitable = tkinter.Button(self.centerframe, text="Full", command=self.toggletable)
		self.button_asciitable.configure(bg="#6fd5f6", activebackground="#6fd5f6", relief="flat", width=4)

		self.label_file.grid(row=0, column=0, sticky="e")
		self.enter_file.grid(row=0, column=1, sticky="w", columnspan=88)
		self.enter_file.focus_set()
		self.label_resolution.grid(row=1, column=0, sticky="e")
		self.enter_resolution_x.grid(row=1, column=1, sticky="w")
		self.enter_resolution_y.grid(row=1, column=2, sticky="w")
		self.label_contrast.grid(row=2, column=0, sticky="e")
		self.enter_contrast.grid(row=2, column=1, sticky="w")
		self.label_table.grid(row=3, column=0, sticky="e")
		self.button_asciitable.grid(row=3, column=1, sticky="w")
		self.label_ticker.grid(row=4, column=0, columnspan=88)
		self.button_start.grid(row=5, column=0, columnspan=88)
		self.button_clear.grid(row=5, column=87)
		self.label_help.grid(row=6, column=0, columnspan=88)


		self.screenwidth = self.t.winfo_screenwidth()
		self.screenheight = self.t.winfo_screenheight()
		self.windowwidth = self.w
		self.windowheight = self.h
		self.windowx = (self.screenwidth-self.windowwidth) / 2
		self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
		self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
		self.t.geometry(self.geometrystring)

		

		self.t.mainloop()

asciigui = Ascii()