# Project: Synology transcoding
# Component: Video quality enhancer for Synology Photo
# Author: Cibran docampo <hello@cibran.es>


import os
import json
import glob
import time
import shutil
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.ERROR,
    datefmt='%Y-%m-%d %H:%M:%S')


ROOTS_PATHS = ['/volume1/photo/', '/volume1/homes/cibran/Photos/', '/volume1/homes/ana/Photos/']
VIDEO_EXTENSIONS = ['mp4', 'MP4', 'mov', 'MOV', 'avi', 'AVI', '3gp']
M_VIDEO_NAME = 'SYNOPHOTO_FILM_M.mp4'
H_VIDEO_NAME = 'SYNOPHOTO_FILM_H.mp4'
FFPROBE_PATH = '/volume1/code/synology-transcoding/bin/ffprobe'
FFMPEG_PATH = '/volume1/code/synology-transcoding/bin/ffmpeg'
WORKSPACE = 'ffmpeg_workspace/'
VIDEO_BITRATE = '2000k'


def listVideosInFolder(path):
    logging.info("listVideosInFolder. Listing videos located in: " + str(path))
    all_video_files = []
    for video_extension in VIDEO_EXTENSIONS:
        all_video_files += glob.iglob(path + '**/*.' + video_extension, recursive=True)
    original_video_files = [x for x in all_video_files if not "@eaDir" in x and not "#recycle" in x]
    logging.info("listVideosInFolder. Videos found: " + str(len(original_video_files)))
    return original_video_files


def getVideoInfoJson(video_path):
    logging.debug("getVideoInfoJson: " + str(video_path))
    ffprobe_pipe = FFPROBE_PATH + ' -loglevel quiet "' + video_path + '"'
    ffprobe_pipe += ' -show_entries stream=width,height,r_frame_rate,profile,codec_name'
    ffprobe_pipe += ' -print_format json'
    raw_video_info = os.popen(ffprobe_pipe)
    time.sleep(1)
    return json.loads(raw_video_info.read())


def getVideoInfoDict(json_video_info, video_path='original'):
    logging.debug("getVideoInfoDict: " + str(json_video_info))
    video_info = {}

    for stream in json_video_info['streams']:
        if 'width' and 'height' in str(stream):
            video_info['width'] = stream['width']
            video_info['height'] = stream['height']
            video_info['codec_name'] = stream['codec_name']
            video_info['profile'] = stream['profile']
            raw_framerate = stream['r_frame_rate'].split('/')
            video_info['framerate'] = int(raw_framerate[0]) / int(raw_framerate[1])
            return video_info

    logging.warning("getVideoInfoDict. Invalid video details for: " + str(video_path))
    return False


def getVideoInfo(video_path):
    logging.debug("getVideoInfo: " + str(video_path))

    json_video_info = getVideoInfoJson(video_path)
    if 'streams' in str(json_video_info) and len(json_video_info['streams']):
        dict_video_info = getVideoInfoDict(json_video_info)
        return dict_video_info if len(dict_video_info) else False

    logging.warning("getVideoInfo. Invalid video details: " + str(json_video_info))
    video_info = {}
    video_info['width'] = video_info['height'] = video_info['profile'] = 0

    return video_info


def cleanWorkingDir(working_dir):
    logging.debug("cleanWorkingDir: " + str(working_dir))
    shutil.rmtree(working_dir)


def videoTranscode(video_path, small_video_path, filename, small_video_info):
    logging.debug("videoTranscode: " + str(video_path))
    pipe = FFMPEG_PATH + ' -loglevel quiet -y -i "' + video_path + '" -pix_fmt yuv420p '
    pipe += '-c:v libx265 -b:v ' + VIDEO_BITRATE + ' -threads 2'

    if small_video_info['width']:
        video_width = small_video_info['width']
        video_height = small_video_info['height']
    else:
        original_video_info = getVideoInfo(video_path)
        if original_video_info['width']:
            video_width = original_video_info['width']
            video_height = original_video_info['height']
        else:
            logging.warning("videoTranscode. Invalid resolution")
            video_width = video_height = 0

    if video_width >= video_height:
        pipe += ' -vf scale=-2:480 '
    else:
        pipe += ' -vf scale=480:-2 '

    working_dir = WORKSPACE + filename
    os.makedirs(working_dir, exist_ok=True)
    log_filename_path = working_dir + '/ffmpeg'

    pipe_2_pass_1 = pipe + ' -pass 1 -passlogfile ' + log_filename_path + ' -an -f null /dev/null'
    pipe_2_pass_2 = pipe + ' -pass 2 -passlogfile ' + log_filename_path + ' "' + small_video_path + '"'

    logging.debug("videoTranscode. Starting transcoding (1/2) for: " + str(filename))
    os.system(pipe_2_pass_1)
    logging.debug("videoTranscode. Finished transcoding (1/2) for: " + str(filename))
    time.sleep(5)
    logging.debug("videoTranscode. Starting transcoding (2/2) for: " + str(filename))
    if int(os.system(pipe_2_pass_2)):
        logging.warning("videoTranscode. Transcoding proccess failed for: " + str(filename))
        logging.debug("videoTranscode. Trying transcodification in a single pass for: " + str(filename))
        pipe_one_pass = pipe + ' "' + small_video_path + '"'
        if os.system(pipe_one_pass):
            logging.error("videoTranscode. Single-pass transcoding failed for: " + str(filename))
            cleanWorkingDir(working_dir)
            return False
        logging.debug("videoTranscode. Finished Single-pass transcoding for: " + str(filename))
        cleanWorkingDir(working_dir)
        return True

    logging.debug("videoTranscode. Finished transcoding (2/2) for: " + str(filename))
    cleanWorkingDir(working_dir)
    return True


def checkVideoParameters(video_path, small_video_path, filename):
    logging.debug("checkVideoParameters: " + str(video_path))
    small_video_info = getVideoInfo(small_video_path)

    if small_video_info['codec_name'] != 'hevc':
        logging.info("checkVideoParameters. Transcodification needed for: " + str(video_path))
        if videoTranscode(video_path, small_video_path, filename, small_video_info):
            logging.info("checkVideoParameters. Transcodification finished for: " + str(video_path))
        else:
            logging.warning("checkVideoParameters. Transcodification failed for: " + str(video_path))


def checkSmallVideo(video_path):
    logging.debug("checkSmallVideo: " + str(video_path))
    filename = video_path.split('/')[-1:][0]
    base_video_path = video_path.replace(filename, '') + '@eaDir/' + filename + '/'

    if os.path.exists(base_video_path + M_VIDEO_NAME):
        checkVideoParameters(video_path, base_video_path + M_VIDEO_NAME, filename)
    if os.path.exists(base_video_path + H_VIDEO_NAME):
        checkVideoParameters(video_path, base_video_path + H_VIDEO_NAME, filename)


def checkVideosInFolder(path):
    for video_path in listVideosInFolder(root_path):
        checkSmallVideo(video_path)


logging.info("------------------------------------------------------")
logging.info("- Starting video quality enhancer for Synology Photo -")
logging.info("------------------------------------------------------")
logging.info("")

cleanWorkingDir(WORKSPACE) if os.path.isdir(WORKSPACE) else None


for root_path in ROOTS_PATHS:
    logging.info("====== Starting Synology improve video quality (" + str(root_path) + ") =====")
    checkVideosInFolder(root_path)

logging.info("------------------------------------------------")
logging.info("- Analysis and video enhancement was COMPLETED -")
logging.info("------------------------------------------------")
