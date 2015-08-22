import json
import praw
import oauthPS2Bot
import os
import re
import requests
import shlex
import sqlite3
import sys
import time
import traceback
from datetime import datetime,timedelta
import warnings
warnings.filterwarnings("ignore")


##############################################################################
## CONFIG
URL_CENSUS_CHAR_PC = 'http://census.daybreakgames.com/s:vAPP/get/ps2:v2/character/?name.first=%s&c:case=false&c:resolve=stat_history,faction,world,outfit_member_extended'
URL_CENSUS_CHAR_PS4_US = 'http://census.daybreakgames.com/s:vAPP/get/ps2ps4us:v2/character/?name.first=%s&c:case=false&c:resolve=stat_history,faction,world,outfit_member_extended'
URL_CENSUS_CHAR_PS4_EU = 'http://census.daybreakgames.com/s:vAPP/get/ps2ps4eu:v2/character/?name.first=%s&c:case=false&c:resolve=stat_history,faction,world,outfit_member_extended'

URL_CENSUS_CHAR_STAT_PC = 'http://census.daybreakgames.com/s:vAPP/get/ps2:v2/characters_stat?character_id=%s&c:limit=5000'
URL_CENSUS_CHAR_STAT_PS4_US = 'http://census.daybreakgames.com/s:vAPP/get/ps2ps4us:v2/characters_stat?character_id=%s&c:limit=5000'
URL_CENSUS_CHAR_STAT_PS4_EU = 'http://census.daybreakgames.com/s:vAPP/get/ps2ps4eu:v2/characters_stat?character_id=%s&c:limit=5000'

URL_SERVER_STATUS = 'https://census.daybreakgames.com/json/status?game=ps2'

URL_DASANFALL = "[[dasanfall]](http://stats.dasanfall.com/ps2/player/%s)"
URL_FISU = "[[fisu]](http://ps2.fisu.pw/player/?name=%s)"
URL_FISU_PS4_US = '[[fisu]](http://ps4us.ps2.fisu.pw/player/?name=%s)'
URL_FISU_PS4_EU = '[[fisu]](http://ps4eu.ps2.fisu.pw/player/?name=%s)'
URL_PSU = "[[psu]](http://www.planetside-universe.com/character-%s.php)"
URL_PLAYERS = "[[players]](https://www.planetside2.com/players/#!/%s)"
URL_KILLBOARD = "[[killboard]](https://www.planetside2.com/players/#!/%s/killboard)"

USERNAME = "ps2bot"

SERVERS = {
    '1': 'Connery (US West)',
    '17': 'Emerald (US East)',
    '10': 'Miller (EU)',
    '13': 'Cobalt (EU)',
    '25': 'Briggs (AU)',
    '19': 'Jaeger',
    '1000': 'Genudine',
    '1001': 'Palos',
    '1002': 'Crux',
    '2000': 'Ceres',
    '2001': 'Lithcorp'
}

REPLY_TEXT_TEMPLATE = '''
**Some stats about {char_name_truecase} ({game_version}).**

------

- Character created: {char_creation}
- Last login: {char_login}
- Time played: {char_playtime} ({char_logins} login{login_plural})
- Battle rank: {char_rank}
- Faction: {char_faction_en}
- Server: {char_server}
- Outfit: {char_outfit}
- Score: {char_score} | Captured: {char_captures} | Defended: {char_defended}
- Medals: {char_medals} | Ribbons: {char_ribbons} | Certs: {char_certs}
- Kills: {char_kills} | Assists: {char_assists} | Deaths: {char_deaths} | KDR: {char_kdr}
- Links: {third_party_websites}


'''

REPLY_TEXT_FOOTER = '''

------

^^This ^^post ^^was ^^made ^^by ^^a ^^bot.
^^Have ^^feedback ^^or ^^a ^^suggestion?
[^^\[pm ^^the ^^creator\]]
(https://np.reddit.com/message/compose/?to=microwavable_spoon&subject=PS2Bot%20Feedback)
^^| [^^\[see ^^my ^^code\]](https://github.com/plasticantifork/PS2Bot)
'''

####                                        ####
# For FUNCTION_MAP, see the bottom of the file #
####                                        ####
COMMAND_IDENTIFIERS = ['/u/' + USERNAME, 'u/' + USERNAME]
COMMAND_IDENTIFIERS = [c.lower() for c in COMMAND_IDENTIFIERS]
MULTIPLE_COMMAND_JOINER = '\n&nbsp;\n_____\n_____\n&nbsp;\n'

## END OF CONFIG
##############################################################################


