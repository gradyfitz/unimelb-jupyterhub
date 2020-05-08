"""
This file contains utilities to help with submission.
"""
import os
from typing import List, Dict
import time, datetime
import hashlib
import math
import redis
import glob

def relative_path(base_folder: str, full_path: str) -> str:
    """
    This takes the name of the base folder and a file inside it and returns the
    relative path of the file inside that folder.
    """
    return os.popen("realpath --relative-to=\"{}\" \"{}\"".format(base_folder, full_path)).read().splitlines()[0]

def file_list(folder: str) -> List[Dict[str, str]]:
    """
    This takes the name of a folder and returns a list of all the items in that folder
    as dictionaries containing the name of the file, the path of the file and the 
    modified timestamp in seconds and as a date-time string.
    """
    list_of_files = []
    for file in os.listdir(folder):
        # Ignore all hidden files.
        if file[0] == '.':
            continue
        new_dict = {}
        full_path = os.path.join(folder, file)
        m_time = os.path.getmtime(full_path)
        new_dict['filename'] = file
        new_dict['path'] = full_path
        new_dict['relative_path'] = relative_path(folder, full_path)
        new_dict['modified_s'] = m_time
        new_dict['timestamp'] = time.ctime(m_time)
        timestamp = datetime.datetime.fromtimestamp(m_time)
        new_dict['timestampstring'] = "%d%02d%02d%02d%02d%02d" % (timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute, timestamp.second)
        list_of_files.append(new_dict)
        filesize = os.path.getsize(full_path)
        new_dict['raw_filesize'] = filesize
    return list_of_files

def get_file_hash(path: str) -> str:
    """
    This takes a file path and returns the hash of the file at that
    location.
    
    Borrowed from 
    https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    """
    sha1 = hashlib.sha1()
    with open(path, 'rb') as f:
        data = f.read()
        sha1.update(data)
    return sha1.hexdigest()

def get_friendly_size(raw_size: int, round_dp=1) -> str:
    """
    Converts the given raw size in bytes to the largest
    of KiB, MiB and GiB which does not reduce the numeric
    component to less than one.
    Rounds _up_ to the nearest value.
    """
    denominations = [' bytes', 'KiB', 'MiB', 'GiB']
    index = 0
    friendly_number = raw_size
    while index < (len(denominations) - 1):
        if friendly_number > 1024:
            index = index + 1
            friendly_number = friendly_number / 1024
        else:
            break
    if not index == 0:
        exponent = 10 ** round_dp
        friendly_number = math.ceil((friendly_number * exponent)) / exponent
    return str(friendly_number) + denominations[index]

def get_username() -> str:
    # Get the current server's name and then get the part after the
    # first dash and drop the newline.
    awk_command = "hostname -s | awk 'BEGIN { FS = \"-\" } ; { print $2 }' | tr -d '\n'"
    return os.popen(awk_command).read()
    
def submit_to_queue(submit_mode="submit", username=None, assignment=None, zip_hash=None, submit_path=None) -> bool:
    """
        Submit mode is "submit" when user disk control is used as authorization.
        Submit mode is "psubmit" when command signing is used as authorization.
        Returns false if all values correctly set.
    """
    if submit_mode == "submit":
        if username is None or assignment is None or zip_hash is None or submit_path is None:
            return False
        r = redis.Redis(host="redis")
        r.rpush(submit_mode, "{} {} {} {} {}".format(submit_mode, username, assignment, zip_hash, submit_path))
        return True
    else:
        return False

def monitor_queue(queue=None, complete_stage=None, monitor_file=None, submission_name=None) -> bool:
    """
        Returns true/false if verify is complete_stage, 
            returns true otherwise if it returns. This is in principle
            not parallel-friendly
    """
    r = redis.Redis(host="redis")
    
    while True:
        item = r.lpop(queue)
        if item is None:
            # Sleep for ten seconds.
            time.sleep(10)
        else:
            print(item.decode("utf-8"))
            if monitor_file:
                with open(monitor_file, "a+") as f:
                    f.write(item.decode("utf-8") + '\n')
            if finalise(item.decode("utf-8"), complete_stage, submission_name):
                if not complete_stage == "verify":
                    return True
                else:
                    words = item.decode("utf-8").split()
                    return words[2] == "pass"
    

def finalise(message: str, complete_stage: str, submission_name: str) -> bool:
    """
    Returns true if the given message reports the stage given is
    completed for the given submission.
    
    Messages usually in format:
        job_id stage signature submission_filename
    Except for verify step which broadcasts success or failure of execution:
        job_id stage success signature submission_filename
    And the setup step which broadcasts job data:
        job_id stage <submitted message data>
    Setup is not a valid checkable as the message is, in 
        principle, ambiguous by design.
    """
    words = message.split()
    print(words)
    if len(words) > 2:
        if words[1] == complete_stage:
            if complete_stage == "verify":
                if " ".join(words[4:]) == submission_name:
                    return True
            elif complete_stage == "setup":
                return True
            else:
                if " ".join(words[3:]) == submission_name:
                    return True
    return False

def latest_matching_glob(glob_str: str) -> str:
    files = []
    for file in glob.glob(glob_str):
        mod_time = os.stat(file).st_mtime
        files.append({'name': file, 'm_time': mod_time})
    files.sort(key=lambda x: x['m_time'], reverse=True)
    # This could throw an exception if no log files are present.
    return files[0]['name']
    