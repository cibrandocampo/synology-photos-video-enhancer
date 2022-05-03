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


def add_quality_control_file(video_quality_path):
    open(video_quality_path, 'a').close()


def check_if_videos_needs_transcoding(base_video_path, videos_filename):
    videos_that_need_transcoding = []
    for video_filename in videos_filename:
        video_file_path = f'{base_video_path}{video_filename}'

        logging.debug(f'check_if_videos_needs_transcoding. Analyzing: {video_file_path}')
        if os.path.exists(video_file_path) and not os.path.isfile(f'{video_file_path}_completed'):
            video_info = get_video_info(video_file_path)
            if not 'codec_name' in video_info or video_info['codec_name'] != 'hevc':
                logging.info(f'check_if_videos_needs_transcoding. {video_file_path} needs to be transcoded')
                videos_that_need_transcoding.append(video_file_path)
            else:
                logging.info(f'check_if_videos_needs_transcoding. {video_file_path} is already transcoded')
                add_quality_control_file(f'{video_file_path}_completed')
        else:
            logging.debug(f'check_if_videos_needs_transcoding. Video: {video_file_path} do not exists')

    return videos_that_need_transcoding


def transcode_video(original_video_path, optimized_video_path):
    logging.info(f'video_transcode. From {original_video_path} to {optimized_video_path}')

    pipe = initialize_ffmpeg_command() + ' -loglevel quiet -y -i "' + original_video_path + '" '

    original_video_info = get_video_info(original_video_path)
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

    working_dir = conf.get('Docker', 'VOLUME_WORKSPACE') + 'ffmpeg_workspace'
    os.makedirs(working_dir, exist_ok=True)
    log_filename_path = working_dir + '/ffmpeg'

    pipe_2_pass_1 = pipe + ' -pass 1 -passlogfile "' + log_filename_path + '" -an -f null /dev/null'

    pipe += '-c:a ' + conf.get('OutputVideo', 'AUDIO_CODEC') + ' '
    pipe += '-b:a ' + conf.get('OutputVideo', 'AUDIO_BITRATE') + ' '
    pipe += '-ac ' + conf.get('OutputVideo', 'AUDIO_CHANNELS') + ' '

    pipe_2_pass_2 = pipe + ' -pass 2 -passlogfile "' + log_filename_path + '" '
    pipe_2_pass_2 += conf.get('FFmpeg', 'CONTAINER_FLAGS') + ' "' + optimized_video_path + '"'

    logging.info(f'video_transcode. Starting transcoding (1/2) for: {original_video_path} to {optimized_video_path}')
    os.system(pipe_2_pass_1)
    logging.info(f'video_transcode. Finished transcoding (1/2) for: {original_video_path} to {optimized_video_path}')

    time.sleep(5)

    logging.info(f'video_transcode. Starting transcoding (2/2) for: {original_video_path} to {optimized_video_path}')
    if int(os.system(pipe_2_pass_2)):
        logging.warning(f'video_transcode. Transcoding proccess for: {original_video_path} to {optimized_video_path}')

        logging.info(f'video_transcode. Starting Single-pass for: {original_video_path} to {optimized_video_path}')
        pipe_one_pass = pipe + ' -crf 16 "' + optimized_video_path + '"'

        if os.system(pipe_one_pass):
            logging.warning(f'video_transcode. Failed Single-pass for: {original_video_path} to {optimized_video_path}')
            clean_path(working_dir)
            return False

        logging.info(f'video_transcode. Finished Single-pass for: {original_video_path} to {optimized_video_path}')
        clean_path(working_dir)
        add_quality_control_file(f'{optimized_video_path}_completed')
        return True

    logging.info(f'video_transcode. Finished transcoding (2/2) for: {original_video_path} to {optimized_video_path}')
    clean_path(working_dir)
    add_quality_control_file(f'{optimized_video_path}_completed')
    return True
