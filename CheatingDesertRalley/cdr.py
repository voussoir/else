import requests
import time as timem
import random

URL = 'http://www.uf3k.com/games/safarirally/record.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
    'Host': 'www.uf3k.com',
    'Referer': 'http://media-ak.y8.com/system/contents/4531/original/desertrally.swf',
    'X-Requested-With': 'ShockwaveFlash/19.0.0.185',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US;en;q=0.8',
    'Connection': 'keep-alive',
}
def make_run(name, distance, avg_speed=None, top_speed=None, time=None, course=1, vehicle=None):
    if avg_speed is None:
        avg_speed = round(random.randint(20, 25) + random.triangular(), 4)
    if top_speed is None:
        top_speed = random.randint(140, 170)
    if time is None:
        time = round(distance * avg_speed * TIME_MULT, 4)
    if vehicle is None:
        vehicle = random.randint(0, 4)
    params = {'cachebuster': int(timem.time() * 1000)}
    data = {
        'long_name': 'ultraflash3000',
        'avg_speed': avg_speed,
        'top_speed': top_speed,
        'time': time,
        'distance': distance,
        'course': course,
        'vehicle': vehicle,
        'name': name
    }
    request = requests.Request('POST', url=URL, params=params, data=data)
    session = requests.Session()
    return session.send(request.prepare())

TIME_MULT = 0.0008128971962616823