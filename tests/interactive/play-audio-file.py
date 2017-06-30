""" Play an audio file """

import argparse

from tunescope.audiometadata import AudioMetadata
from tunescope.audiodecoder import AudioDecoder
from tunescope.buffering import DecoderBuffer
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
<number>   - seek to given time in seconds
s <speed>  - set speed ratio
p <pitch>  - set pitch change in semitones
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
    elif string_is_number(input_string):
        decoder.seek(float(input_string))
        if stretcher.is_eos():
            stretcher.reset()
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
