# Synology transcoder optimizator for H265

import os
import sys

pipe = sys.argv[1]

pipe = pipe.replace(" -r 15","")
pipe = pipe.replace(" -preset superfast","")
pipe = pipe.replace("libx264","libx265")
pipe = pipe.replace("-vprofile baseline","-x265-params crf=23:pools=1")
pipe = pipe.replace("3000k","2000k")
pipe = pipe.replace(" -threads 0","")

print(pipe)
