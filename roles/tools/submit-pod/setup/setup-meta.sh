# Setup metascript
# ==========================================================================
# This script handles the setup step of the assignment which copies all
# user scripts and data to their relevant volumes and locations. 
# 
# Used environment variables: 
# JOB_ID - From environment, the ID of the job, used to construct job-internal
#   pipe names.
# ASSIGNMENT_NAME - From environment, the name of the assignment.
# RAW_SUBMISSIONS_FOLDER - From environment, the root location of the 
#   submissions mount.
# SUBMISSION_FOLDER - From environment, the location of the student's  
#   submission.
# USERNAME - From environment, the submission student's username.
# ASSIGNMENT_SETUP_FOLDER - From environment, contains all assignments.
# SETUP_META_DATA_FOLDER - From environment, the folder which setup script 
#   output will be placed.
# SETUP_META_DATA_NAME - From environment, the name of the folder containing 
#   all setup metadata.
# SETUP_CONFIG_FILE_NAME - From environment, the filename of the configuration
#   file. 
# SETUP_RESULT_FILE - From environment, the filename to place the result of
#  setup into.
# VERIFICATION_DATA_FOLDER - The base verification data folder copied into 
#   in this stage.
# TESTING_DATA_FOLDER - The base testing data folder copied into 
#   in this stage.
# RESULTS_DATA_FOLDER - The base results data folder copied into 
#   in this stage.
# FINALISE_DATA_FOLDER - The base finalisation data folder copied into 
#   in this stage.
# STUDENT_PRIVATE_OUTPUT_FOLDER - From environment, the folder at which
#   output should be stored which might include information the student
#   is not allowed to view.
# REDIS_WAIT_SCRIPT_LOCATION - From environment, the name of the python
#   script used to wait for the specified pipe to contain a message.
# REDIS_NOTIFICATION_SCRIPT_LOCATION - From environment, the name of the 
#   python script used to push an update to the redis server.
# FILE_SIGNATURE - From environment, the SHA1 signature of the submitted file
# SUBMITTED_FILENAME - From environment, the name of the submitted file 
#   being processed in the job.
# 
# Configurable Settings:
# MAXSIZE - Maximum submissions size, the size at which a submission will
#   fail purely based on size. Submissions surpassing this size won't be 
#   transferred to the raw submissions folder, instead the checksum will be
#   verified and then saved in the file's stead. Size in bytes.
#
# Settings Format:
# For simplicity, each option on a line, setting implied (i.e. with only 
#   one setting, this will be )
#
# Outputs: 
# → (redis) Message notifying completion of setup stage to user log pipe 
#   along with all submission details. 
# → (RESULTS_OUTPUT_FOLDER) Metascript output, form: 
#   RESULT (1 line, 0 for PASS, 1 for FAILURE, 124 for TIMEOUT) 
#   MESSAGE (any number of lines, no enforced convention) 
#
# Setup current data output
# Username - Submitted user's username.
# Filename - Filename submitted.
# Submit Server Accept Timestamp - Timestamp of submit script.
# Filesize - Server's read of submitted file's filesize.
# Submitted File Signature - File signature provided by user.
# Server File Signature - File signature calculated from raw file on server,
#   if the filesize is too large, the client volume file version will be 
#   used instead.
# Submission Certificate Plaintext - A string consisting of 
#   [username]-[filename]-[server file signature]-[submit server accept timestamp]
# Submission Verification Certificate - The submission certificate plaintext
#   signed with the RSA key.
# Message - "Please keep the certificate plaintext, the verification certificate
#            and the zip file submitted on your behalf stored somewhere safe
#            as proof of your submission at the time given in the plaintext"
#
# Secrets:
# PRIVATE_SIGNING_KEY - An RSA private key used to sign certificates. This 
#   is ultimately to ensure even if the hub data itself is damaged, diligent
#   students still have proof they submitted their assignment correctly.
# PUBLIC_SIGNING_KEY - An RSA public key used to verify certificates.
# --------------------------------------------------------------------------
SETUP_META_OUTPUT_FILE="$SETUP_META_DATA_FOLDER""/""$SETUP_META_DATA_NAME"
SETUP_META_OUTPUT_FILE_TEMP="$SETUP_META_OUTPUT_FILE""_temp"
RESULTS_META_OUTPUT_FILE=""
SETUP_RESULT=0
STAGE="setup"

