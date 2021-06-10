#!/bin/bash

# Synology transcoder optimizator

VERSION="$@"

PIPE=`python /var/packages/CodecPack/target/bin/h265-transcoder-optimizator.py "$VERSION"`

echo $@ >> /var/log/transcoding-optimizator.log