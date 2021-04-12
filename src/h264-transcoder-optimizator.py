# Synology transcoder optimizator for H264

import os
import sys

pipe = sys.argv[1]

pipe = pipe.replace(" -r 15","")
pipe = pipe.replace(" -preset superfast","")
pipe = pipe.replace("-vprofile baseline","-profile:v high")
pipe = pipe.replace("-level 30","-level:v 4.2")
pipe = pipe.replace("-threads 0","-threads 1")

print(pipe)