SETUP_OUTPUT_PIPE="$JOBID-prepared"

# Setup configuration options file. supported settings as described in 
#   Configurable Settings.
SETUP_CONFIG_FILE_LOCATION="$SETUP_META_DATA_FOLDER""/""$SETUP_CONFIG_FILE_NAME"


# Names of each folder, principally arbitrary, but kind to keep them matching
#   their destinations.
VERIFICATION_FOLDER_STRING="verification"
TESTING_FOLDER_STRING="testing"
RESULTS_FOLDER_STRING="results"
FINALISE_FOLDER_STRING="finalise"

SOURCE_VERIFICATION_DATA_FOLDER="$SETUP_META_DATA_FOLDER""/""$ASSIGNMENT_NAME""$VERIFICATION_FOLDER_STRING"
SOURCE_TESTING_DATA_FOLDER="$SETUP_META_DATA_FOLDER""/""$ASSIGNMENT_NAME""$TESTING_FOLDER_STRING"
SOURCE_RESULTS_DATA_FOLDER="$SETUP_META_DATA_FOLDER""/""$ASSIGNMENT_NAME""$RESULTS_FOLDER_STRING"
SOURCE_FINALISE_DATA_FOLDER="$SETUP_META_DATA_FOLDER""/""$ASSIGNMENT_NAME""$FINALISE_FOLDER_STRING"

# Copy any folders to their relevant mounts.
if [[ -d "$SOURCE_VERIFICATION_DATA_FOLDER" ]]
then
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Setup - Using custom verification script."
    find "$SOURCE_FINALISE_DATA_FOLDER" -exec cp "{}" "$VERIFICATION_DATA_FOLDER" \;
fi

if [[ -d "$SOURCE_TESTING_DATA_FOLDER" ]]
then
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Setup - Using custom testing script."
    find "$SOURCE_FINALISE_DATA_FOLDER" -exec cp "{}" "$TESTING_DATA_FOLDER" \;
fi

if [[ -d "$SOURCE_RESULTS_DATA_FOLDER" ]]
then
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Setup - Using custom results script."
    find "$SOURCE_FINALISE_DATA_FOLDER" -exec cp "{}" "$RESULTS_DATA_FOLDER" \;
fi

if [[ -d "$SOURCE_FINALISE_DATA_FOLDER" ]]
then
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Setup - Using custom finalise script."
    find "$SOURCE_FINALISE_DATA_FOLDER" -exec cp "{}" "$FINALISE_DATA_FOLDER" \;
fi

# Evaluate Submission for size.
FILESIZE_USER=$(du -cbs "$SUBMISSION_FOLDER" | tail -n 1 | awk '{print $1}' | tr -d '\n')

if [[ -f "$SETUP_CONFIG_FILE_LOCATION" ]]
then
    CONFIG_MAXSIZE=$(cat $SETUP_CONFIG_FILE_LOCATION | head -n 1 | tr -d '\n')
    echo "[$(date +'%Y/%m/%d %H:%M:%S')]" "Setup - Config option MAXSIZE set to $CONFIG_MAXSIZE."
    
    if [[ "$FILESIZE_USER" -gt "$CONFIG_MAXSIZE" ]]
    then
      echo "Setup failed - Filesize $FILESIZE_USER >= $CONFIG_MAXSIZE" >> "$SETUP_META_OUTPUT_FILE_TEMP"
      SETUP_RESULT=1
    #else
      #echo "Filesize $FILESIZE_USER < $CONFIG_MAXSIZE" >> "$SETUP_META_OUTPUT_FILE_TEMP"
    fi
fi

SERVER_CHECKSUM=""

