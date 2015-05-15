import json
import requests
import os
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36'}

IMGUR_ALBUM_INDV = '"og:image"content="htt'
# The HTML string which tells us that an image link is
# on this line.

IMGUR_ALBUMFOLDERS = True
# If True, the individual images belonging to an album will be placed
#  into a folder named after the album, like <album_id>/<img_id>.jpg
# Else, files will be named <album_id>_<img_id>.jpg and placed
#  in the local folder.

GFYCAT_MP4 = True
# If True, download gfycat urls in .mp4
# Else, .webm

GFYCAT_SUBDOMAINS = ['zippy', 'fat', 'giant']

SLEEPINESS = 2
# The number of seconds to wait in between making requests
# Similar to PRAW's ratelimit handling.
# Not required, but probably better for the environment.

VIMEO_DICT_START = '"files":{"h264":'
VIMEO_DICT_END = ',"hls"'
# The HTML string which tells us where the mp4 file is

VIMEO_PRIORITY = ['hd', 'sd', 'mobile']
# Download files in this priority

DO_GENERIC = True
# If true, attempt to download whatever URL goes in
# Else, only download from the explicitly supported sites

''' End user config '''

last_request = 0

class StatusExc(Exception):
	pass

def download_file(url, localname):
	if os.path.exists(localname):
		print('\t%s already exists!!' % localname)
		return
	print('\tDownloading %s' % localname)
	downloading = request_get(url, stream=True)
	localfile = open(localname, 'wb')
	for chunk in downloading.iter_content(chunk_size=1024):
		if chunk:
			localfile.write(chunk)
	return True

def request_get(url, stream=False):
	global last_request
	now = time.time()
	diff = now - last_request
	if diff < SLEEPINESS:
		diff = SLEEPINESS - diff
		time.sleep(diff)
	last_request = time.time()
	req = requests.get(url, stream=stream, headers=HEADERS)
	if req.status_code != 200:
		raise StatusExc("Status code %d on url %s" % (req.status_code, url))
	return req

##############################################################################
                                                                            ##
def handle_imgur_html(url):
	pagedata = request_get(url)
	pagedata = pagedata.text.replace(' ', '')
	pagedata = pagedata.split('\n')
	pagedata = [line.strip() for line in pagedata]
	pagedata = [line for line in pagedata if IMGUR_ALBUM_INDV in line]
	pagedata = [line.split('"')[-2] for line in pagedata]
	links = []
	for image in pagedata:
		image = image.split('?')[0]
		if image not in links:
			links.append(image)
	return links

def handle_imgur(url, albumid=''):
	name = url.split('/')[-1]
	if 'imgur.com' in name:
		# This link doesn't appear to have an image id
		return

	basename = name.split('.')[0]
	if '.' in name:
		# This is a direct image link
		if IMGUR_ALBUMFOLDERS and albumid and albumid != basename:
			if not os.path.exists(albumid):
				os.makedirs(albumid)
			localpath = '%s\\%s' % (albumid, name)

		elif albumid and albumid != basename:
			localpath = '%s_%s' % (albumid, name)

		else:
			localpath = name

		download_file(url, localpath)

	else:
		# Not a direct image link, let's read the html.
		images = handle_imgur_html(url)
		print('\tFound %d images' % len(images))
		for image in images:
			handle_imgur(image, albumid=name)


def handle_gfycat(url):
	name = url.split('/')[-1]
	name = name.split('.')[0]
	if GFYCAT_MP4:
		name += '.mp4'
	else:
		name += '.webm'
	for subdomain in GFYCAT_SUBDOMAINS:
		url = 'http://%s.gfycat.com/%s' % (subdomain, name)
		try:
			download_file(url, name)
			break
		except StatusExc:
			pass


def handle_vimeo(url):
	name = url.split('/')[-1]
	name = name.split('?')[0]
	try:
		int(name)
	except ValueError as e:
		print('Could not identify filename of %s' % url)
		raise e
	url = 'http://player.vimeo.com/video/%s' % name
	pagedata = request_get(url)
	pagedata = pagedata.text
	pagedata = pagedata.replace('</script>', '<script')
	pagedata = pagedata.split('<script>')
	for chunk in pagedata:
		if VIMEO_DICT_START in chunk:
			break
	chunk = chunk.split(VIMEO_DICT_START)[1]
	chunk = chunk.split(VIMEO_DICT_END)[0]
	chunk = json.loads(chunk)
	
	for priority in VIMEO_PRIORITY:
		if priority in chunk:
			fileurl = chunk[priority]['url']
			break
	filename = name + '.mp4'
	download_file(fileurl, filename)


def handle_liveleak(url):
	filename = url.split('=')[1]
	filename += '.mp4'
	pagedata = request_get(url)
	pagedata = pagedata.text
	pagedata = pagedata.split('file: "')[1]
	pagedata = pagedata.split('",')[0]
	pagedata = pagedata.split('.')
	for spoti in range(len(pagedata)):
		if 'h264_' in pagedata[spoti]:
			pagedata[spoti] = 'h264_720p'
	pagedata = '.'.join(pagedata)
	download_file(pagedata, filename)


def handle_youtube(url):
	os.system('youtube-dl %s --force-ipv4' % url)


def handle_generic(url):
	try:
		name = url.split('/')[-1]
		download_file(url, name)
	except:
		pass
                                                                            ##
##############################################################################

HANDLERS = {
	'imgur.com': handle_imgur,
	'gfycat.com': handle_gfycat,
	'vimeo.com': handle_vimeo,
	'liveleak.com': handle_liveleak,
	'youtube.com': handle_youtube,
	'youtu.be': handle_youtube
	}

def handle_master(url):
	print('Handling %s' % url)
	for handlerkey in HANDLERS:
		if handlerkey.lower() in url.lower():
			HANDLERS[handlerkey](url)
			return
	if DO_GENERIC:
		handle_generic(url)

def test(imgur=True, gfycat=True, vimeo=True, liveleak=True, youtube=True, generic=True):
	print('Testing')
	if imgur:
		# Imgur gallery album
		handle_master('http://imgur.com/gallery/s4WLG')

		# Imgur album
		handle_master('http://imgur.com/a/s4WLG')

		# Imgur indirect single
		handle_master('http://imgur.com/gvJUct0')

		# Imgur direct single
		handle_master('http://i.imgur.com/gvJUct0.jpg')

	if gfycat:
		# Gfycat direct .gif
		handle_master('http://giant.gfycat.com/FatherlyBruisedIberianchiffchaff.gif')

		# Gfycat general link
		handle_master('http://www.gfycat.com/RawWetFlatcoatretriever')

	if vimeo:
		# Vimeo standard link
		handle_master('https://vimeo.com/109405701')

	if liveleak:
		# LiveLeak standard link
		handle_master('http://www.liveleak.com/view?i=9d1_1429192014')

	if youtube:
		# Youtube standard link
		handle_master('https://www.youtube.com/watch?v=bEgeh5hA5ko')

		# Youtube short link
		handle_master('https://youtu.be/GjOBTstnW20')

	if generic:
		# Some link that might work
		handle_master('https://raw.githubusercontent.com/voussoir/reddit/master/SubredditBirthdays/show/statistics.txt')

		# Some link that might work
		handle_master('https://github.com/voussoir/reddit/tree/master/SubredditBirthdays/show')

test()