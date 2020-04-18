# Test metascript
# ==========================================================================
# This script handles the testing step of the assignment,  
# checking if the testing script is present to be used, or else 
# passing the assignment onto the next stage with no testing. 
# 
# Used environment variables: 
# JOB_ID - From environment, the ID of the job, used to construct job-internal
#   pipe names.
# SUBMISSION_FOLDER - From environment, the location of the student's  
#   submission. 
# VERIFICATION_OUTPUT_FOLDER - From environment, the location of the 
#   verification output mount.
# TESTING_OUTPUT_FOLDER - From environment, the location of the 
#   testing output mount.
# USERNAME - From environment, the submission student's username. 
# TESTING_DATA_FOLDER - The base testing data folder copied into 
#   from the setup stage. The testing script should be at 
#   $TESTING_DATA_FOLDER/test.sh, and this path will be passed
#   directly into the script.
# TESTING_DATA_OUTPUT_NAME - From environment, the name of the  
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
# → (redis) Message with testing completion note to user log pipe. 
# → (TEST_OUTPUT_FOLDER) Metascript output, form: 
#   RESULT (1 line, 0 for PASS, 1 for FAILURE, 124 for TIMEOUT) 
#   MESSAGE (any number of lines, no enforced convention) 
# --------------------------------------------------------------------------
VERIFICATION_META_OUTPUT_FILE="$VERIFICATION_OUTPUT_FOLDER""/""$VERIFICATION_DATA_OUTPUT_NAME"
VERIFICATION_RESULT=1
TESTING_RESULT=1
STAGE="test"

VERIFICATION_OUTPUT_PIPE="$JOBID-process"
TESTING_INPUT_PIPE="$JOBID-process"
TESTING_OuTPUT_PIPE="$JOBID-tested"

TESTING_META_OUTPUT_FILE="$TESTING_OUTPUT_FOLDER""/""$TESTING_DATA_OUTPUT_NAME"
TESTING_META_OUTPUT_FILE_TEMP="$TESTING_META_OUTPUT_FILE""_message_only"
TESTING_SCRIPT_LOCATION="$TESTING_DATA_FOLDER""/test.sh"

python "$REDIS_WAIT_SCRIPT_LOCATION" "$TESTING_INPUT_PIPE"

# See if we pass through failure.
printf "" > $TESTING_META_OUTPUT_FILE_TEMP
if [[ -f "$VERIFICATION_META_OUTPUT_FILE" ]]
then
    VERIFICATION_RESULT="$(cat $VERIFICATION_META_OUTPUT_FILE | head -n 1 | tr -d '\n')"
    if [[ "$VERIFICATION_RESULT""" == 0 ]]
    then
        if [[ -f "$TESTING_SCRIPT_LOCATION" ]]
        then
            echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Beginning testing - Using script" > "$TESTING_META_OUTPUT_FILE_TEMP"
            "$TESTING_SCRIPT_LOCATION" "$SUBMISSION_FOLDER" "$TESTING_OUTPUT_FOLDER" "$USERNAME" "$TESTING_DATA_FOLDER" >> "$TESTING_META_OUTPUT_FILE_TEMP"
            TESTING_RESULT=$?
        else
            echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "No server-side testing script present, testing step passed by default." > "$TESTING_META_OUTPUT_FILE_TEMP"
            TESTING_RESULT=0
        fi

        echo "$TESTING_RESULT" > "$TESTING_META_OUTPUT_FILE"
        python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$USERNAME $JOB_ID $STAGE $FILE_SIGNATURE $SUBMITTED_FILENAME"
    else
        VERIFICATION_RESULT="1"
        TESTING_RESULT="1"
    fi
else
    VERIFICATION_RESULT="1"
    TESTING_RESULT="1"
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Verification step failed so testing script not run." >> "$TESTING_META_OUTPUT_FILE_TEMP"
fi

if [[ ! "$VERIFICATION_RESULT" == "0" ]]
then
    echo "$TESTING_RESULT" > "$TESTING_META_OUTPUT_FILE"
fi

cat "$TESTING_META_OUTPUT_FILE_TEMP" >> "$TESTING_META_OUTPUT_FILE"

# Notify next stage.
python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$TESTING_OUTPUT_PIPE Ready"
