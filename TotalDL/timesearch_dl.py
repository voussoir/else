import sqlite3
import totaldl

sql = sqlite3.connect('!!testdata.db')
cur = sql.cursor()

cur.execute('SELECT * FROM posts WHERE self=0 AND url IS NOT NULL')
while True:
	item = cur.fetchone()
	if item is None:
		break
	url = item[7]
	totaldl.handle_master(url)