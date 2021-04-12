# Synology transcoder optimizator

## Small optimizations to improve the transcoding quality 

By default, the NAS transcodes videos at 15fps, with a resolution of 720p and a bitrate of 2.5Mbps. Which makes the video look bumpy.

This small plugin is developed to optimize it and be able to configure it.

## License

GNU GENERAL PUBLIC LICENSE


## Install

Download and Unzip Ffmpeg from: https://johnvansickle.com/ffmpeg/

```sh
cd /var/packages/CodecPack/target/bin 
sudo mv ffmpeg41 ffmpeg42

sudo ln -s /path/to/ffmpeg41.sh ffmpeg41
sudo ln -s /path/to/ffmpeg ffmpeg45
sudo ln -s /path/to/h265-transcoder-optimizator.py h265-transcoder-optimizator.py
```