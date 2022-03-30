import os
import logging
import configparser

from utils import clean_path, get_video_paths, list_videos_in_folder
from ffmpeg_commands import transcode_video_if_needed


M_VIDEO_NAME = 'SYNOPHOTO_FILM_M.mp4'
H_VIDEO_NAME = 'SYNOPHOTO_FILM_H.mp4'


conf = configparser.ConfigParser()
conf.read('video_quality_enhancer.conf')

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.ERROR,
    datefmt='%Y-%m-%d %H:%M:%S')


def checkVideosInFolder(path):
    for video_path in list_videos_in_folder(path):
        filename = video_path.split('/')[-1:][0]
        base_video_path = video_path.replace(filename, '') + '@eaDir/' + filename + '/'

        if os.path.exists(base_video_path + M_VIDEO_NAME):
            transcode_video_if_needed(video_path, base_video_path + M_VIDEO_NAME, filename)
        if os.path.exists(base_video_path + H_VIDEO_NAME):
            transcode_video_if_needed(video_path, base_video_path + H_VIDEO_NAME, filename)


logging.info("------------------------------------------------------")
logging.info("- Starting video quality enhancer for Synology Photo -")
logging.info("------------------------------------------------------")
logging.info("")

clean_path(conf.get('Docker', 'VOLUME_WORKSPACE'))

for video_path in get_video_paths():
    logging.info("====== Starting Synology improve video quality (" + str(video_path) + ") =====")
    checkVideosInFolder(video_path)

logging.info("")
logging.info("------------------------------------------------")
logging.info("- Analysis and video enhancement was COMPLETED -")
logging.info("------------------------------------------------")
