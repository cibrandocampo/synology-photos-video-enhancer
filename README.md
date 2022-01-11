# Video quality enhancer for Synology Photo 1.1.0-0224

Unfortunately, the quality of the transcoding process for medium quality videos (for mobile devices) is poor.
- Videos uploaded from the smartphone: H.264 baseline profile.
- Videos uploaded on the web / samba: Framerate of 15fps.

This tool aims to increase the quality of these videos without increasing the size or bitrate. To do this, a new transcoding is executed from the original file and the HEVC codec is used. Currently 90% of smartphones, laptops and tablets already support this codec.

## License

GNU GENERAL PUBLIC LICENSE


## Install

- Create a directory to host the code and last FFmpeg version. (for example /code/)
- Download and Unzip FFmpeg from: https://johnvansickle.com/ffmpeg/
- Copy the FFmpeg and FFprobe binary to the /bin code folder (or any directory)
- Copy the code from /photo-enhancer folder to the /code directory
- Manually execute the command, or schedule it in the DSM task manager.

```sh

mkdir /volume1/code/synology-transcoding/photo-enhancer/
mkdir /volume1/code/synology-transcoding/bin/

```
