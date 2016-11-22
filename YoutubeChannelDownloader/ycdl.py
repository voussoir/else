import os
import sqlite3
import ytapi

# AVAILABLE FORMATTERS:
# url, id
YOUTUBE_DL_COMMAND = 'touch {id}.ytqueue'

SQL_CHANNEL_COLUMNS = [
    'id',
    'name',
    'directory',
]

SQL_VIDEO_COLUMNS = [
    'id',
    'published',
    'author_id',
    'title',
    'description',
    'thumbnail',
    'download',
]

SQL_CHANNEL = {key:index for (index, key) in enumerate(SQL_CHANNEL_COLUMNS)}
SQL_VIDEO = {key:index for (index, key) in enumerate(SQL_VIDEO_COLUMNS)}

DATABASE_VERSION = 1
DB_INIT = '''
PRAGMA count_changes = OFF;
PRAGMA cache_size = 10000;
PRAGMA user_version = {user_version};
CREATE TABLE IF NOT EXISTS channels(
    id TEXT,
    name TEXT,
    directory TEXT COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS videos(
    id TEXT,
    published INT,
    author_id TEXT,
    title TEXT,
    description TEXT,
    thumbnail TEXT,
    download TEXT
);


CREATE INDEX IF NOT EXISTS index_channel_id on channels(id);
CREATE INDEX IF NOT EXISTS index_video_id on videos(id);
CREATE INDEX IF NOT EXISTS index_video_published on videos(published);
CREATE INDEX IF NOT EXISTS index_video_download on videos(download);

'''.format(user_version=DATABASE_VERSION)

DEFAULT_DBNAME = 'ycdl.db'

ERROR_DATABASE_OUTOFDATE = 'Database is out-of-date. {current} should be {new}'

def verify_is_abspath(path):
    '''
    TO DO: Determine whether this is actually correct.
    '''
    if os.path.abspath(path) != path:
        raise ValueError('Not an abspath')

class YCDL:
    def __init__(self, youtube, database_filename=None):
        self.youtube = youtube
        if database_filename is None:
            database_filename = DEFAULT_DBNAME

        existing_database = os.path.exists(database_filename)
        self.sql = sqlite3.connect(database_filename)
        self.cur = self.sql.cursor()

        if existing_database:
            self.cur.execute('PRAGMA user_version')
            existing_version = self.cur.fetchone()[0]
            if existing_version != DATABASE_VERSION:
                message = ERROR_DATABASE_OUTOFDATE
                message = message.format(current=existing_version, new=DATABASE_VERSION)
                print(message)
                raise SystemExit

        statements = DB_INIT.split(';')
        for statement in statements:
            self.cur.execute(statement)

    def add_channel(self, channel_id, name=None, download_directory=None, get_videos=True, commit=False):
        if self.get_channel(channel_id) is not None:
            return

        if name is None:
            name = self.youtube.get_user_name(channel_id)

        data = [None] * len(SQL_CHANNEL)
        data[SQL_CHANNEL['id']] = channel_id
        data[SQL_CHANNEL['name']] = name
        if download_directory is not None:
            verify_is_abspath(download_directory)
        data[SQL_CHANNEL['directory']] = download_directory

        self.cur.execute('INSERT INTO channels VALUES(?, ?, ?)', data)
        if get_videos:
            self.refresh_channel(channel_id, commit=False)
        if commit:
            self.sql.commit()

    def channel_has_pending(self, channel_id):
        self.cur.execute('SELECT * FROM videos WHERE author_id == ? AND download == "pending"', [channel_id])
        return self.cur.fetchone() is not None

    def channel_directory(self, channel_id):
        self.cur.execute('SELECT * FROM channels WHERE id == ?', [channel_id])
        fetch = self.cur.fetchone()
        if fetch is None:
            return None
        return fetch[SQL_CHANNEL['directory']]

    def download_video(self, video, force=False):
        if not isinstance(video, ytapi.Video):
            video = self.youtube.get_video(video)

        self.add_channel(video.author_id, get_videos=False, commit=False)
        status = self.insert_video(video, commit=True)

        if status['row'][SQL_VIDEO['download']] != 'pending' and not force:
            print('That video does not need to be downloaded.')
            return

        download_directory = self.channel_directory(video.author_id)
        download_directory = download_directory or os.getcwd()

        current_directory = os.getcwd()
        os.makedirs(download_directory, exist_ok=True)
        os.chdir(download_directory)
        url = 'https://www.youtube.com/watch?v={id}'.format(id=video.id)
        command = YOUTUBE_DL_COMMAND.format(url=url, id=video.id)
        os.system(command)
        os.chdir(current_directory)

        self.cur.execute('UPDATE videos SET download = "downloaded" WHERE id == ?', [video.id])
        self.sql.commit()

    def get_channel(self, channel_id):
        self.cur.execute('SELECT * FROM channels WHERE id == ?', [channel_id])
        fetch = self.cur.fetchone()
        if not fetch:
            return None
        fetch = {key: fetch[SQL_CHANNEL[key]] for key in SQL_CHANNEL}
        return fetch

    def get_channels(self):
        self.cur.execute('SELECT * FROM channels')
        channels = self.cur.fetchall()
        channels = [{key: channel[SQL_CHANNEL[key]] for key in SQL_CHANNEL} for channel in channels]
        channels.sort(key=lambda x: x['name'].lower())
        return channels

    def get_videos_by_channel(self, channel_id):
        self.cur.execute('SELECT * FROM videos WHERE author_id == ?', [channel_id])
        videos = self.cur.fetchall()
        if not videos:
            return []
        videos = [{key: video[SQL_VIDEO[key]] for key in SQL_VIDEO} for video in videos]
        videos.sort(key=lambda x: x['published'], reverse=True)
        return videos

    def mark_video_state(self, video_id, state, commit=True):
        '''
        Mark the video as ignored, pending, or downloaded.
        '''
        if state not in ['ignored', 'pending', 'downloaded']:
            raise ValueError(state)
        self.cur.execute('SELECT * FROM videos WHERE id == ?', [video_id])
        if self.cur.fetchone() is None:
            raise KeyError(video_id)
        self.cur.execute('UPDATE videos SET download = ? WHERE id == ?', [state, video_id])
        if commit:
            self.sql.commit()

    def refresh_channel(self, channel_id, force=True, commit=True):
        video_generator = self.youtube.get_user_videos(uid=channel_id)
        for video in video_generator:
            status = self.insert_video(video, commit=False)
            if not force and not status['new']:
                break
        if commit:
            self.sql.commit()

    def insert_video(self, video, commit=True):
        if not isinstance(video, ytapi.Video):
            video = self.youtube.get_video(video)

        self.add_channel(video.author_id, get_videos=False, commit=False)
        self.cur.execute('SELECT * FROM videos WHERE id == ?', [video.id])
        fetch = self.cur.fetchone()
        if fetch is not None:
            return {'new': False, 'row': fetch}

        data = [None] * len(SQL_VIDEO)
        data[SQL_VIDEO['id']] = video.id
        data[SQL_VIDEO['published']] = video.published
        data[SQL_VIDEO['author_id']] = video.author_id
        data[SQL_VIDEO['title']] = video.title
        data[SQL_VIDEO['description']] = video.description
        data[SQL_VIDEO['thumbnail']] = video.thumbnail['url']
        data[SQL_VIDEO['download']] = 'pending'

        self.cur.execute('INSERT INTO videos VALUES(?, ?, ?, ?, ?, ?, ?)', data)
        if commit:
            self.sql.commit()
        return {'new': True, 'row': data}
