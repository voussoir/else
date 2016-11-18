import converter
import os
import re
import subprocess
import sys
import time

def main(filename):
    assert os.path.isfile(filename)
    ffmpeg = converter.Converter()
    probe = ffmpeg.probe(filename)
    new_name = filename
    if '_x_' in filename:
        dimensions = '%dx%d' % (probe.video.video_width, probe.video.video_height)
        new_name = new_name.replace('_x_', dimensions)
    if '___' in filename:
        video_codec = probe.video.codec

        audios = [stream for stream in probe.streams if stream.type == 'audio']
        audio = max(audios, key=lambda x: x.bitrate)

        audio_codec = probe.audio.codec

        if any(not x for x in [video_codec, probe.video.bitrate, audio_codec, probe.audio.bitrate]):
            print('Could not identify media info')
        else:
            video_bitrate = probe.video.bitrate // 1000
            audio_bitrate = probe.audio.bitrate // 1000
            video = '%s-%d' % (video_codec, video_bitrate)
            audio = '%s-%d' % (audio_codec, audio_bitrate)

            video = video.upper()
            audio = audio.upper()
            video = video.replace('H264', 'h264')
            video = video.replace('HEVC', 'h265')
            info = '{v}, {a}'.format(v=video, a=audio)
            new_name = new_name.replace('___', info)
    print(new_name)
    if input('Okay?').lower() in ['y', 'yes']:
        os.rename(filename, new_name)

if __name__ == '__main__':
    main(sys.argv[1])