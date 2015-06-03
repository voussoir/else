import traceback
import sqlite3
import totaldl
import praw

r = praw.Reddit('')
r.login('', '')

sql = sqlite3.connect('!!testdata.db')
cur = sql.cursor()
cur2 = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS totaldl_urls(url TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS urlindex ON totaldl_urls(url)')
sql.commit()
cur.execute('SELECT * FROM posts WHERE self=0 AND url IS NOT NULL')
while True:
	item = cur.fetchone()
	if item is None:
		break
	
	url = item[7]
	cur2.execute('SELECT * FROM totaldl_urls WHERE url=?', [url])
	if cur2.fetchone():
		continue
	title = item[6]
	for character in '\\/?:*"><|.':
		title = title.replace(character, '')
	if len(title) > 35:
		title = title[:34] + '-'
	try:
		filepath = totaldl.handle_master(url, customname=title)
		if filepath is None:
			continue
		filepath = filepath.replace('\\', '/')
		filepath = filepath.split('/')[-1]
		if '.mp4' in filepath:
			filepath = 'http://syriancivilwar.pw/Videos/' + filepath
			submission = r.get_info(thing_id=item[1])
			submission.add_comment('[Mirror](%s)' % filepath)
		print(filepath)
	except:
		traceback.print_exc()
	cur2.execute('INSERT INTO totaldl_urls VALUES(?)', [url])
	sql.commit()