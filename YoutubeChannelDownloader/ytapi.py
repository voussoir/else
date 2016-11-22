import apiclient.discovery
import datetime
import sqlite3

class Video:
    def __init__(self, snippet):
        self.id = snippet['id']

        snippet = snippet['snippet']
        self.title = snippet['title'] or '[untitled]'
        self.description = snippet['description']
        self.author_id = snippet['channelId']
        self.author_name = snippet['channelTitle']
        # Something like '2016-10-01T21:00:01'
        self.published_string = snippet['publishedAt']
        published = snippet['publishedAt']
        published = published.split('.')[0]
        published = datetime.datetime.strptime(published, '%Y-%m-%dT%H:%M:%S')
        self.published = published.timestamp()

        thumbnails = snippet['thumbnails']
        best_thumbnail = max(thumbnails, key=lambda x: thumbnails[x]['width'] * thumbnails[x]['height'])
        self.thumbnail = thumbnails[best_thumbnail]


class Youtube:
    def __init__(self, key):
        youtube = apiclient.discovery.build(
            developerKey=key,
            serviceName='youtube',
            version='v3',
        )
        self.youtube = youtube

    def get_user_name(self, uid):
        user = self.youtube.channels().list(part='snippet', id=uid).execute()
        return user['items'][0]['snippet']['title']

    def get_user_videos(self, username=None, uid=None):
        if username:
            user = self.youtube.channels().list(part='contentDetails', forUsername=username).execute()
        else:
            user = self.youtube.channels().list(part='contentDetails', id=uid).execute()
        upload_playlist = user['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        page_token = None
        while True:
            items = self.youtube.playlistItems().list(
                maxResults=50,
                pageToken=page_token,
                part='contentDetails',
                playlistId=upload_playlist,
            ).execute()
            page_token = items.get('nextPageToken', None)
            new = [item['contentDetails']['videoId'] for item in items['items']]
            count = len(new)
            new = self.get_video(new)
            new.sort(key=lambda x: x.published, reverse=True)
            yield from new
            #print('Found %d more, %d total' % (count, len(videos)))
            if page_token is None or count < 50:
                break

    def get_video(self, video_ids):
        if isinstance(video_ids, str):
            singular = True
            video_ids = [video_ids]
        else:
            singular = False
        video_ids = chunk_sequence(video_ids, 50)
        results = []
        for chunk in video_ids:
            chunk = ','.join(chunk)
            data = self.youtube.videos().list(part='snippet', id=chunk).execute()
            items = data['items']
            results += items
            #print('Found %d more, %d total' % (len(items), len(results)))
        results = [Video(snippet) for snippet in results]
        if singular and len(results) == 1:
            return results[0]
        return results


def chunk_sequence(sequence, chunk_length, allow_incomplete=True):
    """Given a sequence, divide it into sequences of length `chunk_length`.

    :param allow_incomplete: If True, allow the final chunk to be shorter if the
        given sequence is not an exact multiple of `chunk_length`.
        If False, the incomplete chunk will be discarded.
    """
    (complete, leftover) = divmod(len(sequence), chunk_length)
    if not allow_incomplete:
        leftover = 0

    chunk_count = complete + min(leftover, 1)

    chunks = []
    for x in range(chunk_count):
        left = chunk_length * x
        right = left + chunk_length
        chunks.append(sequence[left:right])

    return chunks
