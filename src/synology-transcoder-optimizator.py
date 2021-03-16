# Synology transcoder optimizator

# Cofiguration values
# /var/packages/CodecPack/target/bin

import os
import sys

FFMPEG_PATH = "/var/packages/CodecPack/target/bin/ffmpeg42"
BITRATE = "3000k"
H264_PROFILE = "high"
H264_LEVEL = "4.2"

input_argv = sys.argv

if '-vframes' in input_argv:
    pipe = FFMPEG_PATH + " " + ' '.join(input_argv[1:])

else:
    input_path = input_argv[int(input_argv.index("-i")) + 1]
    video_codec = input_argv[int(input_argv.index("-vcodec")) + 1]
    v_format = input_argv[int(input_argv.index("-f")) + 1]
    resolution = input_argv[int(input_argv.index("-s")) + 1]
    aspect = input_argv[int(input_argv.index("-aspect")) + 1]
    output_path = input_argv[-1:][0]


    pipe = FFMPEG_PATH + ' -i ' + input_path + ' -y -c:v ' + video_codec + ' -profile:v ' + H264_PROFILE + ' -level:v ' + H264_LEVEL + ' -b:v ' + BITRATE + ' -bt ' + BITRATE
    pipe += ' -s ' + resolution  + ' -aspect ' + aspect + ' -threads 1 -pix_fmt yuv420p -c:a copy -f ' + v_format + ' ' + output_path


with open("transcoding.txt", "a") as myfile:
    myfile.write(pipe)
    myfile.write('\n')

os.popen(pipe)
sys.exit(0)