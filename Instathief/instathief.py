import argparse
import bs4
import datetime
import json
import os
import requests
import sys

# pip install
# https://raw.githubusercontent.com/voussoir/else/master/_voussoirkit/voussoirkit.zip
from voussoirkit import clipext
from voussoirkit import downloady


''' '''
STRFTIME = '%Y%m%d-%H%M%S'
# strftime used for filenames when downloading

URL_PROFILE = 'https://www.instagram.com/{username}'
URL_QUERY = 'https://www.instagram.com/query/'

PAGE_QUERY_TEMPLATE = '''
ig_user({user_id})
{{
    media.after({end_cur}, {count})
    {{
        count,
        nodes
        {{
            code,
            date,
            display_src,
            id,
            video_url
        }},
        page_info
    }}
}}
'''.replace('\n', '').replace(' ', '')

USERAGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
''' '''

last_cookie = None

def download_media(media_list):
    for media in media_list:
        timestamp = datetime.datetime.utcfromtimestamp(media['created'])
        timestamp = timestamp.strftime(STRFTIME)
        basename = downloady.basename_from_url(media['url'])
        extension = os.path.splitext(basename)[1]

        filename = timestamp + extension
        downloady.download_file(
            url=media['url'],
            localname=filename,
            callback_progress=downloady.progress2,
            overwrite=False,
        )

def get_page(user_id, end_cur, count, cookies):
    query = PAGE_QUERY_TEMPLATE.format(
        count=count,
        end_cur=end_cur,
        user_id=user_id,
    )
    headers = {
        'referer': 'https://www.instagram.com/',
        'user-agent': USERAGENT,
        'x-csrftoken': cookies['csrftoken'],
    }
    data = {
        'q': query,
        'ref': 'users::show',
    }

    response = requests.post(
        url=URL_QUERY,
        cookies=cookies,
        data=data,
        headers=headers,
    )
    response.raise_for_status()
    page = response.json()
    return page

def get_user_info(username):
    global last_cookie
    url = URL_PROFILE.format(username=username)
    response = requests.get(url)
    response.raise_for_status()

    text = response.text
    soup = bs4.BeautifulSoup(text, 'html.parser')

    scripts = soup.find_all('script')
    for script in scripts:
        if 'window._sharedData' in script.text:
            break
    else:
        raise Exception('Did not find expected javascript')

    user_data = script.text
    user_data = user_data.split('window._sharedData = ')[1].rstrip(';').strip()
    user_data = json.loads(user_data)
    user_data = user_data['entry_data']['ProfilePage'][0]['user']

    user_id = user_data['id']
    page_info = user_data['media']['page_info']
    if page_info['has_next_page']:
        end_cur = page_info['start_cursor']
        # Minus 1 because the queries use "after" parameters for pagination, and
        # if we just take this cursor then we will only get items after it.
        end_cur = int(end_cur) - 1
    else:
        end_cur = None

    user_data = {
        'user_id': user_id,
        'end_cur': end_cur,
        'cookies': response.cookies,
    }
    last_cookie = response.cookies
    return user_data

def get_user_media(username):
    user_info = get_user_info(username)
    end_cur = user_info.pop('end_cur')

    while True:
        page = get_page(count=50, end_cur=end_cur, **user_info)
        page = page['media']

        posts = page['nodes']
        for post in posts:
            timestamp = post['date']
            media_url = post.get('video_url') or post.get('display_src')
            ret = {
                'created': timestamp,
                'url': media_url
            }
            yield ret

        page_info = page['page_info']
        if page_info['has_next_page']:
            end_cur = page_info['end_cursor']
        else:
            break


def main():
    username = sys.argv[1]
    media = get_user_media(username)
    for (timestamp, url) in media:
        print(url)


if __name__ == '__main__':
    main()
