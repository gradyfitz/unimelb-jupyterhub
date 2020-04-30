# Results metascript
# ==========================================================================
# This script handles the test result processing step of the
# assignment, checking if the processing script is present to be used,
# or else passing the assignment onto the next stage with no processing.
# This step should also pass the completed results back to the student.
#
# Recommendation 1: This step should store results.
# Recommendation 2: This step should store each result in an individual
#   file, rather than update the final collated datafile (this can be
#   done when you collect results later in a single thread). This avoids
#   any possible loss of data.
# Recommendation 3: It is possible to have your results script notify a
#   redis queue that a new processed data point is available, this can
#   be used to run a single-threaded pod that consumes this data.
#   This single-threaded pod can also perform lightweight processing
#   such as updating leaderboards, or performing MOSS-driven checking
#   of solutions upon request.
#
# Used environment variables:
# JOB_ID - From environment, the ID of the job, used to construct job-internal
#   pipe names.
# ASSIGNMENT_NAME - From environment, the name of the assignment.
# SUBMISSION_FOLDER - From environment, the location of the student's
#   submission.
# TESTING_OUTPUT_FOLDER - From environment, the location of the
#   testing output mount.
# RESULTS_OUTPUT_FOLDER - From environment, the location of the
#   results output mount.
# USERNAME - From environment, the submission student's username.
# SETUP_META_DATA_FOLDER - From environment, the folder containing the setup script.
# SETUP_META_DATA_NAME - From environment, the name of the folder containing all setup
#   metadata.
# RESULTS_DATA_FOLDER - The base results data folder copied into
#   from the setup stage. The results processing script should be at
#   $RESULTS_DATA_FOLDER/results.sh, and this path will be passed
#   directly into the script.
# RESULTS_DATA_OUTPUT_NAME - From environment, the name of the
#   metascript output file.
# STUDENT_OUTPUT_FOLDER - From environment, the folder at which output
#   should be stored that the student is allowed to read.
# STUDENT_PRIVATE_OUTPUT_FOLDER - From environment, the folder at which
#   output should be stored which might include information the student
#   is not allowed to view.
# REDIS_WAIT_SCRIPT_LOCATION - From environment, the name of the python
#   script used to wait for the specified pipe to contain a message.
# REDIS_NOTIFICATION_SCRIPT_LOCATION - From environment, the name of the
#   python script used to push an update to the redis server.
# FILE_SIGNATURE - From environment, the signature of the submitted file
# SUBMITTED_FILENAME - From environment, the name of the submitted file
#   being processed in the job.
#
# Outputs:
# → (redis) Message notifying completion of results processing to user log pipe.
# → (RESULTS_OUTPUT_FOLDER) Metascript output, form:
#   RESULT (1 line, 0 for PASS, 1 for FAILURE, 124 for TIMEOUT)
#   MESSAGE (any number of lines, no enforced convention)
# --------------------------------------------------------------------------
SETUP_META_OUTPUT_FILE="$SETUP_META_DATA_FOLDER""/""$SETUP_META_DATA_NAME"
VERIFICATION_META_OUTPUT_FILE="$VERIFICATION_OUTPUT_FOLDER""/""$VERIFICATION_DATA_OUTPUT_NAME"
TESTING_META_OUTPUT_FILE="$TESTING_OUTPUT_FOLDER""/""$TESTING_DATA_OUTPUT_NAME"

TESTING_RESULT=1
RESULTS_RESULT=1
STAGE="results"

TESTING_OUTPUT_PIPE="$JOB_ID-tested"
RESULTS_INPUT_PIPE="$JOB_ID-tested"
RESULTS_OUTPUT_PIPE="$JOB_ID-processed"

RESULTS_META_OUTPUT_FILE="$RESULTS_OUTPUT_FOLDER""/""$RESULTS_DATA_OUTPUT_NAME"
RESULTS_META_OUTPUT_FILE_TEMP="$RESULTS_META_OUTPUT_FILE""_message_only"
RESULTS_SCRIPT_LOCATION="$RESULTS_DATA_FOLDER""/results.sh"

python "$REDIS_WAIT_SCRIPT_LOCATION" "$RESULTS_INPUT_PIPE"

# See if we pass through failure.
printf "" > $RESULTS_META_OUTPUT_FILE_TEMP
if [[ -f "$TESTING_META_OUTPUT_FILE" ]]
then
    TESTING_RESULT="$(cat $TESTING_META_OUTPUT_FILE | head -n 1 | tr -d '\n')"
else
    TESTING_RESULT="1"
    # Silently mark failed if testing metascript output missing.
    #echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Testing step failed so result processing script not run." >> "$RESULTS_META_OUTPUT_FILE_TEMP"
fi

if [[ -f "$RESULTS_SCRIPT_LOCATION" ]]
then
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Beginning result processing - Using script" > "$RESULTS_META_OUTPUT_FILE_TEMP"
    "$RESULTS_SCRIPT_LOCATION" "$SUBMISSION_FOLDER" "$TESTING_RESULT" "$TESTING_OUTPUT_FOLDER" "$STUDENT_OUTPUT_FOLDER" "$JOB_ID" "$USERNAME" "$RESULTS_DATA_FOLDER" "$STUDENT_PRIVATE_OUTPUT_FOLDER" >> "$RESULTS_META_OUTPUT_FILE_TEMP"
    RESULTS_RESULT=$?
else
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "No server-side processing script present, writing all content to communication file." > "$RESULTS_META_OUTPUT_FILE_TEMP"
    RESULTS_RESULT=0
fi

echo "$RESULTS_RESULT" > "$RESULTS_META_OUTPUT_FILE"

if [[ -f "$RESULTS_META_OUTPUT_FILE_TEMP" ]]
then
  cat "$RESULTS_META_OUTPUT_FILE_TEMP" >> "$RESULTS_META_OUTPUT_FILE"
fi

if [[ ! -f "$RESULTS_SCRIPT_LOCATION" ]]
then
    OUTPUTFILE="$(echo "$SUBMITTED_FILENAME" | sed -E 's/\.zip$/\.out/g' | tr -d '\n')"
    if [[ "$OUTPUTFILE" == "$SUBMITTED_FILENAME" ]]
    then
        # If provided file wasn't a zip archive.
        OUTPUTFILE="$OUTPUTFILE"".out"
    fi

    echo "== Setup ==" > "$OUTPUTFILE"
    cat "$SETUP_META_OUTPUT_FILE" >> "$OUTPUTFILE"
    echo "" >> "$OUTPUTFILE"
    echo "== Verify ==" >> "$OUTPUTFILE"
    cat "$VERIFICATION_META_OUTPUT_FILE" >> "$OUTPUTFILE"
    echo "" >> "$OUTPUTFILE"
    echo "== Test ==" >> "$OUTPUTFILE"
    cat "$TESTING_META_OUTPUT_FILE" >> "$OUTPUTFILE"
    echo "" >> "$OUTPUTFILE"
    echo "== Results ==" >> "$OUTPUTFILE"
    echo "" >> "$OUTPUTFILE"
fi

python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$USERNAME" "$JOB_ID $STAGE $FILE_SIGNATURE $SUBMITTED_FILENAME"

# Notify next stage.
python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$RESULTS_OUTPUT_PIPE" "Ready"
