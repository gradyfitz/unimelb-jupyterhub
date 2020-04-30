# Finalisation metascript
# ==========================================================================
# This script handles the cleanup step of the assignment, checking if the
# cleanup script is present to be used, or else notifying the reclaim queue
# that the job has finished.
#
# Note: This step probably doesn't need to do anything, but if there are
#   additional steps that can be performed after results are handed back
#   to students, it may be worth performing them here.
#
# Used environment variables:
# JOB_ID - From environment, the ID of the job, used to construct job-internal
#   pipe names.
# ASSIGNMENT_NAME - From environment, the name of the assignment.
# SUBMISSION_FOLDER - From environment, the location of the student's
#   submission.
# VERIFICATION_OUTPUT_FOLDER - From environment, the location of the
#   verification output mount.
# TESTING_OUTPUT_FOLDER - From environment, the location of the
#   testing output mount.
# RESULTS_OUTPUT_FOLDER - From environment, the location of the
#   results output mount.
# USERNAME - From environment, the submission student's username.
# VERIFICATION_DATA_FOLDER - The base verification data folder copied into
#   from the setup stage. The verification script should be at
#   $VERIFICATION_DATA_FOLDER/verify.sh, and this path will be passed
#   directly into the script.
# VERIFICATION_DATA_OUTPUT_NAME - From environment, the name of the
#   metascript output file.
# TESTING_DATA_FOLDER - The base testing data folder copied into
#   from the setup stage. The testing script should be at
#   $TESTING_DATA_FOLDER/test.sh, and this path will be passed
#   directly into the script.
# TESTING_DATA_OUTPUT_NAME - From environment, the name of the
#   metascript output file.
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
# → (redis) Message notifying completion of finalisation to user log pipe.
# → (redis) Message notifying completion of job to cleanup queue.
# → (STUDENT_OUTPUT_FOLDER) Metascript output, form:
#   RESULT (1 line, 0 for PASS, 1 for FAILURE, 124 for TIMEOUT)
#   MESSAGE (any number of lines, no enforced convention)
# --------------------------------------------------------------------------
TESTING_META_OUTPUT_FILE="$TESTING_OUTPUT_FOLDER""/""$TESTING_DATA_OUTPUT_NAME"
RESULTS_META_OUTPUT_FILE=""
TESTING_RESULT=1
FINALISE_RESULT=1
STAGE="finalise"

RESULTS_OUTPUT_PIPE="$JOB_ID-processed"
FINALISE_INPUT_PIPE="$JOB_ID-processed"
FINALISE_OUTPUT_PIPE="cleanup"

FINALISE_SCRIPT_LOCATION="$RESULTS_DATA_FOLDER""/test.sh"

python "$REDIS_WAIT_SCRIPT_LOCATION" "$FINALISE_INPUT_PIPE"

# See if we pass through failure.
printf "" > $FINALISE_META_OUTPUT_FILE_TEMP
if [[ -f "$TESTING_META_OUTPUT_FILE" ]]
then
    TESTING_RESULT="$(cat $TESTING_META_OUTPUT_FILE | head -n 1 | tr -d '\n')"
else
    TESTING_RESULT="1"
    # Silently mark failed if testing metascript output missing.
    #echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Testing step failed so result processing script not run." >> "$RESULTS_META_OUTPUT_FILE_TEMP"
fi

if [[ -f "$FINALISE_SCRIPT_LOCATION" ]]
then
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Beginning result processing - Using script" > "$FINALISE_META_OUTPUT_FILE_TEMP"
    "$FINALISE_SCRIPT_LOCATION" "$SUBMISSION_FOLDER" "$TESTING_RESULT" "$TESTING_OUTPUT_FOLDER" "$STUDENT_OUTPUT_FOLDER" "$JOB_ID" "$USERNAME" "$RESULTS_DATA_FOLDER" "$" "$STUDENT_PRIVATE_OUTPUT_FOLDER"
    RESULTS_RESULT=$?
else
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "No server-side testing script present, testing step passed by default." > "$FINALISE_META_OUTPUT_FILE_TEMP"
    FINALISE_RESULT=0
fi

echo "$FINALISE_RESULT" > "$FINALISE_META_OUTPUT_FILE"
python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$USERNAME" "$JOB_ID $STAGE $FILE_SIGNATURE $SUBMITTED_FILENAME"

if [[ -f "$FINALISE_META_OUTPUT_FILE_TEMP" ]]
then
  cat "$FINALISE_META_OUTPUT_FILE_TEMP" >> "$FINALISE_META_OUTPUT_FILE"
fi

# Notify user queue.
python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$FINALISE_OUTPUT_PIPE" "$JOB_ID"
