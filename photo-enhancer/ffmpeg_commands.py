import os
import json
import time
import logging
import configparser

from utils import clean_path

conf = configparser.ConfigParser()
conf.read('video_quality_enhancer.conf')

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.ERROR,
    datefmt='%Y-%m-%d %H:%M:%S')


def initialize_ffprobe_command():

    cmd_ini = conf.get('Docker', 'INTRO_CMD') + ' '
    cmd_ini += '-v ' + conf.get('Docker', 'VOLUME_VIDEOS_PATH') + ':' + conf.get('Docker', 'VOLUME_VIDEOS_PATH') + ' '
    return cmd_ini + ' --entrypoint ffprobe ' + conf.get('Docker', 'IMAGE')


def initialize_ffmpeg_command():

    cmd_ini = conf.get('Docker', 'INTRO_CMD') + ' ' + conf.get('Docker', 'DEVICE_CMD') + ' '
    cmd_ini += '-v ' + conf.get('Docker', 'VOLUME_VIDEOS_PATH') + ':' + conf.get('Docker', 'VOLUME_VIDEOS_PATH') + ' '
    cmd_ini += '-v ' + conf.get('Docker', 'VOLUME_WORKSPACE') + ':' + conf.get('Docker', 'VOLUME_WORKSPACE') + ' '

    ffmpeg_cmd = cmd_ini + ' ' + conf.get('Docker', 'IMAGE')

    if bool(conf.get('FFmpeg', 'HW_TRANSCODING')):
        ffmpeg_cmd += ' ' + conf.get('FFmpeg', 'VAAPI_INTRO')

    return ffmpeg_cmd


def get_json_video_info(video_path):
    logging.info("get_json_video_info: " + str(video_path))
    ffprobe_pipe = initialize_ffprobe_command() + ' -loglevel quiet "' + video_path + '"'
    ffprobe_pipe += ' -show_entries stream=width,height,r_frame_rate,profile,codec_name'
    ffprobe_pipe += ' -print_format json'
    raw_video_info = os.popen(ffprobe_pipe)
    time.sleep(1)
    return json.loads(raw_video_info.read())


def get_dict_video_info(json_video_info, video_path='original'):
    logging.info("get_dict_video_info: " + str(json_video_info))
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

    logging.warning("get_dict_video_info. Invalid video details for: " + str(video_path))
    return False


def get_video_info(video_path):
    logging.info("get_video_info: " + str(video_path))

    json_video_info = get_json_video_info(video_path)
    if 'streams' in str(json_video_info) and len(json_video_info['streams']):
        dict_video_info = get_dict_video_info(json_video_info)
        return dict_video_info if len(dict_video_info) else False

    logging.warning("get_video_info. Invalid video details: " + str(json_video_info))
    video_info = {}
    video_info['width'] = video_info['height'] = video_info['profile'] = 0

    return video_info


def transcode_video_if_needed(video_path, small_video_path, filename):
    logging.info("checkVideoNeedsTranscode: " + str(video_path))
    small_video_info = get_video_info(small_video_path)

    if not 'codec_name' in small_video_info or small_video_info['codec_name'] != 'hevc':
        logging.info("transcodeVideoIfNeeded. Transcodification needed for: " + str(video_path))
        if video_transcode(video_path, small_video_path, filename, small_video_info):
            logging.info("transcodeVideoIfNeeded. Transcodification finished for: " + str(video_path))
        else:
            logging.warning("transcodeVideoIfNeeded. Transcodification failed for: " + str(video_path))


def video_transcode(video_path, small_video_path, filename, small_video_info):
    logging.info("video_transcode: " + str(video_path))

    pipe = initialize_ffmpeg_command() + ' -loglevel quiet -y -i "' + video_path + '" '

    if small_video_info['width']:
        video_width = small_video_info['width']
        video_height = small_video_info['height']
    else:
        original_video_info = get_video_info(video_path)
        if original_video_info['width']:
            video_width = original_video_info['width']
            video_height = original_video_info['height']
        else:
            logging.warning("video_transcode. Invalid resolution")
            video_width = video_height = 0

    if video_width >= video_height:
        pipe += "-vf 'format=nv12,hwupload,scale_vaapi=w=-2:h=" + conf.get('OutputVideo', 'VIDEO_MAX_H_W') + "' "
    else:
        pipe += "-vf 'format=nv12,hwupload,scale_vaapi=w=" + conf.get('OutputVideo', 'VIDEO_MAX_H_W') + ":h=-2' "

    if bool(conf.get('FFmpeg', 'HW_TRANSCODING')):
        pipe += '-c:v ' + conf.get('OutputVideo', 'VIDEO_CODEC') + '_vaapi '
    else:
        pipe += '-c:v ' + conf.get('OutputVideo', 'VIDEO_CODEC') + ' '

    pipe += conf.get('OutputVideo', 'VIDEO_PROFILE') + ' '
    pipe += '-b:v ' + conf.get('OutputVideo', 'VIDEO_BITRATE') + ' '
    pipe += '-maxrate ' + conf.get('OutputVideo', 'VIDEO_BITRATE') + ' '
    pipe += '-threads ' + conf.get('FFmpeg', 'EXECUTION_THREADS') + ' '

    working_dir = conf.get('Docker', 'VOLUME_WORKSPACE') + filename
    os.makedirs(working_dir, exist_ok=True)
    log_filename_path = working_dir + '/ffmpeg'

    pipe_2_pass_1 = pipe + ' -pass 1 -passlogfile "' + log_filename_path + '" -an -f null /dev/null'

    pipe += '-c:a ' + conf.get('OutputVideo', 'AUDIO_CODEC') + ' '
    pipe += '-b:a ' + conf.get('OutputVideo', 'AUDIO_BITRATE') + ' '

    pipe_2_pass_2 = pipe + ' -pass 2 -passlogfile "' + log_filename_path + '" '
    pipe_2_pass_2 += conf.get('FFmpeg', 'CONTAINER_FLAGS') + ' "' + small_video_path + '"'

    logging.info("video_transcode. Starting transcoding (1/2) for: " + str(filename))
    logging.debug("video_transcode. " + str(pipe_2_pass_1))
    os.system(pipe_2_pass_1)
    logging.info("video_transcode. Finished transcoding (1/2) for: " + str(filename))
    time.sleep(5)
    logging.info("video_transcode. Starting transcoding (2/2) for: " + str(filename))
    logging.debug("video_transcode. " + str(pipe_2_pass_2))
    if int(os.system(pipe_2_pass_2)):
        logging.warning("video_transcode. Transcoding proccess failed for: " + str(filename))
        logging.info("video_transcode. Trying transcodification in a single pass for: " + str(filename))
        pipe_one_pass = pipe + ' -crf 16 "' + small_video_path + '"'
        logging.debug("video_transcode. " + str(pipe_one_pass))
        if os.system(pipe_one_pass):
            logging.error("video_transcode. Single-pass transcoding failed for: " + str(filename))
            clean_path(working_dir)
            return False
        logging.info("video_transcode. Finished Single-pass transcoding for: " + str(filename))
        clean_path(working_dir)
        return True

    logging.info("video_transcode. Finished transcoding (2/2) for: " + str(filename))
    clean_path(working_dir)
    return True
