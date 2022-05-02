import logging
import configparser

from utils import clean_path, get_video_paths, list_videos_in_folder
from ffmpeg_commands import check_if_videos_needs_transcoding, transcode_video

INTERMEDIATE_VIDEOS = ['SYNOPHOTO_FILM_M.mp4', 'SYNOPHOTO_FILM_H.mp4']
QA_CONTROL_FILENAME = 'optimizated_video'

conf = configparser.ConfigParser()
conf.read('video_quality_enhancer.conf')

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')


def checkVideosInFolder(path):
    logging.info(f'checkVideosInFolder. Analyzing videos inside the path: {path}')
    for video_path in list_videos_in_folder(path):
        filename = video_path.split('/')[-1:][0]
        base_video_path = video_path.replace(filename, '') + '@eaDir/' + filename + '/'

        for video2transcode in check_if_videos_needs_transcoding(base_video_path, INTERMEDIATE_VIDEOS):
            transcode_video(video_path, video2transcode)


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
