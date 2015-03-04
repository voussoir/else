import tkinter
import sqlite3
import hashlib
import random

class Editor:
	def __init__(self):
		self.WINDOWS_BADCHARS = '\\/?:*"><|'

		self.sql = sqlite3.connect('textfiles.db')
		self.cur = self.sql.cursor()
		self.cur.execute('CREATE TABLE IF NOT EXISTS textfiles(id TEXT, filename TEXT, filetext TEXT)')
		self.cur.execute('CREATE INDEX IF NOT EXISTS textfilesindex ON textfiles(id)')
		self.sql.commit()

		self.font_large = ("Consolas", 16)
		self.font_med = ("Consolas", 12)
		self.font_small = ("Consolas", 10)

		self.kilobyte = 1024
		self.megabyte = 1048576
		self.maximum_characters = 1*self.megabyte
		self.maximum_title = 64

		self.t = tkinter.Tk()
		self.w = 450
		self.h = 350
		self.screenwidth = self.t.winfo_screenwidth()
		self.screenheight = self.t.winfo_screenheight()
		self.windowwidth = self.w
		self.windowheight = self.h
		self.windowx = (self.screenwidth-self.windowwidth) / 2
		self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
		self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
		self.t.geometry(self.geometrystring)


		self.entities = []
		self.filename = None
		self.gui_build_fileloader()

		self.t.mainloop()

	def annihilate(self):
		for x in self.entities:
			try:
				x.grid_forget()
				x.pack_forget()
			except:
				pass
			x.destroy()

	def gui_build_fileloader(self, *b):
		self.annihilate()

		self.frame_fileloader = tkinter.Frame(self.t)
		self.entities.append(self.frame_fileloader)
		self.entry_filename = tkinter.Entry(self.frame_fileloader, font=self.font_large, justify='right')
		self.entry_filename.grid(row=0, column=0, columnspan=3)
		self.entry_filename.focus_set()
		self.entry_filename.bind("<Return>", self.loadfile_smart)
		self.entities.append(self.entry_filename)
		self.label_filename = tkinter.Label(self.frame_fileloader, font=self.font_large, text='.txt')
		self.label_filename.grid(row=0, column=3)
		self.entities.append(self.label_filename)
		self.button_fileloader = tkinter.Button(self.frame_fileloader, font=self.font_large, text='Load', command=self.loadfile_smart)
		self.button_fileloader.grid(row=1, column=1, pady=10)
		self.entities.append(self.button_fileloader)
		width = self.t.winfo_width()
		height = self.t.winfo_height()
		if min([width, height]) < 20:
			width = self.w
			height = self.h
		#self.frame_fileloader.pack(expand=True, fill='both', anchor='center')
		self.frame_fileloader.place(x=width/2, y=(height/2)-10, anchor='center')

	def gui_build_editor(self, filetext, *b):
		self.annihilate()

		self.frame_toolbar = tkinter.Frame(self.t)
		self.frame_toolbar.pack()
		self.entities.append(self.frame_toolbar)
		self.button_back = tkinter.Button(self.frame_toolbar, text='back', command=self.gui_build_fileloader, font=self.font_small)
		self.button_back.grid(row=0, column=0)
		self.entities.append(self.button_back)
		self.label_filename = tkinter.Label(self.frame_toolbar, text=self.filename, font=self.font_small)
		self.label_filename.grid(row=0, column=1, padx=20)
		self.entities.append(self.label_filename)
		self.button_save = tkinter.Button(self.frame_toolbar, text='save', command=self.savefile_smart, font=self.font_small)
		self.button_save.grid(row=0, column=2)
		self.entities.append(self.button_save)
		self.label_filesize = tkinter.Label(self.frame_toolbar, text='', font=self.font_small)
		self.label_filesize.grid(row=1, column=0, columnspan=10)
		self.entities.append(self.label_filesize)
		self.text_editor = tkinter.Text(self.t, wrap='word', font=self.font_med)
		self.text_editor.insert('end', filetext)
		self.text_editor.pack(expand=True, fill='both')
		self.text_editor.focus_set()
		self.text_editor.bind('<Control-s>', self.savefile_smart)
		self.text_editor.bind('<Control-w>', self.gui_build_fileloader)
		self.entities.append(self.text_editor)

	def savefile_smart(self, *b):
		try:
			filetext = self.text_editor.get('0.0', 'end')
			self.savefile(self.filename, filetext)
			filesize = len(filetext) - 1
			self.label_filesize.configure(text=self.filesizestring(filesize))
		except NameError:
			# text editor does not exist for some reason
			return

	def savefile(self, filename, filetext):
		filetext = filetext[:-1]
		# Text widget seems to add \n to the end at all times
		# So remove it.
		if self.filename is None:
			return False
		filesize = len(filetext)
		namesize = len(filename)
		if filesize > self.maximum_characters:
			diff = filesize-self.maximum_characters
			print('File exceeds maximum character limit. %d / %d (-%d)' % (filesize, self.maximum_characters, diff))
			return False
		elif namesize > self.maximum_title:
			diff = namesize - self.maximum_title
			print('Filename exceeds maximum character limit: %d / %d (-%d)' % (namesize, self.maximum_title, diff))
			return False
		
		sha = self.sha(filename)
		self.cur.execute('SELECT * FROM textfiles WHERE id=?', [sha])
		fetch = self.cur.fetchone()
		if filesize == 0:
			print('Deleting %s' % filename)
			self.cur.execute('DELETE FROM textfiles WHERE id=?', [sha])
		else:
			if fetch:
				self.cur.execute('UPDATE textfiles SET filename=?, filetext=? WHERE id=?', [filename, filetext, sha])
			else:
				self.cur.execute('INSERT INTO textfiles VALUES(?, ?, ?)', [sha, filename, filetext])
			print('Wrote %s: %s' % (filename, self.filesizestring(filesize)))
		self.sql.commit()
		return True

	def filesizestring(self, filesize):
		percentage = "%0.4f" % (100 * filesize / self.maximum_characters)
		diff = self.maximum_characters - filesize
		out = '%d c,  %s%%,  +%d' % (filesize, percentage, diff)
		return out

	def loadfile_smart(self, *b):
		try:
			filename = self.entry_filename.get()
		except NameError:
			# entry_filename does not exist somehow
			return
		filetext = self.loadfile(filename)
		if filetext is not None:
			self.gui_build_editor(filetext)
		return

	def loadfile(self, filename):
		if filename == 'random':
			filename = self.loadrandom()
		if len(filename) < 1:
			return None
		if len(filename) > self.maximum_title:
			print('Title too long. %d / %d' % (len(filename), self.maximum_title))
			return None
		self.filename = filename
		sha = self.sha(filename)
		self.cur.execute('SELECT * FROM textfiles WHERE id=?', [sha])
		fetch = self.cur.fetchone()
		if fetch:
			loadedtext = fetch[2]
			return loadedtext
		else:
			print('New file: %s' % filename)
			return ""

	def loadrandom(self):
		self.cur.execute('SELECT * FROM textfiles')
		fetch = self.cur.fetchall()
		if len(fetch) < 1:
			return ""
		return random.choice(fetch)[1]

	def strip_to_filename(self, s):
		for bad in self.WINDOWS_BADCHARS:
			s = s.replace(bad, '')
		return s

	def sha(self, data):
		sha = hashlib.sha256()
		data = data.encode('utf-8')
		sha.update(data)
		sha = sha.hexdigest()
		return sha

editor = Editor()