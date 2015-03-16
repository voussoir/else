import tkinter
import sqlite3
import hashlib
import random

class Editor:
	def __init__(self):
		#self.WINDOWS_BADCHARS = '\\/?:*"><|'
		self.windowtitle = 'Editor'

		self.sql = sqlite3.connect('textfiles.db')
		self.cur = self.sql.cursor()
		self.cur.execute('CREATE TABLE IF NOT EXISTS textfiles(id TEXT, filename TEXT, filetext TEXT)')
		self.cur.execute('CREATE INDEX IF NOT EXISTS textfilesindex ON textfiles(id)')
		self.sql.commit()

		self.font_large = ("Consolas", 16)
		self.font_med = ("Consolas", 12)
		self.font_small = ("Consolas", 10)
		self.font_username = "Consolas"
		self.font_usersize = 12

		self.kilobyte = 1024
		self.megabyte = 1048576
		self.maximum_characters = 1*self.megabyte
		self.maximum_title = 64

		self.t = tkinter.Tk()
		self.t.title(self.windowtitle)
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

		self.reserved_filenames = ['random', 'list', 'help']
		self.has_filenames_changed = True
		self.entities = []
		self.filename = None

	def start(self):
		self.gui_build_fileloader()
		self.t.mainloop()

	def annihilate(self):
		while len(self.entities) > 0:
			self.entities[0].destroy()
			del self.entities[0]

	def gui_build_fileloader(self, *b):
		self.annihilate()
		self.t.title(self.windowtitle)
		###
		self.frame_fileloader = tkinter.Frame(self.t)
		self.entities.append(self.frame_fileloader)
		#
		self.entry_filename = tkinter.Entry(self.frame_fileloader, font=self.font_large, justify='right')
		self.entry_filename.grid(row=0, column=0, columnspan=3)
		self.entry_filename.focus_set()
		self.entry_filename.bind("<Return>", self.loadfile_smart)
		self.entities.append(self.entry_filename)
		#
		self.label_filename = tkinter.Label(self.frame_fileloader, font=self.font_large, text='.txt')
		self.label_filename.grid(row=0, column=3)
		self.entities.append(self.label_filename)
		#
		self.button_fileloader = tkinter.Button(self.frame_fileloader, font=self.font_large, text='Load', command=self.loadfile_smart)
		self.button_fileloader.grid(row=1, column=1, pady=10)
		self.entities.append(self.button_fileloader)
		#
		self.frame_fileloader.pack(expand=True, anchor='center')
		#self.frame_fileloader.place(x=width/2, y=(height/2)-10, anchor='center')

	def gui_build_editor(self, filetext, *b):
		self.annihilate()
		###
		self.frame_toolbar = tkinter.Frame(self.t)
		self.frame_toolbar.pack()
		self.entities.append(self.frame_toolbar)
		#
		self.button_back = tkinter.Button(self.frame_toolbar, text='back', command=self.gui_build_fileloader, font=self.font_small)
		self.button_back.grid(row=0, column=0)
		self.entities.append(self.button_back)
		#
		self.label_filename = tkinter.Label(self.frame_toolbar, text=self.filename, font=self.font_small)
		self.label_filename.grid(row=0, column=1, padx=70)
		self.entities.append(self.label_filename)
		#
		self.button_save = tkinter.Button(self.frame_toolbar, text='save', command=self.savefile_smart, font=self.font_small)
		self.button_save.grid(row=0, column=2)
		self.entities.append(self.button_save)
		#
		self.label_filesize = tkinter.Label(self.frame_toolbar, text='', font=self.font_small)
		self.label_filesize.grid(row=1, column=0, columnspan=3)
		self.entities.append(self.label_filesize)
		#
		self.scrollbar_editor = tkinter.Scrollbar(self.t)
		self.scrollbar_horz = tkinter.Scrollbar(self.t, orient='horizontal')
		self.scrollbar_editor.pack(side='right', fill='y')
		self.scrollbar_horz.pack(side='bottom', fill='x')
		self.text_editor = tkinter.Text(self.t, wrap='word', font=self.font_med)
		self.text_editor.configure(yscrollcommand=self.scrollbar_editor.set)
		self.text_editor.configure(xscrollcommand=self.scrollbar_horz.set)
		self.scrollbar_editor.configure(command=self.text_editor.yview)
		self.scrollbar_horz.configure(command=self.text_editor.xview)
		self.text_editor.insert('end', filetext)
		self.text_editor.pack(expand=True, fill='both')
		self.text_editor.focus_set()
		self.text_editor.bind('<Control-s>', self.savefile_smart)
		self.text_editor.bind('<Control-w>', self.gui_build_fileloader)
		self.text_editor.bind('<Control-[>', lambda s: self.editor_resize_font(-1))
		self.text_editor.bind('<Control-]>', lambda s: self.editor_resize_font(1))
		self.text_editor.bind('<Control-/>', self.editor_toggle_wrap)
		self.entities.append(self.text_editor)
		self.entities.append(self.scrollbar_editor)
		self.entities.append(self.scrollbar_horz)
		###

	def editor_resize_font(self, direction, *b):
		self.font_usersize += direction
		if self.font_usersize < 1:
			self.font_usersize = 1
		font = [self.font_username, self.font_usersize]
		self.text_editor.configure(font=font)
		self.label_filesize.configure(text=str(self.font_usersize))

	def editor_toggle_wrap(self, *b):
		mode = self.text_editor.cget('wrap')
		if mode == 'word':
			self.text_editor.configure(wrap='none')
			self.label_filesize.configure(text='word wrap disabled')
		if mode == 'none':
			self.text_editor.configure(wrap='word')
			self.label_filesize.configure(text='word wrap enabled')

	def savefile_smart(self, *b):
		try:
			filetext = self.text_editor.get('0.0', 'end')
			filesize = len(filetext) - 1
			try:
				self.savefile(self.filename, filetext)
				self.label_filesize.configure(text=self.filesizestring(filesize))
			except EditorException as ee:
				self.label_filesize.configure(text=ee.args[0])
		except NameError:
			# text editor does not exist for some reason
			return

	def savefile(self, filename, filetext, permissions=False):
		if filename is None:
			raise EditorException('Please enter a filename')
		if permissions is False and filename in self.reserved_filenames:
			print('This file is restricted. You are not permitted to modify it.')
			raise EditorException("Restricted file")
		filename = filename.replace(' ', '_')
		filetext = filetext[:-1]
		# Text widget seems to add \n to the end at all times
		# So remove it.
		filesize = len(filetext)
		namesize = len(filename)
		if filesize > self.maximum_characters:
			diff = filesize-self.maximum_characters
			sizeerror = 'too big: %d / %d (-%d)' % (filesize, self.maximum_characters, diff)
			print('File exceeds maximum character limit. %s' % sizeerror)
			raise EditorException(sizeerror)
		elif namesize > self.maximum_title:
			diff = namesize - self.maximum_title
			sizeerror = '%d / %d (-%d)' % (namesize, self.maximum_title, diff)
			print('Filename exceeds maximum character limit: %s' % sizeerror)
			raise EditorException('Filename too big: %s' % sizeerror)
		
		sha = self.sha(filename)
		self.cur.execute('SELECT * FROM textfiles WHERE id=?', [sha])
		fetch = self.cur.fetchone()
		if filesize == 0:
			print('Deleting %s' % filename)
			self.cur.execute('DELETE FROM textfiles WHERE id=?', [sha])
			if fetch:
				# If fetch: It previously existed and is now deleted
				# If not fetch: User just created this workspace, and
				# is now closing it without adding anything
				# so nothing has changed on disk.
				self.has_filenames_changed = True
		else:
			if fetch:
				self.cur.execute('UPDATE textfiles SET filename=?, filetext=? WHERE id=?', [filename, filetext, sha])
			else:
				self.cur.execute('INSERT INTO textfiles VALUES(?, ?, ?)', [sha, filename, filetext])
			print('Wrote %s: %s' % (filename, self.filesizestring(filesize)))
			self.has_filenames_changed = True
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
			self.t.title(filename)
		return

	def loadfile(self, filename):
		if filename == 'random':
			filename = self.loadrandom()
		if filename == 'list':
			self.generate_listfile()
		filename = filename.replace(' ', '_')
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

	def generate_listfile(self):
		if self.has_filenames_changed:
			print('Refreshing list file')
			self.cur.execute('SELECT * FROM textfiles')
			fetch = self.cur.fetchall()
			fetch = [x[1] for x in fetch]
			fetch.sort(key=lambda x:x.lower())
			fetch = '\n'.join(fetch)
			self.savefile('list', fetch, permissions=True)
			self.has_filenames_changed = False

	def sha(self, data):
		sha = hashlib.sha256()
		data = data.encode('utf-8')
		sha.update(data)
		sha = sha.hexdigest()
		return sha

class EditorException(Exception):
	pass

editor = Editor()
editor.start()