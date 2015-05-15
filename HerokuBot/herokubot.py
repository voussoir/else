import praw
import time
import sqlite3

print('Logging in.')
r = praw.Reddit('Testing praw api usage over Heroku')
r.login('qQGusVuAHezHxhYTiYGm', 'qQGusVuAHezHxhYTiYGm')

print('Loading database')
sql = sqlite3.connect('sql.db')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS subreddits(name TEXT, subscribers INT)')
sql.commit()

print('Getting subreddit info.')
sub = r.get_subreddit('Goldtesting')
print('/r/Goldtesting')
print('\tCreated at: %d' % sub.created_utc)
print('\tSubscribers: %d' % sub.subscribers)

print('Saving subreddit info.')
cur.execute('INSERT INTO subreddits VALUES(?, ?)', ['Goldtesting', sub.subscribers])
sql.commit()

print('All done!')
while True:
	time.sleep(60)