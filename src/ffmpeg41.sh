#!/bin/bash

# Synology transcoder optimizator

VERSION="$@"

PIPE=`python -c 'import sys;print(sys.argv[1].replace(" -r 15","").replace(" -preset superfast","").replace("-vprofile baseline","-profile:v high").replace("-level 30","-level:v 4.2").replace("-threads 0","-threads 1"))' "$VERSION"`

/var/packages/CodecPack/target/bin/ffmpeg42 $PIPE

echo $@ >> /var/log/transcoding-optimizator.log


cd /var/packages/CodecPack/target/bin 
sudo mv ffmpeg41 ffmpeg42

sudo ln -s /path/to/ffmpeg41.sh ffmpeg41