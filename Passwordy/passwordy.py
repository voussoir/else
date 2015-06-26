import string
import random
import sys

DEFAULT_LENGTH = 32
DEFAULT_SENTENCE = 5
HELP_MESSAGE = '''
 ---------------------------------------------------------------
|Generates a randomized password.                               |
|                                                               |
|> passwordy [length] ["p"] ["d"]                               |
|                                                               |
|   length : How many characters. Default %03d.                  |
|   p      : If present, the password will contain punctuation  |
|            characters. Otherwise not.                         |
|   d      : If present, the password will contain digits.      |
|            Otherwise not.                                     |
|                                                               |
|   The password can always contain upper and lowercase         |
|   letters.                                                    |
 ---------------------------------------------------------------
'''[1:-1] % (DEFAULT_LENGTH)

HELP_SENTENCE = '''
 ---------------------------------------------------------------
|Generates a randomized sentence                                |
|                                                               |
|> passwordy sent [length] [join]                               |
|                                                               |
|   length : How many words to retrieve. Default %03d.           |
|   join   : The character that will join the words together.   |
|            Default space.                                     |
 ---------------------------------------------------------------
 '''[1:-1] % (DEFAULT_SENTENCE)

def make_password(length=None, allowpunctuation=False, allowdigits=False):
	'''
	Returns a string of length `length` consisting of a random selection
	of uppercase and lowercase letters, as well as punctuation and digits
	if parameters permit
	'''
	if length is None:
		length = DEFAULT_LENGTH
		
	s = string.ascii_letters
	if allowpunctuation is True:
		s += string.punctuation
	if allowdigits is True:
		s += string.digits

	password = ''.join([random.choice(s) for x in range(length)])
	return password

def make_sentence(length=None, joiner=' '):
	'''
	Returns a string containing `length` words, which come from
	dictionary.common.
	'''
	import dictionary.common as common
	if length is None:
		length = DEFAULT_LENGTH
	words = [random.choice(common.words) for x in range(length)]
	words = [w.replace(' ', joiner) for w in words]
	result = joiner.join(words)
	return result

if __name__ == '__main__':
	args = sys.argv
	argc = len(args)

	if argc == 1:
		mode = 'password'
		length = DEFAULT_LENGTH

	elif args[1].isdigit():
		mode = 'password'
		length = int(args[1])

	elif 'help' in args[1].lower():
		mode = None
		print(HELP_MESSAGE)
		print(HELP_SENTENCE)

	elif 'sent' in args[1].lower() and argc == 2:
		mode = 'sentence'
		length = DEFAULT_SENTENCE

	elif args[2].isdigit():
		mode = 'sentence'
		length = int(args[2])

	if mode == 'password':
		punc = 'p' in args
		digi = 'd' in args
		
		print(make_password(length, punc, digi))
		
	elif mode == 'sentence':
		if argc == 4:
			joiner = args[3]
		else:
			joiner = ' '
		print(make_sentence(length, joiner))

	else:
		pass