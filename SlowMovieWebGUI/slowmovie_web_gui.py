# Pre requirements 
#   - pip install eel
from pprint import pprint
from pathlib import Path
import subprocess
import os
import glob
import json
import re
import eel

# Load config
import config as config

# Globals
SCRIPT_ABSOLUTE_PATH = os.path.dirname(os.path.realpath(__file__))
WORK_DIR_ABSOLUTE_PATH = SCRIPT_ABSOLUTE_PATH + "/work_dir"
APP_STATE_FILE_PATH = WORK_DIR_ABSOLUTE_PATH + "/app_state.json"
APP_STD_OUTPUT_FILE_PATH = WORK_DIR_ABSOLUTE_PATH + '/SlowMovie_output.txt'
APP_STD_OUTPUT_FILE = None 
PROCESS = None

def prepare_and_init():
    # Create work dir if not exists
    Path(WORK_DIR_ABSOLUTE_PATH).mkdir(parents=True, exist_ok=True)

def get_saved_application_state():
    if not os.path.exists(APP_STATE_FILE_PATH):
        return { 'running': False }
    with open(APP_STATE_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data

def resume_application(args):
        global PROCESS, APP_STD_OUTPUT_FILE
        # For resume only use the args which are not automatically restored by SlowMovie already (other args like the file can differ from the stored one, 
        # because SlowMovie can automatically start the next video)
        delay = args['delay']
        increment = args['increment']
        # Start with minimum of args to restore last state => The last played movie will start where stopped last (loglevel: DEBUG is neccesarry for parsing current progress later)
        process_args = [
            'python3', config.SLOW_MOVIE_EXECUTION_PATH,
            '--delay', delay,
            '--increment', increment,
            '--loglevel', 'DEBUG'
        ]
        PROCESS =  subprocess.Popen(process_args, 
            stdout=APP_STD_OUTPUT_FILE, universal_newlines=True)

def start_application(args):
    global PROCESS
    if PROCESS is None:
        with open(APP_STATE_FILE_PATH, 'w', encoding='utf-8') as f:
            args['running'] = True
            json.dump(args, f, ensure_ascii=False, indent=4)
        
        file = args['file']
        delay = args['delay']
        increment = args['increment']
        start_frame = args['start_frame']
        random_frames = args['random_frames']
        loop = args['loop']
        random_play = args['random_play']
        show_timecode = args['show_timecode']
        show_subtitles = args['show_subtitles']

        process_args = [
            'python3', config.SLOW_MOVIE_EXECUTION_PATH,
            '--file', file,
            '--delay', delay,
            '--increment', increment,
            '--loglevel', 'DEBUG'
        ]
        # Only add start frame when >= 1. Else we skip that flag so video continues where stopped last time
        if (int(start_frame) >= 1):
            process_args.append('--start')
            process_args.append(start_frame)
        if random_frames:
            process_args.append('--random-frames')
        if loop:
            process_args.append('--loop')
        if random_play:
            process_args.append('--random-file')
        if show_timecode:
            process_args.append('--timecode')
        if show_subtitles:
            process_args.append('--subtitles')
        
        # (loglevel: DEBUG is neccesarry for parsing current progress later)
        PROCESS = subprocess.Popen(process_args, stdout=APP_STD_OUTPUT_FILE, universal_newlines=True)
        return True
    else:
        print("Already running")
    return False

def stop_application():
    global PROCESS, APP_STATE_FILE_PATH
    if PROCESS is None:
        print("No application running")
        return False
    with open(APP_STATE_FILE_PATH, 'w', encoding='utf-8') as f:
        config_data = { 'running': False }
        json.dump(config_data, f, ensure_ascii=False, indent=4)
    PROCESS.terminate()
    PROCESS = None
    return True

# Get list of all available movies 
def get_movie_list():
    movie_list = []
    for file_path in glob.glob(config.SLOW_MOVIE_VIDEO_PATH + "/*.mp4"):
        file_name = os.path.basename(file_path)
        movie_list.append({ "path": file_path, "name": file_name })
    return movie_list

# Parse output and get current "live" config (played movie, delay increment etc from it). Returns False when not parseable
def get_current_live_data():
    global APP_STD_OUTPUT_FILE, APP_STD_OUTPUT_FILE_PATH
    output = ""
    if APP_STD_OUTPUT_FILE is None:
        return False
    with open(APP_STD_OUTPUT_FILE_PATH, 'r') as f:
        output = f.read()
    # Interval
    regex = r".*(?<=INFO:slowmovie:Update interval: )(.*)(?=)"
    matches_delay = re.findall(regex, output)
    # Delay
    regex = r".*(?<=INFO:slowmovie:Frame increment: )(.*)(?=)"
    matches_increment = re.findall(regex, output)
    # file
    regex = r".*(?<=INFO:slowmovie:Playing ')(.*)(?=')"
    matches_file = re.findall(regex, output)
    # total frames
    regex = r".*(?<=INFO:slowmovie:Video info: )(.*)(?= frames)"
    matches_frames_total = re.findall(regex, output)

    # Nothing found when sum is smaller 1
    if (len(matches_delay) + len(matches_increment) + len(matches_file) + len(matches_frames_total) < 1):
        return False
    # When match count is not same the newest output is not complete, so return false 
    # if not (len(matches_delay) == len(matches_increment) == len(matches_file) == len(matches_frames_total)):
    #     return False
    
    # They are different ways to get current frame, but not all are always available. When possible, always use "Current frame" as real current frame. 
    # Else use one of the others if available
    current_frame = 0

    pos_frame_start = output.rfind('INFO:slowmovie:Starting at frame ')
    pos_frame_resume = output.rfind('INFO:slowmovie:Resuming at frame ')
    pos_frame_display = output.rfind('DEBUG:slowmovie:Displaying frame ')

    # Determine current frame depending on most recent information we have
    # Start frame is most recent informatiom
    if (pos_frame_start > pos_frame_resume) and (pos_frame_start > pos_frame_display):
        regex = r".*(?<=INFO:slowmovie:Starting at frame )(.*)(?=)"
        matches_frames_starting = re.findall(regex, output)
        if len(matches_frames_starting) >= 1:
            current_frame = matches_frames_starting[-1]

    # Resume frame is most recent informatiom
    if (pos_frame_resume > pos_frame_start) and (pos_frame_resume > pos_frame_display):
        regex = r".*(?<=INFO:slowmovie:Resuming at frame )(.*)(?=)"
        matches_frames_resume = re.findall(regex, output)
        if len(matches_frames_resume) >= 1:
            current_frame = matches_frames_resume[-1]

    # Display frame is most recent informatiom
    if (pos_frame_display > pos_frame_start) and (pos_frame_display > pos_frame_resume):
        regex = r".*(?<=DEBUG:slowmovie:Displaying frame )(.*)(?= of)"
        matches_frame_current = re.findall(regex, output)
        if len(matches_frame_current) >= 1:
            current_frame = matches_frame_current[-1]

    file = matches_file[-1]
    delay = matches_delay[-1]
    increment = matches_increment[-1]
    total_frames = matches_frames_total[-1]

    return { 'file': file, 'delay': delay, 'increment': increment , 'current_frame': current_frame, 'total_frames': total_frames }

# eel
@eel.expose
def slow_movie_is_running():
    if PROCESS is not None:
        return True
    return False

@eel.expose
def slow_movie_start(file, delay, increment, start_frame, random_frames, loop, random_play, show_timecode, show_subtitles):
    args = { 'file': file, 'delay': delay, 'increment': increment, 'start_frame': start_frame, 
             'random_frames': random_frames, 'loop': loop, 'random_play': random_play, 'show_timecode': show_timecode, 'show_subtitles': show_subtitles }
    result = start_application(args)
    return result

@eel.expose
def slow_movie_stop():
    result = stop_application()
    return result

@eel.expose
def slow_movie_get_movie_list():
    return get_movie_list()

@eel.expose
def slow_movie_get_current_live_data():
    live_data = get_current_live_data()
    return live_data


# Inits
prepare_and_init()
if os.path.exists(APP_STD_OUTPUT_FILE_PATH):
    os.remove(APP_STD_OUTPUT_FILE_PATH)
APP_STD_OUTPUT_FILE = open(APP_STD_OUTPUT_FILE_PATH, 'w+')

# Restart application when it was running before
saved_application_state = get_saved_application_state() 
if saved_application_state['running']:
    resume_application(saved_application_state)

# Init local webserver
eel.init('web-frontend', allowed_extensions=['.js', '.html'])
# mode=none so no local browser is started
eel.start('main.html', mode="None", host=config.HOST, port=config.PORT)