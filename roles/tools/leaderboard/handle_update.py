import time
import subprocess
import sympy.series
import os
import sys


def run_leaderboard():
    for assignment in os.listdir(os.path.join(os.getenv("ASSIGNMENT_SETUP_FOLDER"))):
        if os.path.exists(os.path.join(os.getenv("ASSIGNMENT_SETUP_FOLDER"), assignment, 
                    "leaderboard", "leaderboard_builder.py")):
            subprocess.run(['timeout', os.getenv("LEADERBOARD_TIMEOUT"), 'python', 
                        os.path.join(os.getenv("ASSIGNMENT_SETUP_FOLDER"), assignment, 
                        "leaderboard", "leaderboard_builder.py")] + sys.argv[1:])

# Initial update
last_update = time.time()  # Timestamp
run_leaderboard()

while True:
    if time.time() - last_update >= int(os.getenv("UPDATE_PERIOD", default="3600")):
        last_update = time.time()
        run_leaderboard()
    time.sleep(int(os.getenv("UPDATE_PERIOD", default="3600")))
