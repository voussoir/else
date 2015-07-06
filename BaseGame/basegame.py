import random
import shutil

DEFAULT_FROMBASE = 10
DEFAULT_TOBASE = 16
DEFAULT_LOWER = 0
DEFAULT_UPPER = 1000


TERMINALWIDTH = shutil.get_terminal_size().columns

def basex(number, base, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Converts an integer to a different base string."""
    alphabet = alphabet[:base]
    if not isinstance(number, (int, str)):
        raise TypeError('number must be an integer')
    number = int(number)
    based = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        based = alphabet[i] + based
    return sign + based

def changebase(number, frombase, tobase):
    number = str(number)
    result = int(number, frombase)
    return basex(result, tobase)

def intinput(prompt, greaterthan=None):
    ''' Prompt for input until the user enters an int '''
    while True:
        result = input(prompt)
        try:
            i = int(result)
            if greaterthan is None or i > greaterthan:
                return i
        except ValueError:
            pass

def configuration():
    frombase = intinput('  From base: ', 1)
    tobase = intinput('    To base: ', 1)
    lower = intinput('Lower bound: ')
    upper = intinput('Upper bound: ', lower)
    return {
    'frombase': frombase,
    'tobase': tobase,
    'lower': lower,
    'upper': upper,
    }

def calcpoints(solution, lower, upper, maxpoints):
    '''
    1/2 of the maxpoints are granted automatically.
    The other 1/2 points depends on how large the number
    you had to guess was.
    '''
    basescore = int(maxpoints / 2) + 1
    bonus = (solution - lower) / (upper - lower)
    bonus *= basescore
    bonus = int(bonus)
    return basescore + bonus

def playgame():
    c= {
    'frombase': DEFAULT_FROMBASE,
    'tobase': DEFAULT_TOBASE,
    'lower': DEFAULT_LOWER,
    'upper': DEFAULT_UPPER,
    }
    print('\n"!" to reconfigure, "?" to give up')
    score = 0
    while True:
        number = random.randint(c['lower'], c['upper'])
        prompt = changebase(number, 10, c['frombase'])
        solution = changebase(number, 10, c['tobase']).lower()
        prompt = 'b%d -> b%d : %s = ' % (c['frombase'], c['tobase'], prompt)

        cursor = len(prompt) + 1
        scoretext = '(score: %d)' % score
        spacer = ' ' * (TERMINALWIDTH - (len(scoretext) + cursor))
        prompt = prompt + spacer + scoretext 
        prompt += '\b' * (TERMINALWIDTH - cursor)

        correctness = False
        while not correctness:
            guess = input(prompt).lower()
            guess = guess.lstrip('0')
            if guess == '!':
                c = configuration()
                correctness = True
                print()
            if guess == '?':
                if c['frombase'] != 10 and c['tobase'] != 10:
                    b10 = ' (b10= %d)' % number
                else:
                    b10 = ''
                print('%s= %s%s'% (' '*(cursor-3), solution, b10))
                correctness = True
            if guess == solution:
                maxpoints = int((c['upper'] - c['lower']) ** 0.5)
                score += calcpoints(number, c['lower'],c['upper'],maxpoints)
                correctness = True           

if __name__ == '__main__':
    playgame()