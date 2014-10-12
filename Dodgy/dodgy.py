import tkinter
from tkinter import Tk, Label, Frame
import random

class tgame:
	def __init__(self):
		tkvar = Tk()
		tkvar.wm_title("Dodgy")
		tkvar.iconbitmap('Excl.ico')

		arenasize = 40
		self.xpos = int((arenasize-1)/2)
		self.ypos = int((arenasize-1)/2)

		self.data = ['#'*arenasize, '#'*arenasize]
		for x in range(arenasize-2):
			self.data[1:1] = ['#' + '.'*(arenasize-2) + '#']

		self.labelframe = Frame(tkvar)
		self.labelframe.grid(row=1, column=0, columnspan=100)
		#Allows me to center the gui units

		self.datalabel = Label(tkvar, text='\n'.join(self.data), font=('Terminal', 10))
		self.datalabel.grid(row=0, column=0, columnspan=100)

		self.stepslabel = Label(self.labelframe, text='0', font=('Consolas', 10))
		self.stepslabel.grid(row=0, column=0)

		self.collectlabel = Label(self.labelframe, text='0', font=('Consolas', 10), bg="#ccc")
		self.collectlabel.grid(row=0, column=1)

		self.bomblabel = Label(self.labelframe, text='0', font=('Consolas', 10))
		self.bomblabel.grid(row=0, column=2)

		self.poslabel = Label(self.labelframe, text=str(self.xpos) + " " + str(self.ypos), font=('Consolas', 10), bg="#ccc")
		self.poslabel.grid(row=0, column=3)

		self.helplabel = Label(tkvar, text="Press H for help ->", font=('Consolas', 8))
		self.helplabel.grid(row=2, column=0, columnspan=100)

		tkvar.bind('w', lambda data=self.data: mfresh(ymove=-1))
		tkvar.bind('<Up>', lambda data=self.data: mfresh(ymove=-1))
		tkvar.bind('s', lambda data=self.data: mfresh(ymove=1))
		tkvar.bind('<Down>', lambda data=self.data: mfresh(ymove=1))
		tkvar.bind('a', lambda data=self.data: mfresh(xmove=-1))
		tkvar.bind('<Left>', lambda data=self.data: mfresh(xmove=-1))
		tkvar.bind('d', lambda data=self.data: mfresh(xmove=1))
		tkvar.bind('<Right>', lambda data=self.data: mfresh(xmove=1))
		#tkvar.bind('c', lambda data=self.data: spawncandy())
		tkvar.bind('j', lambda data=self.data: spawnbomb())
		tkvar.bind('z', lambda data=self.data: spawnbomb())
		tkvar.bind('k', lambda data=self.data: spawnphantom())
		tkvar.bind('r', lambda data=self.data: restart())
		tkvar.bind('h', lambda data=self.data: helpreel())
		tkvar.bind('<Control-w>', quit)
		self.candylist = []
		self.enemylist = []
		self.bomblist = []
		self.phantomlist = []
		self.entlist = []
		self.symbols = {'char':'H', 'wall':'#', 'floor':' '}
		self.stepstaken = 0
		self.collections = 0
		self.bombs = 0

		self.enemyspawnrate = 50
		self.enemyspawnmindist = 6
		self.candyspawnrate = 4

		self.isdeath = False
		self.bombcost = 4
		self.phantomcost = 10
		self.helplabelindex = -1

		self.helplabeltexts = [
		"<WASD>=Movement <J>=Bomb <R>=Restart ->", 
		"<UDLR>=Movement <Z>=Bomb <R>=Restart ->",
		"<LMB>=Movement <RMB>=Bomb <MMB>=Restart ->",
		self.symbols['char'] + " = You ->",
		enemy.symbol + " = Exclamator ->",
		candy.symbol + " = Candy ->",
		bomb.symbol + " = Bomb ->",
		"Avoid the Exclamators ->",
		"Collect candy to earn bombs ->",
		"Drop bombs to snare Exclamators ->",
		"Enjoy •"]


		def mfresh(xmove=0, ymove=0):
			if not self.isdeath:
				#print(self.xpos, self.ypos, "==> ", end="")
				hasmoved = False
				if xmove != 0:
					if (self.xpos > 1 or xmove > 0) and (self.xpos < (arenasize -2) or xmove < 0):
						self.xpos += xmove
						if self.phantomlist != []:
							ph = self.phantomlist[0]
							ph.x -= xmove
							if ph.x < 1:
								ph.x = 1
							if ph.x > (arenasize-2):
								ph.x = arenasize-2
						hasmoved = True
				if ymove != 0:
					if (self.ypos > 1 or ymove > 0) and (self.ypos < (arenasize -2) or ymove < 0):
						self.ypos += ymove
						if self.phantomlist != []:
							ph = self.phantomlist[0]
							ph.y -= ymove
							if ph.y < 1:
								ph.y = 1
							if ph.y > (arenasize-2):
								ph.y = arenasize-2

						hasmoved = True
				if hasmoved:
					if self.phantomlist != []:
						ph = self.phantomlist[0]
						ph.lifespan -= 1
						if ph.lifespan <= 0:
							self.phantomlist.remove(ph)
							self.entlist.remove(ph)
							del ph
				#print(self.xpos, self.ypos, '|', self.stepstaken)
				self.data = [self.symbols['wall']*arenasize, self.symbols['wall']*arenasize]
				for x in range(arenasize-2):
					self.data[1:1] = [self.symbols['wall'] + self.symbols['floor']*(arenasize-2) + self.symbols['wall']]

				for ycoord in range(len(self.data)):
					yl = self.data[ycoord]
					if ycoord == self.ypos:
						#print(ycoord)
						yl = yl[:self.xpos] + self.symbols['char'] + yl[self.xpos+1:]
						#print(yl)

					cs = []
					for candies in self.candylist:
						if candies.y == ycoord:
							if candies.x == self.xpos and candies.y == self.ypos:
								print('Collection')
								collect(1)
								self.candylist.remove(candies)
								self.entlist.remove(candies)
								del candies

					for enemies in self.enemylist:
						if enemies.y == ycoord:
							if enemies.x == self.xpos and enemies.y == self.ypos:
								print('Death')
								self.isdeath = True
								self.datalabel.configure(fg='Red')

					self.entlist.sort(key=lambda p: p.x)
					for entities in self.entlist:
						if entities.y == ycoord:
							yl = yl[:entities.x] + entities.symbol + yl[entities.x+1:]
					self.data[ycoord] = yl

				if hasmoved:
					self.stepstaken += 1
					if self.stepstaken % self.candyspawnrate == 0:
						spawncandy()
					if self.stepstaken % self.enemyspawnrate == 0:
						spawnenemy()

					for en in self.enemylist:
						oldx = en.x
						oldy = en.y
						if self.phantomlist == []:
							en.approach(self.xpos, self.ypos)
						else:
							ph = self.phantomlist[0]
							en.approach(ph.x, ph.y)
						for otheren in self.enemylist:
							if en != otheren:
								if en.x == otheren.x and en.y == otheren.y:
									#print('Enemy collision at', en.x, en.y)
									en.x = oldx
									en.y = oldy
						#print(dist(en.x, en.y, self.xpos, self.ypos))
						if en.x < 1:
							en.x = 1
						if en.x > (arenasize-2):
							en.x = arenasize-2

						if en.y < 1:
							en.y = 1
						if en.y > (arenasize-2):
							en.y = arenasize-2
						mfresh()

				for bombs in self.bomblist:
					for enemies in self.enemylist:
						if enemies.x == bombs.x and enemies.y == bombs.y:
							self.bomblist.remove(bombs)
							self.enemylist.remove(enemies)
							self.entlist.remove(bombs)
							self.entlist.remove(enemies)
							print('Bang')
							mfresh()

				self.datalabel.configure(text='\n'.join(self.data))
				self.stepslabel.configure(text=str(self.stepstaken) + " steps")
				self.collectlabel.configure(text=str(self.collections) + " candy")
				self.bomblabel.configure(text=str(self.bombs) + " bombs")
				self.poslabel.configure(text=str(self.xpos) + " " + str(self.ypos))


		def translatemouse(event):
			event.x -= 6
			event.y -= 14
			#485

			event.x /= 8
			event.y /= 12
			#print(event.x, event.y)
			xdif = event.x - self.xpos
			ydif = event.y - self.ypos
			if abs(xdif) >= abs(ydif):
				xdif /= abs(xdif)
				xdif = int(xdif)
				mfresh(xmove= xdif)
			else:
				ydif /= abs(ydif)
				ydif = int(ydif)
				mfresh(ymove= ydif)
		tkvar.bind('<Button-1>', translatemouse)
		tkvar.bind('<Button-2>', lambda data=self.data: restart())
		tkvar.bind('<Button-3>', lambda data=self.data: spawnbomb())

		def helpreel():
			self.helplabelindex += 1
			if self.helplabelindex > (len(self.helplabeltexts) - 1):
				self.helplabelindex = 0
			self.helplabel.configure(text=self.helplabeltexts[self.helplabelindex])

		def collect(score):
			for x in range(score):
				self.collections += 1
				if self.collections % self.bombcost == 0:
					self.bombs += 1

		def spawnbomb():
			goodtogo = True
			for bombs in self.bomblist:
				if bombs.x == self.xpos and bombs.y == self.ypos:
					goodtogo = False
			if goodtogo:
				if self.bombs > 0:
					self.bombs -= 1
					newbomb = bomb(self.xpos, self.ypos)
					self.bomblist.append(newbomb)
					self.entlist.append(newbomb)
					mfresh()

		def spawnphantom():
			goodtogo = True
			if self.collections < self.phantomcost:
				goodtogo = False
			if self.phantomlist != []:
				goodtogo = False

			if goodtogo:
				life = 10
				self.collections = 0
				life += round(self.collections / 3)
				newphantom = phantom(self.xpos, self.ypos, life)
				self.phantomlist.append(newphantom)
				self.entlist.append(newphantom)
				mfresh()

		def spawncandy():
			newx = random.randint(1, arenasize-2)
			newy = random.randint(1, arenasize-2)
			goodtogo = True
			if self.xpos == newx and self.ypos == newy:
				goodtogo = False
			if goodtogo:
				for candies in self.candylist:
					if candies.x == newx and candies.y == newy:
						goodtogo = False
			if goodtogo:
				print('New candy at', newx, newy)
				newcan = candy(newx, newy)
				self.candylist.append(newcan)
				self.entlist.append(newcan)
				mfresh()

		def spawnenemy():
			newx = random.randint(1, arenasize-2)
			newy = random.randint(1, arenasize-2)
			goodtogo = True
			spawntries = 0
			while (dist(self.xpos, self.ypos, newx, newy) < self.enemyspawnmindist):
				newx = random.randint(1, arenasize-2)
				newy = random.randint(1, arenasize-2)
				spawntries += 1
				print('Rerolling from', newx, newy)
				if spawntries == 10:
					print('Could not spawn enemy')
					goodtogo = False
					break

			if goodtogo:
				for ens in self.enemylist:
					if ens.x == newx and ens.y == newy:
						goodtogo = False
			if goodtogo:
				print('New enemy at', newx, newy)
				newen = enemy(newx, newy, 1)
				self.enemylist.append(newen)
				self.entlist.append(newen)
				mfresh()

		def restart():
			self.xpos = int((arenasize-1)/2)
			self.ypos = int((arenasize-1)/2)
			while self.entlist != []:
				del self.entlist[0]
			self.candylist = []
			self.enemylist = []
			self.bomblist = []
			self.phantomlist = []
			self.entlist = []
			self.stepstaken = 0
			self.collections = 0
			self.bombs = 0
			self.isdeath = False
			spawncandy()
			self.datalabel.configure(fg='Black')
			mfresh()


		def dist(xa, ya, xb, yb):
			#distance formula
			result = (xa - xb) **2
			result += (ya - yb) ** 2
			result = result ** 0.5
			result = int(result)
			return result



		mfresh()
		spawncandy()
		tkvar.mainloop()

