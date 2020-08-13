"""
A small collection of utilities useful for working with Canvas assignments.
"""
import os
import pandas as pd
import os
import subprocess
import zipfile
import submitutils
import time
import datetime
import glob
import re

def is_float(val):
    """
    Helper function to discard junk rows from queries.
    
    GJF: This probably isn't technically needed but I'm not sure
    where the issue actually is, so it's easier to just deal
    with it this way.
    """
    try:
        num = float(val)
    except ValueError:
        return False
    return True

def get_canvas_name_mapping_df(csv_name=None, first_row=2, location=r"/home/jovyan/assignments/class_raw", columns=['Student', 'ID', 'SIS Login ID'] ) -> pd.DataFrame:
    """
    Retrieves a dataframe which by default maps canvas usernames
    to Student Names as used by canvas.
    
    Location given is the base folder containing the assignments.
    
    Give columns = None to get all columns available.
    
    Required is csv_name, the rest will default.
    """
    full_string = os.popen(r"ls " + location + "/*/ | grep py").read().split('\n')
    canvas_name = os.popen(r"ls " + location + "/*/ | grep py | awk 'BEGIN { FS = " + '"' + "_" + '"'  + r"} ; {print $1}'").read().split('\n')
    l1 = os.popen(r"ls " + location + "/*/ | grep py | awk 'BEGIN { FS = " + '"' + "_" + '"'  + r"} ; {print $2}'").read().split('\n')
    l2 = os.popen(r"ls /home/jovyan/assignments/class_raw/*/ | grep py | awk 'BEGIN { FS = " + '"' + "_" + '"'  + r"} ; {print $3}'").read().split('\n')
    
    fn_field = 'First Name'
    ln_field = 'Last Name'
    canvas_id = 'ID'

    csv = pd.read_csv(csv_name)

    name_map = {}

    for i, n in enumerate(canvas_name):
        #print(n)
        if l1[i] == "LATE":
            name_map[n] = l2[i]
        else:
            name_map[n] = l1[i]
    name_map_names = list(name_map.keys())
    name_map_names.sort()
    name_map_names = [ n for n in name_map_names if is_float(name_map[n]) ]
    #name_map_kvps = [ (k, v) for k, v in name_map.items() ]
    name_map_ids = [ int(name_map[k]) for k in name_map_names if is_float(name_map[k]) ]

    df_data = {'canvas_username': name_map_names, 'ID': name_map_ids}

    name_df = pd.DataFrame(df_data)
    
    if columns is None:
        return csv.columns
    
    canvas_csv = csv[columns][first_row:]
    
    jdf = canvas_csv.set_index('ID').join(name_df.set_index('ID'), on='ID')
    
    return jdf