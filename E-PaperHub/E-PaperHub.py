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
REMEMBER_FILE_RUNNING_APP_PATH = WORK_DIR_ABSOLUTE_PATH + "/remember_running_app.json"
PROCESS_CURRENT = None
RUNNING_APP = ""

def prepare_and_init():
    # Create work dir if not exists
    Path(WORK_DIR_ABSOLUTE_PATH).mkdir(parents=True, exist_ok=True)

def start_application(application, args = None):
    global RUNNING_APP, REMEMBER_FILE_RUNNING_APP_PATH, PROCESS_CURRENT
    if not RUNNING_APP == application.application_name:
        RUNNING_APP = application.application_name
        with open(REMEMBER_FILE_RUNNING_APP_PATH, 'w', encoding='utf-8') as f:
            config_data = { 'running': RUNNING_APP }
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        PROCESS_CURRENT = application.start(args)
        return True
    else:
        print("Already running: " + APP_SLOW_MOVIE.application_name)
    return False

def stop_application(application):
    global RUNNING_APP, REMEMBER_FILE_RUNNING_APP_PATH, PROCESS_CURRENT
    if PROCESS_CURRENT is None:
        print("No application running")
        return False
    application.stop()
    with open(REMEMBER_FILE_RUNNING_APP_PATH, 'w', encoding='utf-8') as f:
        config_data = { 'running': "" }
        json.dump(config_data, f, ensure_ascii=False, indent=4)
    RUNNING_APP = ""
    PROCESS_CURRENT.terminate()
    PROCESS_CURRENT = None
    return True

def resume_application(application, args = None):
    global PROCESS_CURRENT
    print("Resume application: " + application.application_name)
    RUNNING_APP = application.application_name
    PROCESS_CURRENT = application.resume(args)

