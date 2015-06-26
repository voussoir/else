import bot
import os
import praw
import sys
import time

r=bot.rG()

SUBREDDIT = r.get_subreddit(sys.argv[1])
FILENAME = sys.argv[2]
prevtime = 0
while True:
	newtime = os.path.getmtime(FILENAME)
	if newtime != prevtime:
		f=open(FILENAME)
		style = f.read()
		f.close()
		print('Pushing stylesheet. %d bytes' % len(style))
		SUBREDDIT.set_stylesheet(style)
	prevtime = newtime
	time.sleep(5)
