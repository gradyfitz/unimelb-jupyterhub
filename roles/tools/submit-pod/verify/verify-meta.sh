# Verify metascript
# ==========================================================================
# This script handles the verification step of the assignment,
# checking if the verification script is present to be used, or else
# passing the assignment onto the next stage with no verification.
#
# Used environment variables:
# JOB_ID - From environment, the ID of the job, used to construct job-internal
#   pipe names.
# SUBMISSION_FOLDER - From environment, the location of the student's
#   submission.
# VERIFICATION_OUTPUT_FOLDER - From environment, the location of the
#   verification output mount.
# USERNAME - From environment, the submission student's username.
# SETUP_RESULT_FILE - From environment, the file inside VERIFICATION_DATA_FOLDER
#   which marks whether setup succeeded or failed.
# VERIFICATION_DATA_FOLDER - The base verification data folder copied into
#   from the setup stage. The verification script should be at
#   $VERIFICATION_DATA_FOLDER/verify.sh, and this path will be passed
#   directly into the script.
# VERIFICATION_DATA_OUTPUT_NAME - From environment, the name of the
#   metascript output file.
# REDIS_WAIT_SCRIPT_LOCATION - From environment, the name of the python
#   script used to wait for the specified pipe to contain a message.
# REDIS_NOTIFICATION_SCRIPT_LOCATION - From environment, the name of the
#   python script used to push an update to the redis server.
# FILE_SIGNATURE - From environment, the signature of the submitted file
# SUBMITTED_FILENAME - From environment, the name of the submitted file
#   being processed in the job.
#
# Outputs:
# → (redis) Message with result of verification to user log pipe.
# → (VERIFICATION_OUTPUT_FOLDER) Metascript output, form:
#   RESULT (1 line, 0 for PASS, 1 for FAILURE, 124 for TIMEOUT)
#   MESSAGE (any number of lines, no enforced convention)
# --------------------------------------------------------------------------
VERIFICATION_SCRIPT_LOCATION="$VERIFICATION_DATA_FOLDER""/verify.sh"
VERIFICATION_META_OUTPUT_FILE="$VERIFICATION_OUTPUT_FOLDER""/""$VERIFICATION_DATA_OUTPUT_NAME"
VERIFICATION_META_OUTPUT_FILE_TEMP="$VERIFICATION_OUTPUT_FOLDER""/""$VERIFICATION_DATA_OUTPUT_NAME""_message_only"
SETUP_RESULT_OUTPUT="$VERIFICATION_DATA_FOLDER""/""$SETUP_RESULT_FILE"
VERIFICATION_RESULT=1
STAGE="verify"

SETUP_OUTPUT_PIPE="$JOB_ID-prepared"
VERIFICATION_INPUT_PIPE="$JOB_ID-prepared"
VERIFICATION_OUTPUT_PIPE="$JOB_ID-process"

python "$REDIS_WAIT_SCRIPT_LOCATION" "$VERIFICATION_INPUT_PIPE"

if [[ -f "$SETUP_RESULT_OUTPUT" ]]
then
    if [[ "$(cat "$SETUP_RESULT_OUTPUT" | head -n 1 | tr -d '\n')" == "0" ]]
    then
        if [[ -f "$VERIFICATION_SCRIPT_LOCATION" ]]
        then
            echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Beginning verification - Using script" > "$VERIFICATION_META_OUTPUT_FILE_TEMP"
            "$VERIFICATION_SCRIPT_LOCATION" "$SUBMISSION_FOLDER" "$VERIFICATION_OUTPUT_FOLDER" "$USERNAME" "$VERIFICATION_DATA_FOLDER" "$SUBMITTED_FILENAME" >> "$VERIFICATION_META_OUTPUT_FILE_TEMP"
            VERIFICATION_RESULT=$?
        else
            echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "No server-side verification script present, verification step passed by default." > "$VERIFICATION_META_OUTPUT_FILE_TEMP"
            VERIFICATION_RESULT=0
        fi
    else
        VERIFICATION_RESULT="1"
        echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Setup step failed so verification script not run." >> "$VERIFICATION_META_OUTPUT_FILE_TEMP"
    fi
else
    VERIFICATION_RESULT="1"
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Setup step failed so verification script not run." >> "$VERIFICATION_META_OUTPUT_FILE_TEMP"
fi




if [[ "$VERIFICATION_RESULT" == "0" ]]
then
    # Success
    echo "$VERIFICATION_RESULT" > "$VERIFICATION_META_OUTPUT_FILE"
    python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$USERNAME" "$JOB_ID $STAGE pass $FILE_SIGNATURE $SUBMITTED_FILENAME"
elif [[ "$VERIFICATION_RESULT" == "124" ]]
then
    # Timeout
    echo "$VERIFICATION_RESULT" > "$VERIFICATION_META_OUTPUT_FILE"
    python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$USERNAME" "$JOB_ID $STAGE fail $FILE_SIGNATURE $SUBMITTED_FILENAME"
else
    # Failure
    echo "$VERIFICATION_RESULT" > "$VERIFICATION_META_OUTPUT_FILE"
    python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$USERNAME" "$JOB_ID $STAGE fail $FILE_SIGNATURE $SUBMITTED_FILENAME"
fi

cat "$VERIFICATION_META_OUTPUT_FILE_TEMP" >> "$VERIFICATION_META_OUTPUT_FILE"

# Notify next stage.
python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$VERIFICATION_OUTPUT_PIPE" "Ready"
