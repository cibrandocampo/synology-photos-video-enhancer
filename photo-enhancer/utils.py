import os
import glob
import shutil
import logging
import configparser

conf = configparser.ConfigParser()
conf.read('video_quality_enhancer.conf')

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def clean_path(directory_path):
    logging.debug(f'clean_path: {directory_path}')
    if os.path.isdir(directory_path):
        logging.debug('clean_path - Deleting content')
        shutil.rmtree(directory_path)
    os.makedirs(directory_path)


def get_video_paths():
    logging.debug('get_video_paths')
    paths = [conf.get('InputFolders', 'VIDEO_PATH')]
    for user in conf.get('InputFolders', 'USERS').split(','):
        paths.append(conf.get('InputFolders', 'USER_VIDEO_PATH').replace('_user_', user.strip()))

    return paths


def list_videos_in_folder(path):
    logging.debug(f'list_videos_in_folder. Listing videos located in: {path}')
    all_video_files = []
    for video_extension in conf.get('InputVideo', 'VIDEO_EXTENSIONS').split(','):
        all_video_files += glob.iglob(path + '**/*.' + video_extension.strip(), recursive=True)

    original_video_files = [x for x in all_video_files if not "@eaDir" in x and not "#recycle" in x]
    logging.debug(f'list_videos_in_folder. Videos found: {len(original_video_files)}')
    return original_video_files


def create_transcode_signal(original_file):
    logging.debug(f'create_transcode_signal. {original_file}')
    signal_file = f'{original_file}_completed_{conf.get("OutputVideo", "VIDEO_CODEC")}'
    open(signal_file, 'a').close()


def delete_files_by_name(folder_path, word):
    logging.debug(f'clean_completed_signal_file. {folder_path}')
    for filename in os.listdir(folder_path):
        if word in filename:
            os.remove(f'{folder_path}{filename}')
