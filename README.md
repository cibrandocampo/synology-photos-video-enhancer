# Video quality enhancer Synology Photo

Unfortunately, the quality of the transcoding process for medium quality videos (for mobile devices) is poor.
- Videos uploaded from the smartphone: H.264 baseline profile.
- Videos uploaded on the web / samba: Framerate of 15fps.

This tool aims to increase the quality lanching a optimized transcoding process base in the original video. The output can be H.264 HighProfile (best compression/quality rate) or the new H.265/HEVC codec.


## Prerequisites

- A Synology NAS with DSM > 7.0 installed and properly configured.
- Synology Container Manager application > 20.10.23 installed and running.
- Synology Photos application > 1.5.0 installed and running.

## Configuration/Customization

IMPORTANT! Modify the configuration file `video_quality_enhancer.conf` adding the necessary configuration. Mainly the name of the users, the address of the common folder (if it exists), and the path where the photos and videos of each of the users are stored. You can do it in the 4th installation step.


| InputFolders   | Explanation | Default value   | Example |
|----------------|--------------------|----------------|--------------------|
| USERS          | Users configured in DSM |user1, user2, user3| jhon, marc, tonny|
| VIDEO_PATH     | Common folder for photos & videos | /volume1/photo/  ||
| USER_VIDEO_PATH| Generic Path where private users fotos are stored |/volume1/homes/_user_/Photos/|



## Install

1. Using the File Station APP in your Synology, create a directory to host the code (Example: /volume1/code/synology-transcoding/)

2. Download the source code from the last release version. https://github.com/cibrandocampo/synology-transcoding/releases

3. Unzip the folder

4. Configure the `video_quality_enhancer.conf` adding the necessary configuration. More info at Configuration/Customization block.

4. Copy the uncompressed `photo-enhancer` folder to the NAS folder recently created.

5. Schedule the project execution to run once or multiple times a day. For this use the DSM task manager. Go to `Control Panel` > `Task Scheduler`, click `Create`, and select `Scheduled Task`

    - General
	    - Task: Something like `video quality enhancer`
	    - User: root

    - Schedule (When you whant to execute the process)
    - Task Settings
	    - To receive run details of the task, tick Send run details by email.
	    - To get notified only when abnormalities occur, tick Send run details only when the script terminates abnormally.
	    - User-defined script, add:

            ```sh
            cd /volume1/code/synology-transcoding/photo-enhancer/ && python video_quality_enhancer.py
            ```
            NOTE: Use the path configured in the step 1.

Synology manual: https://kb.synology.com/en-uk/DSM/help/DSM/AdminCenter/system_taskscheduler?version=7


## Issues, contributions and help

If you encounter any problems or have any suggestions, feel free to contact me via (hello@cibran.es). You can also contribute to improving this project by submitting pull requests.

## License

This project is licensed under the [MIT License](LICENSE).