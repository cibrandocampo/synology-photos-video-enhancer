# Synology transcoder optimizator for DSM 7.0

## Small optimizations to improve the transcoding quality 

For this version, my NAS (DS720+) just transcode for medium quality in H.264 720p@15fps, and which makes the video look bumpy.

This small plugin is developed to optimize it and be able to configure the video transcodification.

## License

GNU GENERAL PUBLIC LICENSE


## Install

1- Download and Unzip FFmpeg from: https://johnvansickle.com/ffmpeg/
2- Copy the binary FFmpeg file in your favourite path (in my case /volumes1/code/)
3- Execute the following commands. 

```sh
cd /var/packages/CodecPack/target/bin 
sudo mv ffmpeg41 ffmpeg41_original

sudo ln -s /path/to/ffmpeg41.sh ffmpeg41
sudo ln -s /path/to/ffmpeg ffmpeg45
sudo ln -s /path/to/h265-transcoder-optimizator.py h265-transcoder-optimizator.py
```