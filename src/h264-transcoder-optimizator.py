# Synology transcoder optimizator for H265

import os
import sys


def removeSpaces(pipe):
    path = pipe.split('-i ')[1].split(' -threads')[0]
    quote_path = '"' + path + '"'
    pipe = pipe.replace(path, quote_path)

    path = pipe.split('/volume1')[2]
    quote_path = '"' + path + '"'
    pipe = pipe.replace(path, quote_path)

    return pipe


pipe = sys.argv[1]
pipe = removeSpaces(pipe)
pipe = pipe.replace(" -r 15", "")
pipe = pipe.replace(" -level 30", "")
pipe = pipe.replace(" -preset superfast", "")
pipe = pipe.replace("libx264", "libx265")
pipe = pipe.replace("-vprofile baseline", "-vprofile high")
pipe = pipe.replace("2500k", "2000k")


os.system("/var/packages/CodecPack/target/bin/ffmpeg45 " + pipe)
