import socket
import time
import traceback


class RCONRelay:
	def __init__(self):
		self.whitelist = ["joined team", "say", "killed", "suicide", "changed name"]
		self.blacklist = ["say_team"]
		self.weaponmap = {
		"tf_projectile_rocket": "Rocket Launcher",
		"tf_projectile_pipe_remote": "Sticky Bomb",
		"obj_sentrygun": "Sentry lvl 1",
		"obj_sentrygun2": "Sentry lvl 2",
		"obj_sentrygun3": "Sentry lvl 3",
		"shotgun_pyro": "Shotgun",
		"shotgun_soldier": "Shotgun",
		"shotgun_primary": "Shotgun"
		}

		self.ip = ""
		self.port = 32768

	def start(self):
		self.rcon = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#self.rcon.settimeout(60)
		self.rcon.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.rcon.bind((self.ip, self.port))
		print("Listening...")
		while True:
			chatdata = self.rcon.recvfrom(1024)
			#print(chatdata)
			self.processchat(chatdata)

	def processchat(self, chatdata):
		chat = chatdata[0]
		chat = chat.decode("utf-8", "ignore")
		chat = chat[3:-2]
		timestamp = chat[:21]
		if "killed" in chat:
			quotesplit = chat.split('"')
			killerinfo = quotesplit[1]
			victiminfo = quotesplit[3]
			weaponinfo = quotesplit[5]
			weaponinfo = self.weaponmap.get(weaponinfo, weaponinfo)
			misc = '"'.join(quotesplit[6:])
			headshot = True if "(customkill \"headshot\")" in misc else False
			chat = "%s] %s killed %s with %s" % (timestamp, killerinfo, victiminfo, weaponinfo)
			if headshot:
				chat += " (Headshot)"

		elif "committed suicide with \"world\" (attacker_position" in chat:
			quotesplit = chat.split('"')
			victiminfo = quotesplit[1]
			chat = "%s] %s committed suicide" % (timestamp, victiminfo)

		if any(white.lower() in chat.lower() for white in self.whitelist):
			if not any(ban.lower() in chat.lower() for ban in self.blacklist):
				print(chat)

	def weaponmapping(self, chat):
		for key in self.weaponmap:
			val = self.weaponmap[key]
			chat = chat.replace(key, val)
		return chat


rcon = RCONRelay()
rcon.start()