class candy:
	symbol = "@"
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.symbol = candy.symbol

class enemy:
	symbol = "!"
	def __init__(self, x, y, anger):
		self.symbol = enemy.symbol
		self.x = x
		self.y = y
		self.anger = anger
		self.movementx = 0
		self.movementy = 0

	def approach(self, targx, targy):
		hasmoved = False
		xdif = abs(targx - self.x)
		ydif = abs(targy - self.y)
		if xdif > ydif:
			if targx != self.x and hasmoved == False:
				self.movementx += int(((targx-self.x) / (abs(targx-self.x))))
				if self.movementx > 1:
					self.movementx = 1
				if self.movementx < -1:
					self.movementx = -1
		else:
			if targy != self.y and hasmoved == False:
				self.movementy += int(((targy-self.y) / (abs(targy-self.y))))
				if self.movementy > 1:
					self.movementy = 1
				if self.movementy < -1:
					self.movementy = -1
					
		if not hasmoved:
			self.x += self.movementx
		if not hasmoved:
			self.y += self.movementy

class bomb:
	symbol = "X"
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.symbol = bomb.symbol

class phantom:
	symbol = "H"
	def __init__(self, x, y, lifespan):
		self.x = x
		self.y = y
		self.lifespan  = lifespan
		self.symbol = phantom.symbol

t = tgame()