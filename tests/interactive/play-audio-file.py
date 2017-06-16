""" Play an audio file """

import argparse

from tunescope.audiodecoder import AudioDecoder
from tunescope.buffering import DecoderBuffer
from tunescope.audiooutput import AudioOutput

parser = argparse.ArgumentParser(description=globals()['__doc__'])
parser.add_argument('filename', help="Path to audio file")
args = parser.parse_args()

decoder = AudioDecoder(args.filename)
buf = DecoderBuffer(decoder, 1024)
output = AudioOutput(buf)
output.play()

command = raw_input("Press enter to quit")

output.close()