sql = sqlite3.connect((os.path.join(sys.path[0],'ps2bot-sql.db')))
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldmentions(id TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS mentionindex on oldmentions(id)')
sql.commit()

print('logging in')
r = oauthPS2Bot.login()
#import bot
#r = bot.oG()

def now_stamp():
    psttime = datetime.utcnow() - timedelta(hours=7)
    time_stamp = psttime.strftime("%m-%d-%y %I:%M:%S %p PST ::")
    return time_stamp


###############################################################################
## FUNCTIONMAP FUNCTIONS
## The arguments for these functions are provided by functionmap_line().
## Since we're working with user-provided input, we need to be ready to accept
## 0 - inf arguments. Thus, each function has default values for each parameter
## and a *trash bin where we can dump anything extra. This allows us to return
## when given insufficient input, and accept unlimited trash if we need to.
## Your function may take advantage of *trash if you want.

def generate_report_pc(charname=None, *trash):
    if charname is None:
        return
    third_parties = [
    {'url': URL_DASANFALL, 'identifier': 'char_id'},
    {'url': URL_FISU, 'identifier': 'char_name'},
    {'url': URL_PSU, 'identifier': 'char_id'},
    {'url': URL_PLAYERS, 'identifier': 'char_id'},
    {'url': URL_KILLBOARD, 'identifier': 'char_id'}
    ]
    return generate_report(charname, URL_CENSUS_CHAR_PC, URL_CENSUS_CHAR_STAT_PC, third_parties, 'PC')

def generate_report_ps4_us(charname=None, *trash):
    if charname is None:
        return
    third_parties = [
    {'url': URL_FISU_PS4_US, 'identifier': 'char_name'}
    ]
    return generate_report(charname, URL_CENSUS_CHAR_PS4_US, URL_CENSUS_CHAR_STAT_PS4_US, third_parties, 'PS4 US')

def generate_report_ps4_eu(charname=None, *trash):
    if charname is None:
        return
    third_parties = [
    {'url': URL_FISU_PS4_EU, 'identifier': 'char_name'}
    ]
    return generate_report(charname, URL_CENSUS_CHAR_PS4_EU, URL_CENSUS_CHAR_STAT_PS4_EU, third_parties, 'PS4 EU')

def report_server_status(*trash):
    status_updown = {'low': 'UP','medium': 'UP','high': 'UP','down': 'DOWN'}
    status_pop = {'down': ''}
    server_regions = {'Palos': 'Palos (US)','Genudine': 'Genudine (US)','Crux': 'Crux (US)'}
    jcontent = json.loads(requests.get(URL_SERVER_STATUS).text)
    results = []

    def status_reader(jinfo, header):
        table = []
        entries = []
        table.append(header)
        table.append('\nserver | status | population')
        table.append(':- | :- | :-')

        for server, status in jinfo.items():
            # These servers had their players migrated to other servers
            # https://forums.daybreakgames.com/ps2/index.php?threads/ps4-game-update-2-8-12.231243/
            if any(nonexist in server for nonexist in ['Dahaka', 'Xelas', 'Rashnu', 'Searhus']):
                continue
            server = server_regions.get(server, server)
            pop = status['status']
            updown = status_updown[pop]
            pop = status_pop.get(pop, pop)
            entries.append('%s | %s | %s' % (server, updown, pop))

        entries.sort(key=lambda x: ('(US' in x, '(EU' in x, '(AU' in x, x), reverse=True)
        table += entries
        table.append('\n\n')
        return table

    results += status_reader(jcontent['ps2']['Live'], '**PC**')
    results += status_reader(jcontent['ps2']['Live PS4'], '**PS4**')
    results = '\n'.join(results)
    return results

## END OF FUNCTIONMAP FUNCTIONS
###############################################################################


def generate_report(charname, url_census, url_statistics, third_parties, game_version):
    try:
        census_char = requests.get(url_census % charname)
        census_char = census_char.text
        census_char = json.loads(census_char)
    except (IndexError, KeyError, requests.exceptions.HTTPError):
        return None

    if census_char['returned'] != 1:
        # no player with this name was found
        return
            
    census_char = census_char['character_list'][0]
    char_name_truecase = census_char['name']['first']
    char_id = census_char['character_id']
    try:
        census_stat = requests.get(url_statistics % char_id)
        census_stat = census_stat.text
        census_stat = json.loads(census_stat)
        if census_stat['returned'] == 0:
            # When a player has an account, but never logged in / played,
            # his stats page is empty and broken, so just return
            return
    except (IndexError, KeyError, requests.exceptions.HTTPError):
        return
        
    time_format = "%a, %b %d, %Y (%m/%d/%y), %I:%M:%S %p PST"
    char_creation = time.strftime(time_format, time.localtime(float(census_char['times']['creation'])))
    char_login = time.strftime(time_format, time.localtime(float(census_char['times']['last_login'])))
    char_login_count = int(float(census_char['times']['login_count']))
    char_hours, char_minutes = divmod(int(census_char['times']['minutes_played']), 60)
    
    char_playtime = "{:,} hour{s}".format(char_hours, s='' if char_hours == 1 else 's')
    char_playtime += " {:,} minute{s}".format(char_minutes, s='' if char_minutes == 1 else 's')

    try:
        char_score = int(census_char['stats']['stat_history'][8]['all_time'])
        char_capture = int(census_char['stats']['stat_history'][3]['all_time'])
        char_defend = int(census_char['stats']['stat_history'][4]['all_time'])
        char_medal = int(census_char['stats']['stat_history'][6]['all_time'])
        char_ribbon = int(census_char['stats']['stat_history'][7]['all_time'])
        char_certs = int(census_char['stats']['stat_history'][1]['all_time'])
    except (IndexError, KeyError, ValueError):
        char_score = 0
        char_capture = 0
        char_defend = 0
        char_medal = 0
        char_ribbon = 0
        char_certs = 0

    char_rank = '%s' % census_char['battle_rank']['value']
    char_rank_next = census_char['battle_rank']['percent_to_next']
    if char_rank_next != "0":
        char_rank += " (%s%% to next)" % char_rank_next

    char_faction = census_char['faction']
    try:
        char_outfit = census_char['outfit_member']
        if char_outfit['member_count'] != "1":
            members = '{:,}'.format(int(char_outfit['member_count']))
            char_outfit = '[%s] %s (%s members)' % (char_outfit['alias'], char_outfit['name'], members)
        else:
            char_outfit = '[%s] %s (1 member)' % (char_outfit['alias'], char_outfit['name'])
    except KeyError:
        char_outfit = "None"

    try:
        char_kills = int(census_char['stats']['stat_history'][5]['all_time'])
        char_deaths = int(census_char['stats']['stat_history'][2]['all_time'])
        if char_deaths != 0:
            char_kdr = round(char_kills/char_deaths,3)
        else:
            char_kdr = char_kills
    except (KeyError, ZeroDivisionError):
        char_kills = 0
        char_deaths = 0
        char_kdr = 0

    char_stat = census_stat['characters_stat_list']
    #print(char_stat)
    char_assists = 0
    try:
        for stat in char_stat:
            if stat['stat_name'] == 'assist_count':
                char_assists = int(stat['value_forever'])
                break
    except (IndexError, KeyError, ValueError):
        char_assists = 0
        
    third_parties_filled = []
    for website in third_parties:
        url = website['url']
        if website['identifier'] == 'char_id':
            url = url % char_id
        elif website['identifier'] == 'char_name':
            url = url % char_name_truecase
        third_parties_filled.append(url)
    third_parties_filled = ' '.join(third_parties_filled)

    reply_text = REPLY_TEXT_TEMPLATE.format(
        char_name_truecase = char_name_truecase,
        game_version = game_version,
        char_creation = char_creation,
        char_login = char_login,
        char_playtime = char_playtime,
        char_logins = '{:,}'.format(char_login_count),
        login_plural = 's' if char_login_count != 1 else '',
        char_rank = char_rank,
        char_faction_en = char_faction['name']['en'],
        char_server = SERVERS[census_char['world_id']],
        char_outfit = char_outfit,
        char_score = '{:,}'.format(char_score),
        char_captures ='{:,}'.format(char_capture),
        char_defended = '{:,}'.format(char_defend),
        char_medals = '{:,}'.format(char_medal),
        char_ribbons = '{:,}'.format(char_ribbon),
        char_certs = '{:,}'.format(char_certs),
        char_kills = '{:,}'.format(char_kills),
        char_assists = '{:,}'.format(char_assists),
        char_deaths = '{:,}'.format(char_deaths),
        char_kdr = '{:,}'.format(char_kdr),
        third_party_websites = third_parties_filled
        )
    return reply_text

def handle_username_mention(mention, *trash):
    #print('handling username mention', mention.id)
    mention.mark_as_read()
        
    try:
        pauthor = mention.author.name
    except AttributeError:
        # Don't respond to deleted accounts
        return

    if pauthor.lower() == USERNAME.lower():
        # Don't respond to yourself
        return

    cur.execute('SELECT * FROM oldmentions WHERE ID=?', [mention.id])
    if cur.fetchone():
        # Item is already in database
        return
        
    cur.execute('INSERT INTO oldmentions VALUES(?)', [mention.id])
    sql.commit()

    reply_text = functionmap_comment(mention.body)

    if reply_text in [[], None]:
        return

    reply_text = MULTIPLE_COMMAND_JOINER.join(reply_text)
    reply_text += REPLY_TEXT_FOOTER
    #print('Generated reply text:', reply_text[:10])

    print('%s Replying to %s by %s' % (now_stamp(), mention.id, pauthor))
    try:
        mention.reply(reply_text)
    except praw.errors.PRAWException:
        return

def functionmap_line(text):
    #print('User said:', text)
    elements = shlex.split(text)
    #print('Broken into:', elements)
    results = []
    for element_index, element in enumerate(elements):
        if element.lower() not in COMMAND_IDENTIFIERS:
            continue

        arguments = elements[element_index:]
        assert arguments.pop(0).lower() in COMMAND_IDENTIFIERS

        # If the user has multiple command calls on one line
        # (Which is stupid but they might do it anyway)
        # Let's only process one at a time please.
        for argument_index, argument in enumerate(arguments):
            if argument.lower() in COMMAND_IDENTIFIERS:
                arguments = arguments[:argument_index]
                break

        #print('Found command:', arguments)
        if len(arguments) == 0:
            #print('Did nothing')
            continue

        command = arguments[0].lower()
        actual_function = command in FUNCTION_MAP
        function = FUNCTION_MAP.get(command, DEFAULT_FUNCTION)
        #print('Using function:', function.__name__)

        if actual_function:
            # Currently, the first argument is the name of the command
            # If we found an actual function, we can remove that
            # (because add() doesn't need "add" as the first arg)
            # If we're using the default, let's keep that first arg
            # because it might be important.
            arguments = arguments[1:]
        result = function(*arguments)
        #print('Output: %s' % result)
        results.append(result)
    return results

def functionmap_comment(comment):
    lines = comment.split('\n')
    results = []
    for line in lines:
        result = functionmap_line(line)
        if result is None:
            continue
        result = list(filter(None, result))
        if result is []:
            continue
        results += result

    # If the user inputs the same command multiple times
    # lets delete the duplicates
    # We flip the list before and after so that dupes are removed
    # from the back instead of front (because list.remove takes the
    # first match)
    results.reverse()
    for item in results[:]:
        if results.count(item) > 1:
            results.remove(item)
    results.reverse()

    return results

def ps2bot():
    print('checking unreads')
    unreads = list(r.get_unread(limit=None))
    mention_identifier = 'u/' + USERNAME.lower()
    for message in unreads:
        if mention_identifier in message.body.lower():
            handle_username_mention(message)
        else:
            message.mark_as_read()



# This must be defined down here because it can't come before
# the function definitions (or else NameError)
DEFAULT_FUNCTION = generate_report_pc
FUNCTION_MAP = {
    '!player': generate_report_pc,
    '!p': generate_report_pc,

    '!playerps4us': generate_report_ps4_us,
    '!ps4us': generate_report_ps4_us,
    '!p4us': generate_report_ps4_us,

    '!playerps4eu': generate_report_ps4_eu,
    '!ps4eu': generate_report_ps4_eu,
    '!p4eu': generate_report_ps4_eu,

    '!status': report_server_status,
    '!s': report_server_status
}
# lowercase it baby
FUNCTION_MAP = {c.lower():FUNCTION_MAP[c] for c in FUNCTION_MAP}



try:
    ps2bot()
except requests.exceptions.HTTPError:
    print(now_stamp(), 'A site/service is down. Probably Reddit.')
except Exception:
    traceback.print_exc()

#SAMPLES = [
#'u/ps2bot higby',
#'/u/ps2bot higby',
#'/u/PS2BOT higby',
#'/u/ps2bot !player higby',
#'/u/ps2bot !PLAYER higby',
#'/u/ps2bot higby /u/ps2bot !player higby',
#'/u/ps2bot',
#'/u/ps2bot !s !s !s !s',
#'/u/ps2bot !p4us bloodwolf\n/u/ps2bot !p bloodwolf\n/u/ps2bot !s',
#]
#for sample in SAMPLES:
#    result = functionmap_comment(sample)
#    #print(result)
#    if result in [[], None]:
#        continue
#    message = MULTIPLE_COMMAND_JOINER.join(result)
#    message += REPLY_TEXT_FOOTER
#    print(message)
