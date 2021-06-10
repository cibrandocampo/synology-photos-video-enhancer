# Synology transcoder optimizator for H265

import os
import sys

FFMPEG_PATH = "/var/packages/CodecPack/target/bin/ffmpeg45"


def addPathQuotes(pipe):
    path = pipe.split('-i ')[1].split(' -threads')[0]
    quote_path = '"' + path + '"'
    pipe = pipe.replace(path, quote_path)

    path = pipe.split('/volume1')[2]
    quote_path = '"' + path + '"'
    pipe = pipe.replace(path, quote_path)

    return pipe


def optimizePramas(pipe):
    pipe = pipe.replace(" -r 15", "")
    pipe = pipe.replace(" -level 30", "")
    pipe = pipe.replace(" -preset superfast", "")
    pipe = pipe.replace("libx264", "libx265")
    pipe = pipe.replace("-vprofile baseline", "-x265-params crf=23:pools=1")
    pipe = pipe.replace("2500k", "2000k")
    return pipe


pipe = sys.argv[1]
pipe = addPathQuotes(pipe)
pipe = optimizePramas(pipe)

os.system(FFMPEG_PATH + " " + pipe)

print("OK")
