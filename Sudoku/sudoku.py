import tkinter

class Sudoku:
	def __init__(self):
		self.t = tkinter.Tk()
		self.t.title("Sudoku")
		self.t.resizable(0,0)

		self.color_enterbox = "#cfc"
		self.color_entertext = "#111"
		self.color_background = "#222"
		self.color_helptext = "#ccc"
		self.checkerboard_step = 2
		self.color_checkerboard = self.checkerboard(self.color_enterbox)

		self.font_enterbox = ["Consolas", 16]
		self.font_helptext = ["Consolas", 10]
		self.relief_enterbox = "ridge"
		# flat, groove, raised, ridge, solid, sunken
		self.docheckerboard = True

		self.allow_wraparound = True

		self.entry_square = 50
		self.spacer_width = 3
		self.misc_height = 0
		self.window_square = (9 * self.entry_square) + (2 * self.spacer_width)
		
		self.helptext = "W,A,S,D to easily move around; E to clear cell; Enter to grade"
		self.create_helptext(self.helptext)

		self.t.configure(width=self.window_square, height=self.window_square+self.misc_height)
		self.t.configure(bg=self.color_background)
		self.entities_entry = []

		self.permanents = []
		self.create_boxes()

		self.t.bind("<KeyPress>", self.keypress)
		self.keypress_movement = {
		"w":[0, -1],
		"s":[0, 1],
		"a":[-1, 0],
		"d":[1, 0]
		}
		self.key_clearcurrent = ["e"]

		self.cursor_position = [0,0]
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

	def create_helptext(self, helptext):
		helplabel = tkinter.Label(self.t, text=helptext)
		helplabel.configure(font=self.font_helptext,
							fg=self.color_helptext,
							bg=self.color_background,
							justify="left")
		
		height = (2.3 * self.font_helptext[1])
		height *= len(helptext.split('\n'))
		height += self.spacer_width
		print('Helptext added %d pixels in height' % height)
		self.misc_height += height
		helplabel.place(x=0, y=self.window_square + self.spacer_width)


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

				enter = tkinter.Entry(self.t)
				stringvar = tkinter.StringVar()

				enter.stringvar = stringvar
				enter.stringvar.trace("w", lambda name,index,mode, stringvar=stringvar: self.checkinput(stringvar))
				
				bg = self.color_enterbox
				relief = self.relief_enterbox
				if self.docheckerboard:
					docheckerboard = (str(x+y)[-1] in "13579")
					if docheckerboard:
						bg = self.color_checkerboard
				enter.configure(justify="c",
								textvariable=enter.stringvar,
								font=self.font_enterbox, 
								bg=bg, 
								fg=self.color_entertext,
								relief=relief)
				enter.bind("<Button-1>", self.update_position_byclick)
				enter.coordinates = [x, y]
				
				self.entities_entry.append(enter)
				enter.place(x=xpos, y=ypos, width=self.entry_square, height=self.entry_square)

	def checkerboard(self, hexivalue):
		hexivalue = hexivalue[1:]
		if len(hexivalue) == 3:
			r = hexivalue[0]
			g = hexivalue[1]
			b = hexivalue[2]
			padding = "1"
		if len(hexivalue) == 6:
			r = hexivalue[:2]
			g = hexivalue[2:4]
			b = hexivalue[4:]
			padding = "2"

		hexiout = "#"
		for colorcomponent in [r,g,b]:
			decivalue = int(colorcomponent, 16)
			if decivalue < self.checkerboard_step:
				decivalue += self.checkerboard_step
			else:
				decivalue -= self.checkerboard_step

			formatstring = "%0" + padding + "x"
			hexivalue = formatstring % decivalue
			hexiout += hexivalue
		return hexiout

	def checkinput(self, *bullish):
		stringvar = bullish[0]
		stringvalue = stringvar.get()
		try:
			test_for_integer= int(stringvalue)
			test_for_nonzero= 14/test_for_integer
		except:
			stringvar.set("")
		if len(stringvalue) > 1:
			stringvar.set(stringvalue[0])

	def update_position_byclick(self, event):
		enter = event.widget
		x = enter.coordinates[0]
		y = enter.coordinates[1]
		self.cursor_position = [x,y]

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
		hasmoved = False
		if (xposition > 0 or xdirection == 1) and (xposition < 8 or xdirection == -1) and (xdirection != 0):
			xposition += xdirection
			hasmoved = True
		if (yposition > 0 or ydirection == 1) and (yposition < 8 or ydirection == -1) and (ydirection != 0):
			yposition += ydirection
			hasmoved = True

		if self.allow_wraparound and hasmoved is False:
			if xposition == 0 and xdirection == -1:
				xposition = 8
			elif xposition == 8 and xdirection == 1:
				xposition = 0

			elif yposition == 0 and ydirection == -1:
				yposition = 8
			elif yposition == 8 and ydirection == 1:
				yposition = 0

		self.cursor_position = [xposition, yposition]
		self.select_entry_by_pos(self.cursor_position)
		print(self.cursor_position)


soduku = Sudoku()
