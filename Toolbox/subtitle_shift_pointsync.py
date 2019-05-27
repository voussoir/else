import argparse
import sys

inf = float('inf')

class Subtitles:
    def __init__(self, lines):
        self.lines = sorted(lines)

    @classmethod
    def from_text(cls, text):
        text = text.strip()
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        lines = text.split('\n\n')
        lines = [SubtitleLine.from_text(line) for line in lines]
        return cls(lines)

    def __getitem__(self, index):
        return self.lines[index]

    def __len__(self):
        return len(self.lines)

    def __repr__(self):
        return f'Subtitles with {len(self.lines)} lines.'

    def as_srt(self):
        lines = sorted(self.lines)
        lines = [f'{index+1}\n{line.as_srt()}' for (index, line) in enumerate(lines)]
        return '\n\n'.join(lines)

class SubtitleLine:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text

    @classmethod
    def from_text(cls, text):
        (index, timestamps, text) = text.split('\n', 2)
        timestamps = timestamps.replace(',', '.')
        (start, end) = timestamps.split('-->')
        start = hms_to_seconds(start)
        end = hms_to_seconds(end)
        return cls(start, end, text)

    def __lt__(self, other):
        return (self.start, self.end) < (other.start, other.end)

    def __repr__(self):
        return repr(self.as_srt())

    def as_srt(self):
        start = seconds_to_hms(self.start, force_hours=True, force_milliseconds=True)
        end = seconds_to_hms(self.end, force_hours=True, force_milliseconds=True)
        srt = f'{start} --> {end}'.replace('.', ',')
        srt += '\n' + self.text
        return srt


class Point:
    def __init__(self, x, y=None):
        self.x = x
        self.y = y

    def __lt__(self, other):
        return (self.x, self.y) < (other.x, other.y)

    def __repr__(self):
        return f'Point({self.x}, {self.y})'


def hms_to_seconds(hms):
    '''
    Convert hh:mm:ss string to an integer seconds.
    '''
    hms = hms.split(':')
    seconds = 0
    if len(hms) == 3:
        seconds += int(hms.pop(0)) * 3600
    if len(hms) == 2:
        seconds += int(hms.pop(0)) * 60
    if len(hms) == 1:
        seconds += float(hms.pop(0).replace(',', '.'))
    return seconds

def seconds_to_hms(seconds, force_hours=False, force_milliseconds=False):
    milliseconds = seconds % 1
    if milliseconds >= 0.999:
        milliseconds = 0
        seconds += 1
    seconds = int(seconds)
    (minutes, seconds) = divmod(seconds, 60)
    (hours, minutes) = divmod(minutes, 60)

    parts = []
    if hours or force_hours:
        parts.append(hours)

    if minutes or force_hours:
        parts.append(minutes)

    parts.append(seconds)

    hms = ':'.join(f'{part:02d}' for part in parts)
    if milliseconds or force_milliseconds:
        milliseconds = f'.{milliseconds:.03f}'.split('.')[-1]
        hms += '.' + milliseconds
    return hms

def linear(slope, intercept):
    '''
    Given slope m and intercept b, return a function f such that f(x) = mx + b.
    '''
    def f(x):
        y = (slope * x) + intercept
        print(x, y, f'{y:.03f}', seconds_to_hms(y))
        return y
    return f

def slope_intercept(p1, p2):
    '''
    Given two Points, return the slope and intercept describing a line
    between them.
    '''
    slope = (p2.y - p1.y) / (p2.x - p1.x)
    intercept = p1.y - (slope * p1.x)
    return (slope, intercept)

def pointsync(input_filename, output_filename, input_landmarks):
    landmarks = []
    used_olds = set()
    for landmark in input_landmarks:
        (old, new) = landmark.split('=')
        (old, new) = (hms_to_seconds(old), hms_to_seconds(new))
        if old < 0 or new < 0:
            raise ValueError('No negative numbers!')
        if old in used_olds:
            raise ValueError(f'Cant use the same old value {seconds_to_hms(old, force_hours=True)} twice.')
        used_olds.add(old)
        landmarks.append(Point(old, new))
    landmarks.sort()
    if landmarks[0].x != 0:
        landmarks.insert(0, Point(0, 0))

    # print(landmarks)
    if len(landmarks) < 2:
        raise ValueError('Not enough landmarks')

    landmark_functions = []
    for (land1, land2) in zip(landmarks, landmarks[1:]):
        (slope, intercept) = slope_intercept(land1, land2)
        if slope < 0:
            raise ValueError(f'Negative slope between {land1} and {land2}.')
        f = linear(slope, intercept)
        landmark_functions.append((land1.x, f))
    landmark_functions.append((inf, None))
    old_srt = Subtitles.from_text(open(input_filename, encoding='utf-8').read())

    pointer = 0
    new_srt = Subtitles([])
    for old_line in old_srt:
        if old_line.start >= landmark_functions[pointer+1][0]:
            pointer += 1
        new_start = landmark_functions[pointer][1](old_line.start)

        if old_line.end >= landmark_functions[pointer+1][0]:
            pointer += 1
        new_end = landmark_functions[pointer][1](old_line.end)
        new_line = SubtitleLine(new_start, new_end, old_line.text)
        new_srt.lines.append(new_line)
    new_file = open(output_filename, 'w', encoding='utf-8')
    new_file.write(new_srt.as_srt())

def pointsync_argparse(args):
    input_filename = args.input_filename
    output_filename = args.output_filename
    if '.srt' not in output_filename:
        raise ValueError('Output filename', output_filename)

    input_landmarks = args.landmarks
    return pointsync(input_filename, output_filename, input_landmarks)

def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('input_filename')
    parser.add_argument('output_filename')
    parser.add_argument('landmarks', nargs='*', default=None)
    parser.set_defaults(func=pointsync_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
