import spinal
import tkinter

class Path:
	def __init__(self, src='', dst='', overwrite=False, precalcsize=False):
		self.src = src
		self.dst = dst
		self.overwrite = overwrite
		self.precalcsize = precalcsize
	def __str__(self):
		return 'Path: %s -> %s' % (self.src, self.dst)

class SpinalClient:
	def __init__(self):
		self.windowtitle = 'Spinal'

		self.font_large = ("Consolas", 16)
		self.font_med = ("Consolas", 12)
		self.font_small = ("Consolas", 10)

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
		self.geometrystring = '%dx%d+%d+%d' % (
			 self.windowwidth, self.windowheight, self.windowx, self.windowy)
		self.t.geometry(self.geometrystring)

		self.panes_main = tkinter.PanedWindow(self.t, orient='vertical',
						  sashrelief='raised', sashpad=8)
		self.panes_main.pack(expand=True, fill='both')

		### FRAME_CONFIG ###
		#
		self.frame_config = tkinter.Frame(self.t)
		self.button_configload = tkinter.Button(self.frame_config,text='Load')
		self.button_configload.grid(row=0, column=0)
		self.button_configload.configure(bg="#6fd5f6", 
			 activebackground="#6fd5f6", relief="flat", width=4)
		#
		self.enter_configpath = tkinter.Entry(self.frame_config)
		self.enter_configpath.grid(row=0, column=1, sticky='nesw')
		self.enter_configpath.configure(font=self.font_small)
		#
		self.button_configsave = tkinter.Button(self.frame_config,text='Save')
		self.button_configsave.grid(row=0, column=2)
		self.button_configsave.configure(bg="#76E22E", 
			 activebackground="#46E22E", relief="flat", width=4)
		#
		### END FRAME_CONFIG ###


		### FRAME_PRIMARY ###
		#
		self.frame_primary = tkinter.Frame(self.t)
		self.paths = []
		#
		### END FRAME_PRIMARY ###
		tkinter.Grid.columnconfigure(self.frame_config, 1, weight=10)
		self.panes_main.add(self.frame_config)
		self.panes_main.add(self.frame_primary)

	def mainloop(self):
		self.t.mainloop()

	def add_pathline(self):
		pass

if __name__ == '__main__':
	s = SpinalClient()
	s.mainloop()