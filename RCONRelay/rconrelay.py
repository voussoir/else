import socket
import time
import traceback

class LogEvent:
	def __init__(self):
		self.type = None
		self.killerinfo = None
		self.victiminfo = None
		self.weaponinfo = None

class Player:
	def __init__(self, name=""):
		self.name = name
		self.kills = 0
		self.deaths = 0
		self.objectives = 0
		self.events = []
		self.status = None

	def __str__(self):
		return "%s :|: %d kills, %d deaths, %d objectives :|: Status=%s" % (self.name, self.kills, self.deaths, self.objectives, self.status)

class RCONRelay:
	def __init__(self):
		self.whitelist = ["joined team", "disconnected", "say", "killed", "suicide", "changed name", "flagevent", "flag."]
		self.blacklist = ["say_team"]
		self.weaponmap = {
		"tf_projectile_rocket": "Rocket Launcher",
		"tf_projectile_pipe_remote": "Sticky Bomb",
		"tf_projectile_pipe": "Grenade Launcher",
		"obj_sentrygun": "Sentry lvl 1",
		"obj_sentrygun2": "Sentry lvl 2",
		"obj_sentrygun3": "Sentry lvl 3",
		"shotgun_pyro": "Shotgun",
		"shotgun_soldier": "Shotgun",
		"shotgun_primary": "Shotgun",
		"club": "Kukri",
		"pistol_scout": "Pistol",
		"world": "World Hazard"
		}

		self.ip = "0.0.0.0"
		self.port = 32768
		self.players = []

	def start(self):
		self.rcon = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#self.rcon.settimeout(60)
		self.rcon.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.rcon.bind((self.ip, self.port))
		print("Listening...")
		while True:
			chatdata = self.rcon.recvfrom(1024)
			#print(chatdata)
			chatdata = chatdata[0]
			chatdata = chatdata.decode('utf-8', 'ignore')
			chatdata = chatdata[3:-2]
			self.parsechat(chatdata)

	def parsechat(self, chat):
		timestamp = chat.split(': ')[0]
		quotesplit = chat.split('"')
		if "killed" in chat:
			killerinfo = quotesplit[1]
			victiminfo = quotesplit[3]
			weaponinfo = quotesplit[5]
			weaponinfo = self.weaponmap.get(weaponinfo, weaponinfo)
			misc = '"'.join(quotesplit[6:])
			headshot = True if "(customkill \"headshot\")" in misc else False
			chat = "%s] %s killed %s with %s" % (timestamp, killerinfo, victiminfo, weaponinfo)
			if headshot:
				chat += " (Headshot)"

		elif "flagevent" in chat:
			killerinfo = quotesplit[1]
			flagevent = quotesplit[5]
			if flagevent == 'captured':
				capscurrent = quotesplit[7]
				capstotal = quotesplit[9]
				chat = "%s] %s %s flag. %s / %s" % (timestamp, killerinfo, flagevent, capscurrent, capstotal)
			else:
				chat = "%s] %s %s flag." % (timestamp, killerinfo, flagevent)				

		elif "committed suicide with \"world\" (attacker_position" in chat:
			victiminfo = quotesplit[1]
			chat = "%s] %s committed suicide" % (timestamp, victiminfo)

		if any(white.lower() in chat.lower() for white in self.whitelist):
			if not any(black.lower() in chat.lower() for black in self.blacklist):
				print(chat)

if __name__ == '__main__':
	rcon = RCONRelay()
	rcon.start()