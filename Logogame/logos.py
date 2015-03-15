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
		if not os.path.exists('logos.db'):
			print('You\'re missing the game\'s logo database!')
			print('Cannot proceed!')
			quit()

		self.font_main = ('Consolas', 12)
		self.font_small = ('Consolas', 8)
		self.color_blue = '#0ed'
		self.color_green = '#31f13a'
		self.color_red = '#e23939'

		self.logos_per_row = 6
		self.logo_padx = 10
		self.logo_pady = 10

		self.dbindex_id = 0
		self.dbindex_name = 1
		self.dbindex_solutions = 2
		self.dbindex_images = 3
		self.dbindex_tag = 4

		self.sql = sqlite3.connect('logos.db')
		self.cur = self.sql.cursor()
		self.stats_main = self.stats_load('stats')
		self.playerstats_load(self.stats_main.playername)

		self.tkinter_elements = []
		self.logo_elements = []
		self.tag_elements = []
		self.active_tags = set()
		self.all_tags = []
		self.all_logos = []
		self.logos_load()

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

		self.uirefresher = self.gui_build_main
		self.gui_build_main()

		#self.t.bind('<Configure>', self.update_wh)

		self.t.mainloop()

	def logos_load(self):
		self.all_logos = []
		self.cur.execute('SELECT * FROM logos')
		fetch = self.cur.fetchall()
		for item in fetch:
			logo = Generic()
			logo.id = item[self.dbindex_id]
			logo.images = item[self.dbindex_images].split(',')
			logo.name = item[self.dbindex_name]
			logo.solutions = item[self.dbindex_solutions].split(',')
			logo.tags = item[self.dbindex_tag].split(',')
			logo.solved = self.playerstats_hassolved(logo.id)
			self.all_logos.append(logo)
		self.all_tags = self.get_all_tags()
		self.all_tags.append('Completed')

	def destroy_all_elements(self):
		self.tag_elements = []
		self.destroy_all_logos()
		while len(self.tkinter_elements) > 0:
			self.tkinter_elements[0].destroy()
			del self.tkinter_elements[0]

	def destroy_all_logos(self):
		while len(self.logo_elements) > 0:
			self.logo_elements[0].destroy()
			del self.logo_elements[0]

	def gui_build_main(self, *b):
		self.destroy_all_elements()
		###
		self.frame_mainmenu = tkinter.Frame(self.t)
		self.frame_mainmenu.pack(expand=True, anchor='center')
		self.tkinter_elements.append(self.frame_mainmenu)
		#
		self.button_playgame = tkinter.Button(
			self.frame_mainmenu,
			text='Play',
			#relief='flat',
			font=self.font_main,
			bg=self.color_green,
			activebackground=self.color_green,
			command=self.gui_build_game)
		self.button_playgame.grid(row=10, column=5)
		self.tkinter_elements.append(self.button_playgame)
		#
		self.label_playername = tkinter.Label(
			self.frame_mainmenu,
			text='Player name: ',
			font=self.font_main)
		self.label_playername.grid(row=30, column=4)
		self.tkinter_elements.append(self.label_playername)
		#
		self.entry_playername = tkinter.Entry(
			self.frame_mainmenu,
			font=self.font_main,
			relief='solid',
			width=30)
		self.entry_playername.bind('<Return>', lambda x: self.playername_set(self.entry_playername.get()))
		self.entry_playername.insert(0, self.stats_main.playername)
		self.entry_playername.grid(row=30, column=5)
		self.tkinter_elements.append(self.entry_playername)
		#
		self.button_playername = tkinter.Button(
			self.frame_mainmenu, 
			text='Set', 
			font=self.font_small,
			#relief='flat', 
			bg=self.color_blue, 
			activebackground=self.color_blue,
			command=lambda: self.playername_set(self.entry_playername.get()))
		self.button_playername.grid(row=30, column=6)
		self.tkinter_elements.append(self.button_playername)
		#
		self.label_playerhash = tkinter.Label(
			self.frame_mainmenu,
			text=self.sha8(self.stats_main.playername),
			font=self.font_main)
		self.label_playerhash.grid(row=30, column=7)
		self.tkinter_elements.append(self.label_playerhash)
		###

	def gui_build_game(self, *b):
		self.destroy_all_elements()
		###
		self.frame_gametoolbar = tkinter.Frame(self.t)
		self.frame_gametoolbar.pack(fill='x', anchor='n')
		self.tkinter_elements.append(self.frame_gametoolbar)
		#
		self.button_back = tkinter.Button(
			self.frame_gametoolbar,
			text='X',
			font=self.font_main,
			bg=self.color_red,
			activebackground=self.color_red,
			command=self.gui_build_main)
		self.button_back.grid(row=0, column=0)
		self.tkinter_elements.append(self.button_back)
		#
		#self.frame_gamearea = tkinter.Frame(self.t, bg='#f00')
		#self.frame_gamearea.pack(expand=True, fill='both', anchor='w')
		#
		self.frame_posttoolbar = tkinter.Frame(self.t)
		self.frame_posttoolbar.pack(expand=True, fill='both')
		self.tkinter_elements.append(self.frame_posttoolbar)
		#
		self.frame_gametaglist = tkinter.Frame(self.frame_posttoolbar)
		self.frame_gametaglist.pack(expand=True, fill='y', side='left', anchor='w')
		self.tkinter_elements.append(self.frame_gametaglist)
		#
		self.frame_logoarea = tkinter.Frame(self.frame_posttoolbar)
		self.frame_logoarea.pack(expand=True, fill='both', anchor='e')
		self.tkinter_elements.append(self.frame_logoarea)
		#
		button_applytag = tkinter.Button(self.frame_gametaglist, text='Apply', command=self.gui_rebuild_game)
		button_applytag.grid(row=0, column=0, sticky='w')
		#
		for i in range(len(self.all_tags)):
			tag = self.all_tags[i]
			intvar = tkinter.IntVar()
			intvar.tag=tag
			checkbox = tkinter.Checkbutton(self.frame_gametaglist, text=tag, variable=intvar)
			checkbox.intvar = intvar
			checkbox.grid(row=i+1, column=0, sticky='w')
			intvar.set(1)
			self.tkinter_elements.append(checkbox)
			self.tag_elements.append(checkbox)
			self.active_tags.add(tag)

		self.gui_rebuild_game()

		###

	def gui_rebuild_game(self, *b):
		self.destroy_all_logos()
		w = self.t.winfo_width()
		h = self.t.winfo_height()
		resizemeter = w / 9
		row = 0
		col = 0
		for element in self.tag_elements:
			if element.intvar.get() == 1:
				self.active_tags.add(element.intvar.tag)
			elif element.intvar.tag in self.active_tags:
				self.active_tags.remove(element.intvar.tag)

		for logo in self.all_logos:
			if not any(tag in self.active_tags for tag in logo.tags):
				continue
			if logo.solved is True and 'Completed' not in self.active_tags:
				continue
			logoframe = tkinter.Frame(self.frame_logoarea)
			logoframe.pack_propagate(0)
			self.logo_elements.append(logoframe)
			imageframe = tkinter.Frame(logoframe, width=resizemeter, height=resizemeter)
			imageframe.pack_propagate(0)
			imageframe.grid(row=0, column=0, sticky='n')
			label_image = tkinter.Label(imageframe)
			label_image.pack(anchor='center', expand=True, fill='both')
			label_name = tkinter.Label(logoframe)
			entry_name = tkinter.Entry(logoframe)
			if logo.solved is True:
				i = self.png_load(logo.images[-1], resizemeter)
				label_image.configure(image=i)
				label_image.i = i
				label_name.configure(text=logo.name)
				label_name.grid(row=1, column=0, sticky='s')
			else:
				i = self.png_load(logo.images[0], resizemeter)
				label_image.configure(image=i)
				label_image.i = i
				entry_name.grid(row=1, column=0, sticky='s')
			self.tkinter_elements.append(logoframe)
			logoframe.id = logo.id
			logoframe.entry_name = entry_name
			logoframe.label_name = label_name
			logoframe.label_image = label_image
			logoframe.grid(row=row, column=col, padx=self.logo_padx, pady=self.logo_pady)
			col += 1
			col = col % self.logos_per_row
			if col == 0:
				row += 1


	def gui_build_logo(self, *b):
		self.destroy_all_elements()
		###

	def playername_set(self, newname):
		if newname != self.stats_main.playername:
			self.cur.execute('UPDATE stats SET value=? WHERE key="playername"', [newname])
			self.sql.commit()
			playerhash = self.playerstats_load(newname)
			self.stats_main.playername = newname

			if self.label_playerhash:
				self.label_playerhash.configure(text=playerhash)
		for logo in self.all_logos:
			logo.solved = self.playerstats_hassolved(logo.id)
		print('Name: ' + self.stats_main.playername)

	def sha8(self, text):
		sha = hashlib.sha256()
		sha.update(text.encode('utf-8'))
		sha = sha.hexdigest()
		return sha[:8]

	def png_load(self, filename, resize=None):
		if filename[-4:] != '.png':
			filename = filename + '.png'
		filename = 'images/' + filename
		i = Image.open(filename)
		if resize:
			ratio = resize / max(i.size)
			newx = int(i.size[0] * ratio)
			newy = int(i.size[1] * ratio)
			i = i.resize([newx, newy], resample=Image.ANTIALIAS)
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
		self.cur_player.execute('SELECT * FROM stats WHERE key=?', [key])
		f = self.cur_player.fetchone()
		if f:
			return f[1]
		return None

	def playerstats_hassolved(self, logoid):
		key = 'hassolved_%d' % logoid
		val = self.playerstats_get(key)
		if val is None:
			return False
		return True

	def strip_to_filename(self, s):
		for badchar in self.WINDOWS_BADCHARS:
			s = s.replace(badchar, '')
		return s

	def get_all_tags(self):
		self.cur.execute('SELECT * FROM logos')
		fetch = self.cur.fetchall()
		alltags = []
		for item in fetch:
			itemtags = item[self.dbindex_tag]
			itemtags = itemtags.replace(', ', ',')
			itemtags = itemtags.split(',')
			alltags += itemtags
		alltags = list(set(alltags))
		alltags.sort()
		return alltags

logogame = LogoGame()