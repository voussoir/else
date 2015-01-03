import tkinter

class Marketeer:
	def __init__(self):
		self.t = tkinter.Tk()
		self.t.grid_propagate(0)
		self.t.title("Marketeer")
		
		self.multiplier = 1.15
		self.current = tkinter.StringVar()
		self.entry = tkinter.Entry(self.t, textvariable=self.current)
		self.entry.configure(relief="flat")
		self.entry.place(x=40, y=40)
		self.entry.bind("<Return>", self.clear)
		self.entry.focus_set()
		self.current.trace("w", self.update)

		self.output = tkinter.Label(self.t)
		self.output.place(x=30, y=90)

		self.dolladollabill = tkinter.Label(self.t, text="$")
		self.dolladollabill.place(x=30, y=40)
		self.indicator = tkinter.Label(self.t, text="x %0.2f"%self.multiplier)
		self.indicator.place(x=60, y=64)
		self.isreversed = tkinter.IntVar()
		self.reversal = tkinter.Checkbutton(self.t, variable=self.isreversed, command=self.updatemultiplier)
		self.reversal.place(x=110, y=64)
		self.t.mainloop()

	def update(self, *bull):
		current = self.current.get()
		try:
			current = float(current)
			current *= self.multiplier
			current = "$ %0.3f"% round(current, 2)
			self.output.configure(text=current)
		except:
			pass
		if current == "":
			self.output.configure(text="")

	def updatemultiplier(self, *bull):
		rev = self.isreversed.get()
		if rev == 1:
			self.multiplier = (1 / 1.15)
		else:
			self.multiplier = 1.15
		self.indicator.configure(text="x %0.2f" % self.multiplier)
		self.update()

	def clear(self, *bull):
		self.entry.delete(0, "end")

marketeer = Marketeer()