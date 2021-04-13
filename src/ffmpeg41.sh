#!/bin/bash

# Synology transcoder optimizator

VERSION="$@"

PIPE=`python /var/packages/CodecPack/target/bin/h265-transcoder-optimizator.py "$VERSION"`

/var/packages/CodecPack/target/bin/ffmpeg45 $PIPE

echo $@ >> /var/log/transcoding-optimizator.log