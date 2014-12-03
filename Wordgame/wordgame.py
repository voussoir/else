import random
import time
import string
import os
import sys


filea = open('dictionarywords\\SINGLE.txt')
read = filea.read()
single = read.splitlines()
filea.close()
del read

score = 0
failes = []
wordqueue = []
marker = '_'

def randword():
	#Takes one from the wordqueue or picks a random word from single.txt
	global wordqueue
	if len(wordqueue) == 0:
		return single[random.randint(0,len(single)-1)]
	else:
		w = wordqueue[0]
		wordqueue = wordqueue[1:]
		return w

def clear():
	os.system('cls')

def allindex(word, letter):
	#Finds all instances of letter in word. Returns a list of indexes
	pos = 0
	result = []
	while len(word) > 0:
		if word[0].lower() == letter.lower():
			result.append(pos)
		word = word[1:]
		pos += 1
	return result

def newgame():
	global failes
	global score

	failes = []


	word = randword()
	hidden = word
	for char in string.ascii_letters:
		hidden = hidden.replace(char, marker)
	gameround(word, hidden)

def gameround(word, hidden):
	global failes
	global score
	global wordqueue
	clear()
	animtext(hidden, 0.05)
	clear()
	while marker in hidden:
		print(hidden, '\nNo:', ', '.join(failes), '\nPts:', score)
		try:
			guess = input('> ')
		except EOFError:
			print('Your environment does not support input. Try running this game through the CMD')
			while True:
				pass

		clear()
		if guess == '!close':
			quit()
		elif guess == '!show':
			#Give answer
			print(word)
		elif guess[:7] == '!choose':
			#Add a word to the queue
			wordqueue.append(guess[8:])
		elif guess[:8] == '!xchoose':
			#Forfeit current game and start chosen word
			wordqueue.append(guess[9:])
			score -= (len(word) + 2)
			break
		elif guess == '!forfeit':
			#Forfeit current game
			score -= (len(word) + 2)
			break

		else:
			for g in guess:
				found = False
				hidden = list(hidden)
				i = allindex(word, g)
				for index in i:
					hidden[index] = g
					found = True
				if found == False and g not in failes:
					failes.append(g)
					score -= 1
				hidden = ''.join(hidden)

	clear()
	score += len(word) + 2
	animtext(word, 0.06)
	print('You did it!\nPts:', score)

def animtext(word, period):
	for m in word:
		print(m, end='')
		sys.stdout.flush()
		time.sleep(period)
	print()


clear()
while True:
	print()
	newgame()
	print('Press Enter to play again')
	input()
	clear()