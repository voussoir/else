import sqlite3
import totaldl

sql = sqlite3.connect('!!testdata.db')
cur = sql.cursor()
cur2 = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS totaldl_urls(url TEXT)')
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
	totaldl.handle_master(url, customname=title)
	cur2.execute('INSERT INTO totaldl_urls VALUES(?)', [url])
	sql.commit()