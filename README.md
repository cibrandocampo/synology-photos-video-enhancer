# Video quality enhancer for Synology Photo 1.0.0-0182

Unfortunately, the quality of the transcoding process for medium quality videos (for mobile devices) is poor.
- Videos uploaded from the smartphone: H.264 baseline profile.
- Videos uploaded on the web / samba: Framerate of 15fps.

This tool aims to increase the quality of these videos without increasing the size or bitrate. To do this, a new transcoding is executed from the original file and the HEVC codec is used. Currently 90% of smartphones, laptops and tablets already support this codec.

## License

GNU GENERAL PUBLIC LICENSE


## Install

1- Create a directory to host the code and last FFmpeg version. (for example /code/)
2- Download and Unzip FFmpeg from: https://johnvansickle.com/ffmpeg/
4- Copy the FFmpeg and FFrpobe binary to the /bin code folder (or any directory deemed suitable)
5- Copy the code from /photo-enhancer folder to the /code directory
6- Manually execute the command, or schedule it in the DSM task manager.

```sh

mkdir /volume1/code/synology-transcoding/photo-enhancer/
mkdir /volume1/code/synology-transcoding/bin/

```