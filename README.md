# Video quality enhancer for DSM v7.1 and Synology Photo 1.3.0-0317

Unfortunately, the quality of the transcoding process for medium quality videos (for mobile devices) is poor.
- Videos uploaded from the smartphone: H.264 baseline profile.
- Videos uploaded on the web / samba: Framerate of 15fps.

This tool aims to increase the quality of these videos without increasing the size or bitrate. To do this, a new transcoding is executed from the original file and the HEVC codec is used. Currently 90% of smartphones, laptops and tablets already support this codec.

## License

GNU GENERAL PUBLIC LICENSE


## Install

- Create a directory to host the code and last FFmpeg version. (for example /code/)
- Copy the code from /photo-enhancer folder to the /code directory
- Manually execute the command, or schedule it in the DSM task manager.

```sh

mkdir /volume1/code/synology-transcoding/photo-enhancer/

```