if [[ "$SETUP_RESULT" == "0" ]]
then
    # Copy file over to raw submissions, certify submission against provided signature.
    mkdir -p "$RAW_SUBMISSIONS_FOLDER""/""$ASSIGNMENT_NAME""/""$USERNAME"
    cp "$SUBMISSION_FOLDER""/""$SUBMITTED_FILENAME" "$RAW_SUBMISSIONS_FOLDER""/""$ASSIGNMENT_NAME""/""$USERNAME"
    SETUP_RESULT="$?"
    if [[ "$SETUP_RESULT" == "0" ]]
    then
        SERVER_CHECKSUM=$(sha1sum "$RAW_SUBMISSIONS_FOLDER""/""$ASSIGNMENT_NAME""/""$USERNAME""/""$SUBMITTED_FILENAME" | head -n 1 | awk '{ print $1 }' | tr -d '\n')
    else
        echo "Copy failed - Unknown Error" >> "$SETUP_META_OUTPUT_FILE_TEMP"
        SERVER_CHECKSUM=$(sha1sum "$SUBMISSION_FOLDER""/""$SUBMITTED_FILENAME" | head -n 1 | awk '{ print $1 }' | tr -d '\n')
    fi
else
    # Calculate checksum still.
    echo "Submitted file too large" >> "$SETUP_META_OUTPUT_FILE_TEMP"
    SERVER_CHECKSUM=$(sha1sum "$SUBMISSION_FOLDER""/""$SUBMITTED_FILENAME" | head -n 1 | awk '{ print $1 }' | tr -d '\n')
fi

SERVER_ACCEPT_TIMESTAMP="$(date +'%Y/%m/%d %H:%M:%S')"
SUBMISSION_VERIFICATION_PLAINTEXT=""
SUBMISSION_VERIFICATION_CERTIFICATE=""

PYTHON_RUN_SCRIPT="print(0) if "'"'"$SERVER_CHECKSUM"'"'" == "'"'"$FILE_SIGNATURE"'"'" else print(1)"
if [[ ! $(python -c "$PYTHON_RUN_SCRIPT") == "0" ]]
then
    echo "Submitted file did not copy successfully or the submitted sha1 signature is wrong, please try to resubmit your work (certificate not valid)" >> "$SETUP_META_OUTPUT_FILE_TEMP"
    SETUP_RESULT="1"
else
    SUBMISSION_VERIFICATION_PLAINTEXT="$USERNAME-$SUBMITTED_FILENAME-$SERVER_CHECKSUM-$SERVER_ACCEPT_TIMESTAMP"
    SUBMISSION_VERIFICATION_CERTIFICATE=$(openssl rsautl -encrypt -pubin -inkey $PRIVATE_SIGNING_KEY)
fi



echo "$SETUP_RESULT" > "$SETUP_META_OUTPUT_FILE"
echo "  Username: $USERNAME
  Filename: $SUBMITTED_FILENAME
  Submit Server Accept Timestamp: $SERVER_ACCEPT_TIMESTAMP
  Filesize: $FILESIZE_USER
  Submitted File Signature: $FILE_SIGNATURE
  Server File Signature: $SERVER_CHECKSUM
  Submission Certificate Plaintext: $SUBMISSION_VERIFICATION_PLAINTEXT
  Submission Verification Certificate: $SUBMISSION_VERIFICATION_CERTIFICATE
  Please keep the certificate plaintext, the verification certificate
  and the zip file submitted on your behalf stored somewhere safe
  as proof of your submission at the time given in the plaintext" >> "$SETUP_META_OUTPUT_FILE"
python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$USERNAME $STAGE $JOB_ID $FILE_SIGNATURE $SUBMITTED_FILENAME"

cat "$SETUP_META_OUTPUT_FILE_TEMP" >> "$SETUP_META_OUTPUT_FILE"
echo "$SETUP_RESULT" > "$VERIFICATION_DATA_FOLDER""/""$SETUP_RESULT_FILE"

# Notify user queue.
python "$REDIS_NOTIFICATION_SCRIPT_LOCATION" "$SETUP_OUTPUT_PIPE Ready"
