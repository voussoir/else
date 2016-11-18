import sys
try:
    sys.path.append('C:\\git\\else\\Bytestring')
    import bytestring
except ImportError:
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

def calc(seconds, kbps):
    final_kilobits = kbps * seconds
    final_bytes = final_kilobits * 128
    return final_bytes

if __name__ == '__main__':
    length = sys.argv[1] # HH:MM:SS
    kbps = int(sys.argv[2])
    seconds = hms_s(length)
    print(bytestring.bytestring(calc(seconds, kbps)))