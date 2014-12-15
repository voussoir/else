import tkinter
import threading
import time

class CanvasGame:
	def managementthread(self):
		while True:
			w = self.pressed_dict.get('w', False)
			s = self.pressed_dict.get('s', False)
			a = self.pressed_dict.get('a', False)
			d = self.pressed_dict.get('d', False)
			if w:
				self.velocity_y -= self.velocity_speedup
			if s:
				self.velocity_y += self.velocity_speedup

			if a:
				self.velocity_x -= self.velocity_speedup
			if d:
				self.velocity_x += self.velocity_speedup

			if not any(movement for movement in [w,a,s,d]):
				nondirectional = abs(self.velocity_x) + abs(self.velocity_y)
				nondirectional /= 2
				if nondirectional < self.velocity_minimum:
					self.velocity_x = 0
					self.velocity_y = 0
				else:
					if self.velocity_x != 0:
						self.velocity_x *= self.velocity_slowdown
					if self.velocity_y != 0:
						self.velocity_y *= self.velocity_slowdown



			self.velocity_x = self.numbercap(self.velocity_x, self.velocity_maximum)
			self.velocity_y = self.numbercap(self.velocity_y, self.velocity_maximum)

			self.player_x += self.velocity_x
			self.player_y += self.velocity_y

			x = self.x_camera + self.player_x
			y = self.y_camera + self.player_y
			xdiff = x - self.gamewidthcenter
			ydiff = y - self.gameheightcenter
			if xdiff > self.camera_distance:
				self.x_camera -= abs(xdiff / self.camera_distance)
			elif xdiff < -self.camera_distance:
				self.x_camera += abs(xdiff / self.camera_distance)

			if ydiff > self.camera_distance:
				self.y_camera -= abs(ydiff / self.camera_distance)
			elif ydiff < -self.camera_distance:
				self.y_camera += abs(ydiff / self.camera_distance)

			#print(self.player_x, x)

			self.canvas.coords(self.player, x-self.player_radius, y-self.player_radius,
							   x+self.player_radius, y+self.player_radius)

			time.sleep(0.017)

	def numbercap(self, i, cap):
		if i > cap:
			i = cap
		elif i < -cap:
			i = -cap
		return i

	def pushkey(self, event):
		#print(event.char, "Down")
		self.pressed_dict[event.char] = True
	def releasekey(self, event):
		#print(event.char, "Up")
		self.pressed_dict[event.char] = False

	def __init__(self):
		self.t = tkinter.Tk()
		self.pressed_dict = {}

		self.gamewidth = 640
		self.gameheight = 480
		self.gamewidthcenter = self.gamewidth / 2
		self.gameheightcenter = self.gameheight / 2
		self.canvas = tkinter.Canvas(self.t, width=self.gamewidth, height=self.gameheight)
		self.x_camera = (self.gamewidth / 2)
		self.y_camera = (self.gameheight / 2)

		x = 0
		y = 0
		self.player_x = x
		self.player_y = y
		self.player_radius = 3
		self.player = self.canvas.create_oval(x-self.player_radius, y-self.player_radius, 
											  x+self.player_radius, y+self.player_radius, 
											  fill="#ff0")
		self.camera = self.canvas.create_oval(self.x_camera, self.y_camera, self.x_camera, self.y_camera)
		self.camera_distance = 20
		self.playerthread = threading.Thread(name="Playerthread", target=self.managementthread)
		self.playerthread.daemon = True
		self.velocity_x = 0
		self.velocity_y = 0
		self.velocity_maximum = 4
		self.velocity_minimum = 0.2
		self.velocity_slowdown = 0.95
		self.velocity_speedup = 0.6

		self.entities = []

		self.canvas.bind("<KeyPress>", self.pushkey)
		self.canvas.bind("<KeyRelease>", self.releasekey)
		self.canvas.focus_set()

		self.playerthread.start()

		self.canvas.pack()

		self.t.mainloop()

c = CanvasGame()
