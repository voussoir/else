import sys

# pip install
# https://raw.githubusercontent.com/voussoir/else/master/_voussoirkit/voussoirkit.zip
from vousoirkit import bytestring

def hms_s(hms):
    hms = hms.split(':')
    seconds = 0
    if len(hms) == 3:
        seconds += int(hms[0])*3600
        hms.pop(0)
    if len(hms) == 2:
        seconds += int(hms[0])*60
        hms.pop(0)
    if len(hms) == 1:
        seconds += int(hms[0])
    return seconds

def calc(seconds, goal_bytes):
    goal_kibs = goal_bytes / 1024
    goal_kilobits = goal_kibs * 8
    goal_kbps = goal_kilobits / seconds
    goal_kbps = round(goal_kbps, 2)
    return goal_kbps

if __name__ == '__main__':
    length = sys.argv[1] # HH:MM:SS
    goal_bytes = bytestring.parsebytes(sys.argv[2])
    seconds = hms_s(length)
    print(calc(seconds, goal_bytes), 'kbps')