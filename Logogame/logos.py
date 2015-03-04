import os
import tkinter
import sqlite3
import hashlib
import string
from PIL import Image
from PIL import ImageTk

class Generic:
	def __init__(self):
		pass
	def set_dict_attributes(self, attributes):
		for attribute in attributes:
			setattr(self, attribute, attributes[attribute])

class LogoGame:
	def __init__(self):
		self.WINDOWS_BADCHARS = '\\/?:*"><|'
		self.t = tkinter.Tk()
		self.t.title('Logogame')
		self.tkinter_elements = []
		if not os.path.exists('logos.db'):
			print('You\'re missing the game\'s logo database!')
			print('Cannot proceed!')
			quit()

		self.font_main = ('Consolas', 12)
		self.font_small = ('Consolas', 8)
		self.color_blue = '#0ed'
		self.color_green = '#31f13a'
		self.color_red = '#e23939'

		self.sql = sqlite3.connect('logos.db')
		self.cur = self.sql.cursor()
		self.stats_main = self.stats_load('stats')
		self.playerstats_load(self.stats_main.playername)

		self.w = 1062
		self.h = 600
		self.screenwidth = self.t.winfo_screenwidth()
		self.screenheight = self.t.winfo_screenheight()
		self.windowwidth = self.w
		self.windowheight = self.h
		self.windowx = (self.screenwidth-self.windowwidth) / 2
		self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
		self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
		self.t.geometry(self.geometrystring)

		self.uirefresher = self.buildui_main
		self.buildui_main()

		self.t.bind('<Configure>', self.update_wh)

		self.t.mainloop()

	def update_wh(self, *b):
		oldw = self.w
		oldh = self.h
		self.w = self.t.winfo_width()
		self.h = self.t.winfo_height()
		if oldw != self.w or oldh != self.h:
			pass
			#self.uirefresher()

	def destroy_all_elements(self):
		while len(self.tkinter_elements) > 0:
			self.tkinter_elements[0].destroy()
			del self.tkinter_elements[0]

	def buildui_main(self, *b):
		self.destroy_all_elements()
		x = self.w
		y = self.h

		self.button_playgame = tkinter.Button(
			self.t,
			text='Play',
			#relief='flat',
			font=self.font_main,
			bg=self.color_green,
			activebackground=self.color_green,
			command=self.buildui_game)
		self.button_playgame.grid(row=10, column=5)

		self.label_playername = tkinter.Label(self.t, text='Player name: ', font=self.font_main)
		self.label_playername.grid(row=30, column=4)

		self.entry_playername = tkinter.Entry(
			self.t,
			font=self.font_main,
			relief='solid',
			width=30)
		self.entry_playername.bind('<Return>', lambda x: self.playername_set(self.entry_playername.get()))
		self.entry_playername.insert(0, self.stats_main.playername)
		self.entry_playername.grid(row=30, column=5)

		self.button_playername = tkinter.Button(
			self.t, 
			text='Set', 
			font=self.font_small,
			#relief='flat', 
			bg=self.color_blue, 
			activebackground=self.color_blue,
			command=lambda: self.playername_set(self.entry_playername.get()))
		self.button_playername.grid(row=30, column=6)

		self.label_playerhash = tkinter.Label(self.t, text=self.sha8(self.stats_main.playername),
			font=self.font_main)
		self.label_playerhash.grid(row=30, column=7)

		self.tkinter_elements.append(self.button_playgame)
		self.tkinter_elements.append(self.label_playername)
		self.tkinter_elements.append(self.entry_playername)
		self.tkinter_elements.append(self.button_playername)
		self.tkinter_elements.append(self.label_playerhash)

	def buildui_game(self, *b):
		self.destroy_all_elements()

		self.button_back = tkinter.Button(
			self.t,
			text='X',
			font=self.font_main,
			bg=self.color_red,
			activebackground=self.color_red,
			command=self.buildui_main)
		self.button_back.grid(row=0, column=0)

		self.tkinter_elements.append(self.button_back)

	def playername_set(self, newname):
		if newname != self.stats_main.playername:
			self.cur.execute('UPDATE stats SET value=? WHERE key="playername"', [newname])
			self.sql.commit()
			playerhash = self.playerstats_load(newname)
			self.stats_main.playername = newname

			if self.label_playerhash:
				self.label_playerhash.configure(text=playerhash)
		print('Name: ' + self.stats_main.playername)

	def sha8(self, text):
		sha = hashlib.sha256()
		sha.update(text.encode('utf-8'))
		sha = sha.hexdigest()
		return sha[:8]

	def getnext(self):
		pass

	def png_load(self, filename, resize=None):
		if filename[-4:] != '.png':
			filename = filename + '.png'
		i = Image.open(filename)
		if resize:
			ratio = resize / max(i.size)
			newx = int(i.size[0] * ratio)
			newy = int(i.size[1] * ratio)
			i = i.resize([newx, newy])
		i = ImageTk.PhotoImage(i)
		return i

	def stats_load(self, database):
		if database == 'stats':
			self.cur.execute('SELECT * FROM stats')
			fetchall = self.cur.fetchall()
		if database == 'player':
			self.cur_player.execute('SELECT * FROM stats')
			fetchall = self.cur_player.fetchall()
		keyvals = {}
		for fetched in fetchall:
			keyvals[fetched[0]] = fetched[1]
		stats = Generic()
		stats.set_dict_attributes(keyvals)
		return stats

	def playerstats_load(self, playername, presha=False):
		if not presha:
			sha = self.sha8(playername)
		else:
			sha = playername
		filename = self.strip_to_filename(playername) + '_' + sha
		self.sql_player = sqlite3.connect('playerdata/%s.db' % filename)
		self.cur_player = self.sql_player.cursor()
		self.cur_player.execute('CREATE TABLE IF NOT EXISTS stats(key TEXT, value TEXT)')
		self.sql_player.commit()
		return sha

	def playerstats_set(self, key, value):
		self.cur_player.execute('SELECT * FROM stats WHERE key=?', [key])
		if cur.fetchone():
			self.cur_player.execute('UPDATE stats SET value=? WHERE key=?', [value, key])
		else:
			self.cur_player.execute('INSERT INTO stats VALUES(?, ?)', [key, value])
		self.sql_player.commit()

	def playerstats_get(self, key):
		self.cur_execute.execute('SELECT * FROM stats WHERE key=?', [key])
		f = cur.fetchone()
		if f:
			return f[1]
		return None

	def strip_to_filename(self, s):
		for badchar in self.WINDOWS_BADCHARS:
			s = s.replace(badchar, '')
		return s

logogame = LogoGame()