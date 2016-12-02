'''
Usage:

Shift all subtitles 10 seconds forward:
> subtitle_shift file.srt +10

Shift all subtitles 10 seconds backward:
> subtitle_shift file.srt -10

This will produce "file_correct.srt" with the new timestamps.
'''

import os
import sys
filename = sys.argv[1]
offset = float(sys.argv[2])
f = open(filename, 'r')

lines = [l.strip() for l in f.readlines()]
for (lineindex, line) in enumerate(lines):
    changed = False

    if '-->' not in line:
        continue

    words = line.split(' ')
    for (wordindex, word) in enumerate(words):
        if not (':' in word and ',' in word):
            continue

        if not word.replace(':', '').replace(',', '').isdigit():
            continue

        # 1.) 01:23:45,678 --> 02:34:56,789 | our input
        # 2.) 01:23:45:678 --> 02:34:56:789 | comma to colon
        # 3.) 5025.678 --> 9296.789         | split by colon and sum
        # 4.) 5035.678 --> 9306.789         | add offset
        # 5.) 01:23:55.678 --> 02:35:06.789 | reformat
        # 6.) 01:23:55,678 --> 02:35:06,789 | period to comma
        word = word.replace(',', ':')
        (hours, minutes, seconds, mili) = [int(x) for x in word.split(':')]
        seconds = (3600 * hours) + (60 * minutes) + (seconds) + (mili / 1000)

        seconds += offset
        (hours, seconds) = divmod(seconds, 3600)
        (minutes, seconds) = divmod(seconds, 60)

        if hours < 0:
            raise Exception('Negative time')

        word = '%02d:%02d:%06.3f' % (hours, minutes, seconds)
        word = word.replace('.', ',')
        changed = True
        words[wordindex] = word

    if changed:
        line = ' '.join(words)
        print(line)
        lines[lineindex] = line

lines = '\n'.join(lines)
(name, extension) = os.path.splitext(filename)
newname = name + '_correct' + extension
x = open(newname, 'w')
x.write(lines)
x.close()