def get_running_application_from_file():
    if not os.path.exists(REMEMBER_FILE_RUNNING_APP_PATH):
        return False
    with open(REMEMBER_FILE_RUNNING_APP_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['running']

@eel.expose
def get_running_application():
    return RUNNING_APP

# SlowMovie
class Application_SlowMovie:
    application_name = "SlowMovie"
    application_execution_path = config.SLOW_MOVIE_EXECUTION_PATH
    application_video_path = config.SLOW_MOVIE_VIDEO_PATH
    application_work_dir = WORK_DIR_ABSOLUTE_PATH + "/SlowMovie"
    application_work_dir_data_path = application_work_dir + '/SlowMovie.json'
    application_work_dir_std_output_path = application_work_dir + '/SlowMovie_output.txt'
    application_work_dir_std_output_file = None

    config_file = ""
    config_delay = 120
    config_increment = 4

    # Has to be implemented
    def __init__(self):
        # Create application specific work dir if not exists
        Path(self.application_work_dir).mkdir(parents=True, exist_ok=True)
        # Delete old output file if exists
        if os.path.exists(self.application_work_dir_std_output_path):
            os.remove(self.application_work_dir_std_output_path)

        # Load old config if exiting
        if os.path.exists(self.application_work_dir_data_path):
            with open(self.application_work_dir_data_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.config_file = config_data['file']
                self.config_delay = config_data['delay']
                self.config_increment = config_data['increment']
        # Create and open output file
        self.application_work_dir_std_output_file = open(self.application_work_dir_std_output_path, 'w+')
    
    # Has to be implemented
    def resume(self, args = None):
        # Start without args => resume where stopped last time (loglevel: DEBUG is neccesarry for parsing current progress later)
        return subprocess.Popen(['python3', self.application_execution_path, '--loglevel', 'DEBUG'], 
            stdout=self.application_work_dir_std_output_file, universal_newlines=True)

    # Has to be implemented
    def start(self, args):
        self.config_file = args['file']
        self.config_delay = args['delay']
        self.config_increment = args['increment']

        print("Start Application: " + self.application_name)
        with open(self.application_work_dir_data_path, 'w', encoding='utf-8') as f:
            config_data = { 'file': self.config_file, 'delay': self.config_delay, 'increment': self.config_increment }
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        # (loglevel: DEBUG is neccesarry for parsing current progress later)
        return subprocess.Popen(['python3', self.application_execution_path, '--file', self.config_file, '--delay', self.config_delay, '--increment', self.config_increment, '--start', '1',  '--loglevel', 'DEBUG'], 
                stdout=self.application_work_dir_std_output_file, universal_newlines=True)

    # Has to be implemented
    def stop(self):
        return True

    # Get list of all available movies 
    def get_movie_list(self):
        movie_list = []
        for file_path in glob.glob(self.application_video_path + "/*.mp4"):
            file_name = os.path.basename(file_path)
            movie_list.append({ "path": file_path, "name": file_name })
            # print("File path: " + file_path + " File name: " + file_name)
        return movie_list
    
    # Parse output and get current "live" config (played movie, delay increment etc from it). Returns False when not parseable
    def get_current_live_data(self):
        output = ""
        if self.application_work_dir_std_output_file is None:
            return False
        with open(self.application_work_dir_std_output_path, 'r') as f:
            output = f.read()
        print("Output: ")
        print(output)
        # Interval
        regex = r".*(?<=INFO:slowmovie:Update interval: )(.*)(?=)"
        matches_delay = re.findall(regex, output)
        pprint(matches_delay) # DEBUG
        # Delay
        regex = r".*(?<=INFO:slowmovie:Frame increment: )(.*)(?=)"
        matches_increment = re.findall(regex, output)
        pprint(matches_increment) # DEBUG
        # file
        regex = r".*(?<=INFO:slowmovie:Playing ')(.*)(?=')"
        matches_file = re.findall(regex, output)
        pprint(matches_file) # DEBUG
        # total frames
        regex = r".*(?<=INFO:slowmovie:Video info: )(.*)(?= frames)"
        matches_frames_total = re.findall(regex, output)
        pprint(matches_frames_total) # DEBUG

        # Nothing found when sum is smaller 1
        if (len(matches_delay) + len(matches_increment) + len(matches_file) + len(matches_frames_total) < 1):
            print("Nothing found. Sum < 1") # DEBUG
            return False
        # When match count is not same the newest output is not complete, so return false 
        # if not (len(matches_delay) == len(matches_increment) == len(matches_file) == len(matches_frames_total)):
        #     print("Match count is not same") # DEBUG
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
            print("matches_frames_starting") # DEBUG
            pprint(matches_frames_starting) # DEBUG

        # Resume frame is most recent informatiom
        if (pos_frame_resume > pos_frame_start) and (pos_frame_resume > pos_frame_display):
            regex = r".*(?<=INFO:slowmovie:Resuming at frame )(.*)(?=)"
            matches_frames_resume = re.findall(regex, output)
            if len(matches_frames_resume) >= 1:
                current_frame = matches_frames_resume[-1]
            print("matches_frames_resume") # DEBUG
            pprint(matches_frames_resume) # DEBUG

        # Display frame is most recent informatiom
        if (pos_frame_display > pos_frame_start) and (pos_frame_display > pos_frame_resume):
            regex = r".*(?<=DEBUG:slowmovie:Displaying frame )(.*)(?= of)"
            matches_frame_current = re.findall(regex, output)
            if len(matches_frame_current) >= 1:
                current_frame = matches_frame_current[-1]
            print("matches_frame_current") # DEBUG
            pprint(matches_frame_current) # DEBUG

        file = matches_file[-1]
        delay = matches_delay[-1]
        increment = matches_increment[-1]
        total_frames = matches_frames_total[-1]

        return { 'file': file, 'delay': delay, 'increment': increment , 'current_frame': current_frame, 'total_frames': total_frames }


@eel.expose
def slow_movie_start(file, delay, increment):
    args = { 'file': file, 'delay': delay, 'increment': increment }
    result = start_application(APP_SLOW_MOVIE, args)
    return result

@eel.expose
def slow_movie_stop():
    result = stop_application(APP_SLOW_MOVIE)
    return result

@eel.expose
def slow_movie_get_movie_list():
    return APP_SLOW_MOVIE.get_movie_list()

@eel.expose
def slow_movie_get_current_live_data():
    live_data = APP_SLOW_MOVIE.get_current_live_data()
    print("Current live data:") # DEBUG
    pprint(live_data)
    return live_data

# Init all applications
APP_SLOW_MOVIE = Application_SlowMovie()

result = get_running_application_from_file()
if result != False:
    RUNNING_APP = result

if RUNNING_APP == APP_SLOW_MOVIE.application_name:
    resume_application(APP_SLOW_MOVIE)

# Init local webserver
eel.init('web-frontend', allowed_extensions=['.js', '.html'])
eel.start('main.html', mode="None", host=config.IP, port=config.PORT)





