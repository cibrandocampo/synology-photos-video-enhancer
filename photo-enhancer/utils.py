import os
import glob
import shutil
import logging
import configparser

conf = configparser.ConfigParser()
conf.read('video_quality_enhancer.conf')

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')


def clean_path(directory_path):
    logging.info('clean_path: ' + str(directory_path))
    if os.path.isdir(directory_path):
        logging.debug('clean_path - Deleting content')
        shutil.rmtree(directory_path)
    os.makedirs(directory_path)


def get_video_paths():
    logging.info("get_video_paths.")
    paths = [conf.get('InputFolders', 'VIDEO_PATH')]
    for user in conf.get('InputFolders', 'USERS').split(','):
        paths.append(conf.get('InputFolders', 'USER_VIDEO_PATH').replace('_user_', user.strip()))

    return paths


def list_videos_in_folder(path):
    logging.info("list_videos_in_folder. Listing videos located in: " + str(path))
    all_video_files = []
    for video_extension in conf.get('InputVideo', 'VIDEO_EXTENSIONS').split(','):
        all_video_files += glob.iglob(path + '**/*.' + video_extension.strip(), recursive=True)

    original_video_files = [x for x in all_video_files if not "@eaDir" in x and not "#recycle" in x]
    logging.info("list_videos_in_folder. Videos found: " + str(len(original_video_files)))
    return original_video_files
