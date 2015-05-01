import tkinter

class DataPoint:
	def __init__(self, width=720, height=480):
		self.windowtitle = 'DataPoint'

		self.t = tkinter.Tk()
		self.t.title(self.windowtitle)
		self.w = width
		self.h = height
		self.screenwidth = self.t.winfo_screenwidth()
		self.screenheight = self.t.winfo_screenheight()
		self.windowwidth = self.w
		self.windowheight = self.h
		self.windowx = (self.screenwidth-self.windowwidth) / 2
		self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
		self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
		self.t.geometry(self.geometrystring)

		self.reset_attributes()

		self.margin = 0.10
		self.c = tkinter.Canvas(self.t)
		self.c.pack(fill='both', expand=True)
		
		self.clear()

	def mainloop(self):
		self.t.mainloop()

	def reset_attributes(self):
		'''
		Set the DataPoint's grid attributes back to None
		so that they will be recalculated during the next plot
		'''
		self.lowestx = None
		self.highestx = None
		self.lowesty = None
		self.highesty = None
		self.spanx = None
		self.spany = None
		self.marginx = None
		self.marginy = None
		self.drawablew = None
		self.drawableh = None

	def clear(self):
		self.c.delete('all')

	def meow(self):
		return 'meow.'

	def function(self, x):
		x -= 50
		x *= 0.1
		y = 1 / (1 + (2.718 ** -x))
		return y

	def verifypoints(self, points):
		for item in points:
			if len(item) != 2:
				raise Exception('%s Incorrect number of values for coordinate. Use help(plotpoints)' % str(item))
			for subitem in item:
				try:
					int(subitem)
				except ValueError as e:
					if not e.args:
						e.args = ('',)
					e.args += ('Invalid format. Use help(plotpoints',)
					raise

	def plotpoints(self, points, pointdiameter=4, fill='#000'):
		'''
		Plot points onto the canvas
		var points = list, where each element is a 2-length list, where [0] is x and [1] is y coordinate
		var pointdiameter = int for how wide the plotted point should be, in pixels
		'''
		self.verifypoints(points)

		if self.lowestx is None:
			xs = [point[0] for point in points]
			ys = [point[1] for point in points]
			self.lowestx = min(xs)
			self.highestx = max(xs)
			self.lowesty = min(ys)
			self.highesty = max(ys)
			del xs
			del ys

			self.spanx = abs(self.highestx - self.lowestx)
			self.spany = abs(self.highesty - self.lowesty)
			if self.spanx == 0:
				self.spanx = 1
			if self.spany == 0:
				self.spany = 1

			self.marginx = self.w * self.margin
			self.marginy = self.h * self.margin
			self.drawablew = self.w - (2 * self.marginx)
			self.drawableh = self.h - (2 * self.marginy)

		for point in points:
			# Get percentage of the span
			x = ((point[0]) - self.lowestx) / self.spanx
			y = ((point[1]) - self.lowesty) / self.spany
			# Flip y
			y = 1 - y
			# Use the percentage to get a location on the board
			x *= self.drawablew
			y *= self.drawableh
			# Put into center
			x += self.marginx
			y += self.marginy

			r = pointdiameter / 2
			self.c.create_oval(x-r, y-r, x+r, y+r, fill=fill)
			self.c.update()
			#print(point, x, y)

if __name__ == '__main__':
	dp = DataPoint()
	points = list(range(100))
	points = [[p, dp.function(p)] for p in points]
	dp.plotpoints(points)
	dp.mainloop()