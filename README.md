# Video quality enhancer for DSM v7.1 and Synology Photo 1.3.0-0317

Unfortunately, the quality of the transcoding process for medium quality videos (for mobile devices) is poor.
- Videos uploaded from the smartphone: H.264 baseline profile.
- Videos uploaded on the web / samba: Framerate of 15fps.

This tool aims to increase the quality lanching a optimized transcoding process base in the original video. The output can be H.264 HighProfile (best compression/quality rate) or the new H.265/HEVC codec.

## Install

- Confirm docker package is installed on DSM. (https://www.synology.com/en-global/dsm/packages/Docker)
- Create a directory to host the code (Example: /volume1/code/synology-transcoding/)
- Copy the code from /photo-enhancer folder to the previous folder (Example: /volume1/code/synology-transcoding/)
- Manually execute the command, or schedule it in the DSM task manager. (https://kb.synology.com/en-uk/DSM/help/DSM/AdminCenter/system_taskscheduler?version=7)


## Help

Send me an email (hello@cibran.es) if you need extra help.

## License

GNU GENERAL PUBLIC LICENSE