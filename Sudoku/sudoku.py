import tkinter
import random
import sudoku_generator

class Sudoku:
	def __init__(self):
		self.t = tkinter.Tk()
		self.t.title("Sudoku")
		self.t.resizable(0,0)

		self.color_enterbox = "#555"
		self.color_entertext = "#fff"
		self.color_background = "#222"
		self.color_helptext = "#ccc"
		self.color_incorrecttext = "#f00"
		self.color_giventext = "#7f7"
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
		self.entities_stringvar = []

		self.create_boxes()

		self.t.bind("<KeyPress>", self.keypress)
		self.keypress_movement = {
		"w":[0, -1],
		"s":[0, 1],
		"a":[-1, 0],
		"d":[1, 0]}

		self.key_clearcurrent = ["e"]
		self.key_grade = ["\r"]

		print('Creating puzzle')
		self.entries_solution = sudoku_generator.cgimain()[0]
		for pos in range(len(self.entries_solution)):
			self.entries_solution[pos] += 1
		self.entries_given = self.entries_solution[:]
		for pos in range(len(self.entries_given)):
			if random.randint(0, 100) <= 50:
				self.entries_given[pos] = None
		#self.entries_given = self.entries_solution[1]
		#self.entries_solution = self.entries_solution[0]
		self.entries_current = []

		self.apply_given()

		self.cursor_position = [0,0]
		self.select_entry_by_pos(self.cursor_position)
		self.game_win = False
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
		elif event.char in self.key_grade:
			self.grade()

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
				
				enter.is_permanent = False
				enter.stringvar.is_permanent = False
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
				self.entities_stringvar.append(enter.stringvar)
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
		if stringvar.is_permanent:
			index = self.entities_stringvar.index(stringvar)
			stringvar.set(self.entries_solution[index])
			self.entities_entry[index].configure(fg=self.color_giventext)
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
		#print(self.cursor_position)

	def generate_puzzle(self):
		return [random.randint(1, 8) for x in range(81)]

	def reset_colors(self):
		for enterbox in self.entities_entry:
			if not enterbox.is_permanent:
				enterbox.configure(fg=self.color_entertext)

	def apply_given(self):
		for givenpos in range(len(self.entries_given)):
			given = self.entries_given[givenpos]
			if given:
				self.entities_entry[givenpos].is_permanent = True
				self.entities_stringvar[givenpos].is_permanent = True
				self.checkinput(self.entities_stringvar[givenpos])
				self.entities_entry[givenpos].configure(fg=self.color_giventext)

	def grade(self):
		self.entries_current = []
		self.reset_colors()

		self.game_win = True
		self.has_errors = False

		for enterbox_index in range(len(self.entities_entry)):
			enterbox = self.entities_entry[enterbox_index]
			cell = enterbox.get()
			try:
				cell = int(cell)
				if cell != self.entries_solution[enterbox_index]:
					self.game_win = False
					self.has_errors = True
					enterbox.configure(fg=self.color_incorrecttext)
			except:
				self.game_win = False
				pass
			if cell == '':
				cell = 0
			self.entries_current.append(cell)

		if self.game_win:
			print("WOOOOO")

		elif not self.has_errors:
			print('Doing well')
		else:
			print('Some mistakes')

		#print(self.entries_solution)
		#print(self.entries_current)


soduku = Sudoku()
