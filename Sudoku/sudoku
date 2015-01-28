import tkinter

class Sudoku:
	def __init__(self):
		self.t = tkinter.Tk()
		self.t.title("Sudoku")

		self.entry_square = 50
		self.spacer_width = 3
		self.cursor_position = [0,0]

		self.t.configure(width=9*self.entry_square, height=9*self.entry_square)
		self.t.configure(bg="#000")
		self.entities_entry = []
		self.create_boxes()

		self.t.bind("<KeyPress>", self.keypress)
		self.keypress_movement = {
		"w":[0, -1],
		"s":[0, 1],
		"a":[-1, 0],
		"d":[1, 0]
		}
		self.key_clearcurrent = ["e"]

		self.permanents[]

		self.select_entry_by_pos(self.cursor_position)
		self.t.mainloop()

	def keypress(self, event):
		movement = self.keypress_movement.get(event.char, None)
		if movement:
			self.move_cursor(movement)
			return

		if event.char in self.key_clearcurrent:
			x = self.cursor_position[0]
			y = self.cursor_position[1]
			index = (9 * y) + x
			self.entities_entry[index].delete(0, "end")

	def create_boxes(self):
		spacer_y = 0
		for y in range(9):
			if (y > 0) and (y % 3 == 0):
				spacer_y += self.spacer_width
			ypos = (y * self.entry_square) + spacer_y

			spacer_x = 0
			for x in range(9):
				if (x > 0) and (x % 3 == 0):
					spacer_x += self.spacer_width
				xpos = (x * self.entry_square) + spacer_x

				stringvar = tkinter.StringVar()
				enter = tkinter.Entry(self.t)
				enter.stringvar = stringvar
				enter.stringvar.trace("w", lambda name,index,mode, stringvar=stringvar: self.checkinput(stringvar))
				enter.configure(justify="c", textvariable=enter.stringvar)
				enter.configure(font= ("Consolas", 14))
				enter.name = "%d, %s" % (x,y)
				
				self.entities_entry.append(enter)
				enter.place(x=xpos, y=ypos, width=self.entry_square, height=self.entry_square)

	def checkinput(self, *bullish):
		stringvar = bullish[0]
		stringvalue = stringvar.get()
		try:
			int(stringvalue)
		except ValueError:
			stringvar.set("")
		if len(stringvalue) > 1:
			stringvar.set(stringvalue[0])

	def select_entry_by_pos(self, position):
		x = position[0]
		y = position[1]
		index = (9 * y) + x
		self.entities_entry[index].focus_set()

	def move_cursor(self, direction):
		xdirection = direction[0]
		ydirection = direction[1]

		xposition = self.cursor_position[0]
		yposition = self.cursor_position[1]
		if (xposition > 0 or xdirection >= 0) and (xposition < 8 or xdirection <= 0):
			xposition += xdirection
		if (yposition > 0 or ydirection >= 0) and (yposition < 8 or ydirection <= 0):
			yposition += ydirection

		self.cursor_position = [xposition, yposition]
		self.select_entry_by_pos(self.cursor_position)
		print(self.cursor_position)


soduku = Sudoku()
