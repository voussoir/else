WORDS = ['STEAD','CONSUBSTANTIATION','WRONGHEADED','UNINTELLIGIBILITY']

def get_weight(character, distance):
	return (ord(character.lower()) - 96) * distance

def try_balancing(word, pivot):
	left = word[:pivot]
	wleft = sum(get_weight(left[x], len(left)-x) for x in range(len(left)))
	right = word[pivot+1:]
	wright = sum(get_weight(right[x], x+1) for x in range(len(right)))

	if wright == wleft:
		print '%s %s %s - %d' % (left, word[pivot], right, wleft)

for word in WORDS:
	for x in range(len(word)):
		try_balancing(word, x)