PORT = 22
LOCAL_FIRMWARE_FILE_NAME = "firmware.py"
REMOTE_FIRMWARE_PATH = "/home/root/firmware.py" # DO NOT CHANGE THIS
MAX_DOWNLOAD_WAIT_TIME = 120 # max wait time to download a file, in seconds. Note that the firmware file will gather data for 80 seconds or 80*ADC_SAMPLING_RATE = 80*250 iterations
DOWNLOAD_DELAY = 10 # time to wait in between checking if the file is created, in seconds