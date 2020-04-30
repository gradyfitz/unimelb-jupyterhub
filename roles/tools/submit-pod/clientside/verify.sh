# For now, simple test, Just check the file is smaller than 1M
# Run with 
#   verify.sh SUBMISSION_FOLDER SUBMISSION_FILE VERIFICATION_OUTPUT_FOLDER USERNAME VERIFICATION_EXTRA_DATA_FOLDER
# 
# SUBMISSION_FOLDER - The folder which contains the submission contents
# VERIFICATION_OUTPUT_FOLDER - The folder which contains the result of verification
# USERNAME - The username of the user to be tested
# VERIFICATION_EXTRA_DATA_FOLDER - Location of any extra data which this script should know about.
SUBMISSION_FOLDER="$1"
VERIFICATION_OUTPUT_FOLDER="$2"
USERNAME="$3"
VERIFICATION_EXTRA_DATA_FOLDER="$4"

# 1M filesize limit
FILESIZE_LIMIT=$(python -c "print(1024 * 1024)" | tr -d '\n')

# Verification log data file.
VERIFICATION_LOG="$VERIFICATION_OUTPUT_FOLDER""/verify_out.txt"

FILESIZE=$(du -cbs "$SUBMISSION_FOLDER" | tail -n 1 | awk '{print $1}' | tr -d '\n')
echo "" > "$VERIFICATION_LOG"
if [[ $FILESIZE -gt $FILESIZE_LIMIT ]]
then
  echo "Filesize $FILESIZE >= $FILESIZE_LIMIT" >> "$VERIFICATION_LOG"
  echo "Failed Verification" >> "$VERIFICATION_LOG"
  exit 1
else
  echo "Filesize $FILESIZE < $FILESIZE_LIMIT" >> "$VERIFICATION_LOG"
  echo "Passed Verification" >> "$VERIFICATION_LOG"
  exit 0
fi
