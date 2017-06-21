""" Play an audio file """

import argparse

from tunescope.audiodecoder import AudioDecoder
from tunescope.buffering import DecoderBuffer
from tunescope.timestretcher import TimeStretcher
from tunescope.audiooutput import AudioOutput

parser = argparse.ArgumentParser(description=globals()['__doc__'])
parser.add_argument('filename', help="Path to audio file")
parser.add_argument('--speed', type=float)
parser.add_argument('--pitch', type=float)
args = parser.parse_args()

decoder = AudioDecoder(args.filename)
buf = DecoderBuffer(decoder, 1024)
stretcher = TimeStretcher(buf)
output = AudioOutput(stretcher)

if args.speed:
    stretcher.speed = args.speed

if args.pitch:
    stretcher.pitch = args.pitch

output.play()
playing = True  # FIXME: This should be an attribute of AudioOutput

print("""
<Enter>    - pause/play
s <speed>  - set speed ratio
p <pitch>  - set pitch ratio
q          - quit
""")

while True:
    input_string = raw_input("Command: ")
    if not input_string:
        if playing:
            output.pause()
            playing = False
        else:
            output.play()
            playing = True
    elif input_string.startswith('q'):
        break
    else:
        try:
            command, arg = input_string.split()
            arg = float(arg)
            if command == 's':
                stretcher.speed = arg
            elif command == 'p':
                stretcher.pitch = arg
            else:
                raise ValueError()
        except ValueError:
            print("Unrecognized command")

output.close()
