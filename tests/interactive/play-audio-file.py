""" Play an audio file """

import sys
import argparse

from tunescope.audiometadata import AudioMetadata
from tunescope.audiodecoder import AudioDecoder
from tunescope.buffering import DecoderBuffer
from tunescope.looper import Looper
from tunescope.timestretcher import TimeStretcher
from tunescope.audiooutput import AudioOutput


def string_is_number(string):
    try:
        float(string)
    except ValueError:
        return False
    else:
        return True


parser = argparse.ArgumentParser(description=globals()['__doc__'])
parser.add_argument('filename', help="Path to audio file")
parser.add_argument('--speed', type=float)
parser.add_argument('--pitch', type=float)
args = parser.parse_args()

metadata = AudioMetadata(args.filename)
print(u"""
Title:    {m.title}
Artist:   {m.artist}
Album:    {m.album}
Duration: {m.duration:.2f} seconds
""".format(m=metadata))

decoder = AudioDecoder(args.filename)
buf = DecoderBuffer(decoder, 1024)
looper = Looper(buf)
stretcher = TimeStretcher(looper)
output = AudioOutput(stretcher)

if args.speed:
    stretcher.speed = args.speed

if args.pitch:
    stretcher.pitch = args.pitch

output.play()
playing = True  # FIXME: This should be an attribute of AudioOutput


def toggle_playing():
    global output, playing
    if playing:
        output.pause()
        playing = False
    else:
        output.play()
        playing = True


print("""
<Enter>         - pause/play
<number>        - seek to given time in seconds
s <speed>       - set speed ratio
p <pitch>       - set pitch change in semitones
l <start> <end> - loop between <start> and <end> in seconds
l               - stop looping
q               - quit
""")

while True:
    input_tokens = raw_input("Command: ").split()
    if len(input_tokens) == 0:
        toggle_playing()
        continue

    command, args = input_tokens[0], input_tokens[1:]
    try:
        if len(args) == 0:
            if command == 'q':
                break
            elif command == 'l':
                looper.deactivate()
            elif string_is_number(command):
                stretcher.seek(float(command))
            else:
                print('Unrecognized command')
        elif len(args) == 1:
            if command == 's':
                stretcher.speed = float(args[0])
            elif command == 'p':
                stretcher.pitch = float(args[0])
            else:
                print('Unrecognized command')
        elif len(args) == 2:
            if command == 'l':
                looper.activate(*map(float, args))
            else:
                print('Unrecognized command')
    except:
        print(sys.exc_info()[1])

output.close()
