#29 October 11:34
import threading
import tkinter
from tkinter import Tk, Label, Frame
import random

class dodgygame:
	def __init__(self):
		tkvar = Tk()
		tkvar.resizable(0,0)
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

		self.phantlabel = Label(self.labelframe, text='0',font=('Consolas', 10),  bg="#ccc")
		self.phantlabel.grid(row=0, column=3)

		self.poslabel = Label(self.labelframe, text=str(self.xpos) + " " + str(self.ypos), font=('Consolas', 10))
		self.poslabel.grid(row=0, column=4)

		self.helplabel = Label(tkvar, text="Press H for help ->", font=('Consolas', 8))
		self.helplabel.grid(row=2, column=0, columnspan=100)

		self.consolelabel = Label(tkvar, text="Welcome", font=("Terminal", 8), width=arenasize, height=4)
		self.consolelabeldata = []
		self.consolelabel.configure(anchor="nw", justify="left")
		self.consolelabel.grid(row=3, column=0)

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
		tkvar.bind('x', lambda data=self.data: spawnphantom())
		tkvar.bind('r', lambda data=self.data: restart())
		tkvar.bind('h', lambda data=self.data: helpreel())
		tkvar.bind('<Control-w>', quit)
		self.candylist = []
		self.enemylist = []
		self.bomblist = []
		self.phantomlist = []
		self.goldcandylist = []
		self.entlist = []
		self.symbols = {'char':'H', 'wall':'#', 'floor':' '}

		self.stepstaken = 0
		self.isdeath = False

		self.candyspawnrate = 4
		self.collections = 0

		self.enemyspawnrate = 50
		self.enemyspawnmindist = 9
		self.enemydocollide = False

		self.bombs = 0
		self.bombcost = 4
		self.phantomcost = 60

		self.goldcandyflashrate = 8
		self.goldcandyspawnrate = 40
		self.goldcandyspawnrand = 4

		self.helplabelindex = -1
		self.helplabeltexts = [
		"<WASD>=Movement <J>=Bomb <K>=Phantom <R>=Restart ->", 
		"<UDLR>=Movement <Z>=Bomb <X>=Phantom <R>=Restart ->",
		"<LMB>=Movement <RMB>=Bomb <MMB>=Phantom/Restart ->",
		self.symbols['char'] + " = You ->",
		enemy.symbol + " = Exclamator ->",
		candy.symbol + " = Candy ->",
		bomb.symbol + " = Bomb ->",
		"Avoid the Exclamators ->",
		"Collect candy to earn bombs ->",
		"Drop bombs to snare Exclamators ->",
		"Deploy phantoms to distract Exclamators ->",
		"Phantoms have a minimum cost of " + str(self.phantomcost) + " ->",
		"But deploying phantom will consume all candy ->",
		"More candy consumed = longer phantom lifespan ->",
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

				for candies in self.candylist:
					if candies.x == self.xpos and candies.y == self.ypos:
						#print('Collection')
						collect(1)
						self.candylist.remove(candies)
						self.entlist.remove(candies)
						del candies

				for goldcandies in self.goldcandylist:
					if goldcandies.x == self.xpos and goldcandies.y == self.ypos:
						tempvar = '[ ' + goldcandy.symbol + ' ] Got gold'
						print(tempvar)
						printr(tempvar)
						collect(5)
						self.goldcandylist.remove(goldcandies)
						self.entlist.remove(goldcandies)

				for enemies in self.enemylist:
					if enemies.x == self.xpos and enemies.y == self.ypos:
						tempvar = '[ ' + self.symbols['char'] + ' ] Death'
						print(tempvar)
						printr(tempvar)
						self.isdeath = True
						self.datalabel.configure(fg='Red')

			if not self.isdeath:
				if hasmoved:
					self.stepstaken += 1
					if self.stepstaken % self.candyspawnrate == 0:
						spawncandy()

					goldchance = random.randint(self.stepstaken-self.goldcandyspawnrand, self.stepstaken+self.goldcandyspawnrand)
					#print(goldchance)
					if goldchance % self.goldcandyspawnrate == 0:
						spawngoldcandy()
					if self.stepstaken % self.enemyspawnrate == 0:
						spawnenemy()
						for x in range(self.stepstaken // 200):
							spawnenemy()

					for en in self.enemylist:
						oldx = en.x
						oldy = en.y
						if self.phantomlist == []:
							en.approach(self.xpos, self.ypos)
						else:
							ph = self.phantomlist[0]
							en.approach(ph.x, ph.y)
						if self.enemydocollide:
							for otheren in self.enemylist:
								if en != otheren:
									if en.x == otheren.x and en.y == otheren.y:
										tempvar = '[ '+enemy.symbol+' ] Enemy collision at '+str(en.x)+' '+str(en.y)
										print(tempvar)
										printr(tempvar)
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

					for goldcandies in self.goldcandylist:
						goldcandies.tick(self.goldcandyflashrate)
						if goldcandies.lifespan <= 0:
							self.goldcandylist.remove(goldcandies)
							self.entlist.remove(goldcandies)
							del goldcandies

				for bombs in self.bomblist:
					for enemies in self.enemylist:
						if enemies.x == bombs.x and enemies.y == bombs.y:
							self.bomblist.remove(bombs)
							self.enemylist.remove(enemies)
							self.entlist.remove(bombs)
							self.entlist.remove(enemies)
							tempvar = '[ ' + bomb.symbol + ' ] Bang'
							print(tempvar)
							printr(tempvar)
							mfresh()

			self.data = [self.symbols['wall']*arenasize, self.symbols['wall']*arenasize]
			for x in range(arenasize-2):
				self.data[1:1] = [self.symbols['wall'] + self.symbols['floor']*(arenasize-2) + self.symbols['wall']]
			for ycoord in range(len(self.data)):
				yl = self.data[ycoord]
				if ycoord == self.ypos and not self.isdeath:
					#print(ycoord)
					yl = yl[:self.xpos] + self.symbols['char'] + yl[self.xpos+1:]
					#print(yl)
				self.entlist.sort(key=lambda p: p.x)
				for entities in self.entlist:
					if entities.y == ycoord:
						yl = yl[:entities.x] + entities.symbol + yl[entities.x+1:]
				self.data[ycoord] = yl


			self.datalabel.configure(text='\n'.join(self.data))
			self.stepslabel.configure(text="%04d"%(self.stepstaken) + " steps")
			self.collectlabel.configure(text="%03d"%(self.collections) + " candy")
			self.bomblabel.configure(text="%02d"%(self.bombs) + " bombs")
			self.poslabel.configure(text="%02d"%(self.xpos) + " " + "%02d"%(self.ypos))
			if self.collections >= self.phantomcost:
				self.phantlabel.configure(text='1 phantom')
			else:
				self.phantlabel.configure(text='0 phantom')

		def printr(info):
			self.consolelabeldata.append(str(info))
			self.consolelabeldata = self.consolelabeldata[-4:]
			self.consolelabel.configure(text='\n'.join(self.consolelabeldata))


		def translatemouse(event, middlemouse=False):
			event.x -= 9
			event.y -= 9
			#485

			event.x /= 8
			event.y /= 12
			#spawncandy(round(event.x), round(event.y))
			#print(event.x, event.y)
			xdif = event.x - self.xpos
			ydif = event.y - self.ypos
			if abs(xdif) >= 0.5 or abs(ydif) >= 0.5:
				if abs(xdif) >= abs(ydif):
					xdif /= abs(xdif)
					xdif = int(xdif)
					mfresh(xmove= xdif)
				else:
					ydif /= abs(ydif)
					ydif = int(ydif)
					mfresh(ymove= ydif)

		def middlemouse():
			if self.isdeath:
				restart()
			else:
				spawnphantom()
		tkvar.bind('<Button-1>', translatemouse)
		tkvar.bind('<Button-2>', lambda data=self.data: middlemouse())
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
				tempvar='[ ' + self.symbols['char'] + ' ] Not enough Candy. ' + str(self.collections) + '/' + str(self.phantomcost) + '. -' + str(self.phantomcost-self.collections)
				print(tempvar)
				printr(tempvar)
				goodtogo = False
			if self.phantomlist != []:
				goodtogo = False

			if goodtogo:
				life = 15
				self.collections = 0
				life += round(self.collections / 3)
				tempvar = '[ ' + self.symbols['char'] + ' ] New phantom with ' + str(life) + ' life'
				print(tempvar)
				printr(tempvar)
				newphantom = phantom(self.xpos, self.ypos, life)
				self.phantomlist.append(newphantom)
				self.entlist.append(newphantom)
				mfresh()

		def spawncandy(forcex=None, forcey=None):
			goodtogo = True
			if forcex == None or forcey == None:
				newx = random.randint(1, arenasize-2)
				newy = random.randint(1, arenasize-2)
			else:
				newx = forcex
				newy = forcey
			if self.xpos == newx and self.ypos == newy:
				goodtogo = False
			if goodtogo:
				for candies in self.candylist:
					if candies.x == newx and candies.y == newy:
						goodtogo = False
			if goodtogo:
				tempvar = '[ ' + candy.symbol + ' ] New candy at ' + str(newx)+' '+str(newy)
				print(tempvar)
				printr(tempvar)
				newcan = candy(newx, newy)
				self.candylist.append(newcan)
				self.entlist.append(newcan)
				mfresh()


		def spawngoldcandy(forcex=None, forcey=None):
			goodtogo = True
			if forcex == None or forcey == None:
				newx = random.randint(1, arenasize-2)
				newy = random.randint(1, arenasize-2)
				spawntries = 0
				while (dist(self.xpos, self.ypos, newx, newy) < self.enemyspawnmindist):
					newx = random.randint(1, arenasize-2)
					newy = random.randint(1, arenasize-2)
					spawntries += 1
					#print('Rerolling from', newx, newy)
					if spawntries == 20:
						#print('Could not spawn enemy')
						goodtogo = False
						break
			else:
				newx = forcex
				newy = forcey
			if goodtogo:
				for entity in self.entlist:
					if entity.x == newx and entity.y == newy:
						goodtogo = False
			if goodtogo:
				lifespan= dist(self.xpos, self.ypos, newx, newy)
				lifespan *= 2
				tempvar = '[ ' + goldcandy.symbol + ' ] New gold candy'
				print(tempvar)
				printr(tempvar)
				newcan = goldcandy(newx, newy, lifespan)
				self.goldcandylist.append(newcan)
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
				#print('Rerolling from', newx, newy)
				if spawntries == 10:
					print('Could not spawn enemy')
					goodtogo = False
					break

			if goodtogo:
				for ens in self.enemylist:
					if ens.x == newx and ens.y == newy:
						goodtogo = False
			if goodtogo:
				tempvar = '[ ' + enemy.symbol +  ' ] New enemy at '+str(newx)+' '+str(newy)
				print(tempvar)
				printr(tempvar)
				newen = enemy(newx, newy, 1)
				self.enemylist.append(newen)
				self.entlist.append(newen)
				mfresh()

		def restart():
			tempvar = 'Resetting game.'
			print(tempvar)
			printr(tempvar)
			self.consolelabeldata = []
			self.consolelabel.configure(text='')
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

class goldcandy:
    symbol = "$"
    def __init__(self, x, y, lifespan):
        self.x = x
        self.y = y
        self.lifespan = lifespan
        self.symbol = goldcandy.symbol
    def tick(self, flashrate):
        self.lifespan -= 1
        if self.lifespan % flashrate == 0 or self.lifespan % flashrate == 1:
            self.symbol = goldcandy.symbol
        else:
            self.symbol = candy.symbol

t = dodgygame()