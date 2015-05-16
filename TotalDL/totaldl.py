import json
import requests
import os
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36'}

DOWNLOAD_DIRECTORY = ''
# Save files to this folder
# If blank, it uses the local folder

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

LIVELEAK_YOUTUBEIFRAME = 'youtube.com/embed'

LIVELEAK_RESOLUTIONS = ['h264_base', 'h264_720p', 'h264_270p']

DO_GENERIC = True
# If true, attempt to download whatever URL goes in
# Else, only download from the explicitly supported sites

''' End user config '''

last_request = 0

if DOWNLOAD_DIRECTORY != '':
	if DOWNLOAD_DIRECTORY[-1] not in ['/', '\\']:
		DOWNLOAD_DIRECTORY += '\\'
	if not os.path.exists(DOWNLOAD_DIRECTORY):
		os.makedirs(DOWNLOAD_DIRECTORY)

class StatusExc(Exception):
	pass

def download_file(url, localname):
	localname = DOWNLOAD_DIRECTORY + localname
	if 'twimg' in url:
		localname = localname.replace(':large', '')
		localname = localname.replace(':small', '')
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

def handle_imgur(url, albumid='', customname=None):
	name = url.split('/')[-1]
	if 'imgur.com' in name:
		# This link doesn't appear to have an image id
		return

	basename = name.split('.')[0]
	if '.' in name:
		# This is a direct image link
		if customname:
			# replace the imgur ID with the customname, keep ext.
			name = '%s.%s' % (customname, name.split('.')[-1])
		if albumid and albumid != basename:

			if IMGUR_ALBUMFOLDERS:

				if not os.path.exists(DOWNLOAD_DIRECTORY + albumid):
					os.makedirs(DOWNLOAD_DIRECTORY + albumid)
				localpath = '%s\\%s' % (albumid, name)
	
			else:
				localpath = '%s_%s' % (albumid, name)

		else:
			localpath = name

		download_file(url, localpath)

	else:
		# Not a direct image link, let's read the html.
		images = handle_imgur_html(url)
		if customname:
			name = customname
		print('\tFound %d images' % len(images))
		if len(images) > 1:
			for imagei in range(len(images)):
				image = images[imagei]
				handle_imgur(image, albumid=name, customname=str(imagei))
		else:
			handle_imgur(images[0], customname=name)


def handle_gfycat(url, customname=None):
	name = url.split('/')[-1]
	name = name.split('.')[0]
	if customname:
		filename = customname
	else:
		filename = name

	if GFYCAT_MP4:
		name += '.mp4'
		filename += '.mp4'
	else:
		name += '.webm'
		filename += '.webm'

	for subdomain in GFYCAT_SUBDOMAINS:
		url = 'http://%s.gfycat.com/%s' % (subdomain, name)
		try:
			download_file(url, filename)
			break
		except StatusExc:
			pass


def handle_vimeo(url, customname=None):
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
	if customname:
		filename = customname + '.mp4'
	else:
		filename = name + '.mp4'
	download_file(fileurl, filename)


def handle_liveleak(url, customname=None):
	if customname:
		name = customname
	else:
		name = url.split('=')[1]
	name += '.mp4'
	pagedata = request_get(url)
	pagedata = pagedata.text
	if LIVELEAK_YOUTUBEIFRAME in pagedata:
		pagedata = pagedata.split('\n')
		pagedata = [line for line in pagedata if LIVELEAK_YOUTUBEIFRAME in line]
		pagedata = pagedata[0]
		pagedata = pagedata.split('src="')[1]
		pagedata = pagedata.split('"')[0]
		print('\tFound youtube embed')
		handle_master(pagedata)
	else:
		pagedata = pagedata.split('file: "')[1]
		pagedata = pagedata.split('",')[0]
		original = pagedata
		pagedata = pagedata.split('.')
		for spoti in range(len(pagedata)):
			if 'h264_' in pagedata[spoti]:
				pagedata[spoti] = 'LIVELEAKRESOLUTION'
		pagedata = '.'.join(pagedata)
		for res in LIVELEAK_RESOLUTIONS:
			url = pagedata.replace('LIVELEAKRESOLUTION', res)
			try:
				download_file(url, name)
				return
			except StatusExc:
				pass
		download_file(original, name)



