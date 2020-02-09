import argparse
import os
import sqlite3
import sys
import threading
import time
import traceback

from voussoirkit import bytestring
from voussoirkit import downloady
from voussoirkit import clipext

DEFAULT_PIECE_SIZE = bytestring.MIBIBYTE
DEFAULT_THREAD_COUNT = 10

def init(url, localname=None, piece_size=DEFAULT_PIECE_SIZE):
    localname = localname or downloady.basename_from_url(url) or str(int(time.time()))
    plan = downloady.prepare_plan(url, localname, headers={'range': 'bytes=0-'})
    sql_name = localname + '.db'
    if os.path.exists(sql_name):
        raise ValueError('database already exists %s' % sql_name)
    sql = sqlite3.connect(sql_name)
    cur = sql.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS meta (url TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS pieces (indx INT, start INT, end INT, done INT)')
    cur.execute('INSERT INTO meta VALUES(?)', [url])
    cur.execute('CREATE INDEX IF NOT EXISTS index_done on pieces(done)')
    index = 0
    while True:
        start = index * piece_size
        end = start + piece_size
        end = min(end, plan['remote_total_bytes'])
        done = 0
        cur.execute('INSERT INTO pieces VALUES(?, ?, ?, ?)', [index, start, end, done])
        start += piece_size
        if start > plan['remote_total_bytes']:
            break
        index += 1
    sql.commit()
    print('Initialized %s with %d pieces' % (sql_name, index + 1))

def reset(databasename):
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur.execute('UPDATE pieces SET done = 0 WHERE done == 1')
    sql.commit()

def piece_thread(entry):
    try:
        headers = {'range': 'bytes=%d-%d' % (entry['start'], entry['end'])}
        x = downloady.download_file(entry['url'], entry['localname'], headers=headers, timeout=10)
        entry['job'].finish()
        return x
    except:
        traceback.print_exc()
        entry['job'].reset()

class Downloader:
    def __init__(self, sql_name, thread_count=10):
        self.thread_count = thread_count
        self.sql_name = sql_name
        self.localname = self.sql_name.rsplit('.db')[0]
        self.sql = sqlite3.connect(self.sql_name)
        self.cur = self.sql.cursor()
        self.url = self.cur.execute('SELECT * FROM meta').fetchone()[0]
    
    def start(self):
        self.cur.execute('SELECT * FROM pieces WHERE done == 0')
        fetch = self.cur.fetchall()
        jobs = []
        for entry in fetch:
            entry = {
                'url': self.url,
                'localname': self.localname,
                'index': entry[0],
                'start': entry[1],
                'end': entry[2],
            }
            job = Job(entry)
            jobs.append(job)

        while len(jobs) > 0:
            finished_jobs = []
            active_jobs = []
            pending_jobs = []

            for job in jobs:
                if job.state == 'finished':
                    finished_jobs.append(job)
                elif job.state == 'in progress':
                    active_jobs.append(job)
                else:
                    pending_jobs.append(job)

            for job in finished_jobs:
                self.cur.execute('UPDATE pieces SET done == 1 WHERE indx == ?', [job.entry['index']])
                print('finished #%d' % job.entry['index'])
            self.sql.commit()

            need = self.thread_count - len(active_jobs)
            while need > 0 and len(pending_jobs) > 0:
                job = pending_jobs.pop()
                print('starting #%d' % job.entry['index'])
                job.start()
                active_jobs.append(job)
                need -= 1

            jobs = pending_jobs + active_jobs
            print('%d jobs in progress' % len(active_jobs))
            print('%d jobs waiting' % len(pending_jobs))
            time.sleep(2)

class Job:
    def __init__(self, entry):
        self.state = 'pending'
        self.entry = entry

    def start(self):
        self.state = 'in progress'
        self.entry['job'] = self
        thread = threading.Thread(target=piece_thread, args=[self.entry])
        thread.daemon = True
        thread.start()

    def finish(self):
        self.state = 'finished'

    def reset(self):
        self.state = 'pending'


def init_argparse(args):
    if isinstance(args.piece_size, str):
        piece_size = bytestring.parsebytes(args.piece_size)
    else:
        piece_size = args.piece_size
    url = clipext.resolve(args.url)
    init(url, localname=args.localname, piece_size=piece_size)

def reset_argparse(args):
    reset(args.databasename)

def download_argparse(args):
    downloader = Downloader(args.databasename, int(args.thread_count))
    downloader.start()

def main(argv):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'

    p_init = subparsers.add_parser('init')
    p_init.add_argument('url')
    p_init.add_argument('localname', nargs='?', default=None)
    p_init.add_argument('--piece-size', dest='piece_size', default=DEFAULT_PIECE_SIZE)
    p_init.set_defaults(func=init_argparse)

    p_reset = subparsers.add_parser('reset')
    p_reset.add_argument('databasename')
    p_reset.set_defaults(func=reset_argparse)

    p_download = subparsers.add_parser('download')
    p_download.add_argument('databasename')
    p_download.add_argument('--threads', dest='thread_count', default=DEFAULT_THREAD_COUNT)
    p_download.set_defaults(func=download_argparse)

    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