def handle_youtube(url, customname=None):
	# The customname doesn't do anything on this function
	# but handle_master works better if everything uses
	# the same format.
	url = url.replace('&amp;', '&')
	url = url.replace('feature=player_embedded&', '')
	url = url.replace('&feature=player_embedded', '')
	os.system('youtube-dl "{0}" --force-ipv4 -o "/{1}/%(title)s.%(ext)s"'.format(url, DOWNLOAD_DIRECTORY))


def handle_twitter(url, customname=None):
	pagedata = request_get(url)
	pagedata = pagedata.text
	try:
		link = pagedata.split('data-url="')[1]
		link = link.split('"')[0]
		handle_master(link, customname=customname)
		return
	except IndexError:
		try:
			link = pagedata.split('data-expanded-url="')[1]
			link = link.split('"')[0]
			handle_master(link, customname=customname)
			return
		except IndexError:
			pass
	print('\tNo media detected')


def handle_generic(url, customname=None):
	try:
		name = url.split('/')[-1]
		if customname:
			name = '%s.%s' % (customname, name.split('.')[-1])
		if '.' not in name:
			name += '.html'
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
	'youtu.be': handle_youtube,
	'twitter.com': handle_twitter
	}

def handle_master(url, customname=None):
	print('Handling %s' % url)
	for handlerkey in HANDLERS:
		if handlerkey.lower() in url.lower():
			HANDLERS[handlerkey](url, customname=customname)
			return
	if DO_GENERIC:
		handle_generic(url, customname=customname)

def test_imgur():
	# Imgur gallery album
	handle_master('http://imgur.com/gallery/s4WLG')

	# Imgur standard album with customname
	handle_master('http://imgur.com/a/s4WLG', customname='album')

	# Imgur indirect 
	handle_master('http://imgur.com/gvJUct0')

	# Imgur indirect single with customname
	handle_master('http://imgur.com/gvJUct0', customname='indirect')

	# Imgur direct single
	handle_master('http://i.imgur.com/gvJUct0.jpg')

def test_gfycat():
	# Gfycat direct .gif
	handle_master('http://giant.gfycat.com/FatherlyBruisedIberianchiffchaff.gif')

	# Gfycat general link
	handle_master('http://www.gfycat.com/RawWetFlatcoatretriever')

	# Gfycat general link with customname
	handle_master('http://www.gfycat.com/RawWetFlatcoatretriever', customname='gfycatgeneral')

def test_vimeo():
	# Vimeo standard link
	handle_master('https://vimeo.com/109405701')

	# Vimeo player link with customname
	handle_master('https://player.vimeo.com/video/109405701', customname='vimeoplayer')

def test_liveleak():
	# LiveLeak standard link
	handle_master('http://www.liveleak.com/view?i=9d1_1429192014')

	# Liveleak article with youtube embed
	handle_master('http://www.liveleak.com/view?i=ab8_1367941301')

	# LiveLeak standard link with customname
	handle_master('http://www.liveleak.com/view?i=9d1_1429192014', customname='liveleak')

def test_youtube():
	# Youtube standard link
	handle_master('https://www.youtube.com/watch?v=bEgeh5hA5ko')

	# Youtube short link
	handle_master('https://youtu.be/GjOBTstnW20')

	# Youtube player embed link
	handle_master('https://www.youtube.com/watch?feature=player_embedded&amp;v=bEgeh5hA5ko')

def test_twitter():
	# Tiwtter with twitter-image embed
	handle_master('https://twitter.com/PetoLucem/status/599493836214272000')

	# Twitter with twitter-image embed
	handle_master('https://twitter.com/Jalopnik/status/598287843128188929')

	# Twitter with twitter-image embed and customname
	handle_master('https://twitter.com/Jalopnik/status/598287843128188929', customname='twits')

	# Twitter with youtube embed
	handle_master('https://twitter.com/cp_orange_x3/status/599705117420457984')

	# Twitter plain text
	handle_master('https://twitter.com/cp_orange_x3/status/599700702382817280')

def test_generic():
	# Some link that might work
	handle_master('https://raw.githubusercontent.com/voussoir/reddit/master/SubredditBirthdays/show/statistics.txt')

	# Some link that might work with customname
	handle_master('https://raw.githubusercontent.com/voussoir/reddit/master/SubredditBirthdays/show/statistics.txt', customname='sss')

	# Some link that might work
	handle_master('https://github.com/voussoir/reddit/tree/master/SubredditBirthdays/show')

if __name__ == '__main__':
	#test_imgur()
	#test_gfycat()
	#test_vimeo()
	#test_liveleak()
	#test_youtube()
	test_twitter()
	#test_generic()
	pass