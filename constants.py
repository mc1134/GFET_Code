PORT = 22
LOCAL_FIRMWARE_FILE_NAME = "firmware.py"
REMOTE_FIRMWARE_PATH = "/home/root/firmware.py" # DO NOT CHANGE THIS
MAX_DOWNLOAD_WAIT_TIME = 120 # max wait time to download a file, in seconds. Note that the firmware file will gather data for 80 seconds or 80*ADC_SAMPLING_RATE = 80*250 iterations
DOWNLOAD_DELAY = 10 # time to wait in between checking if the file is created, in seconds
DOWNLOAD_STR = "No download directory selected."

HELP_STRING = f"""
==============================
| GFET GUI PROGRAM           |
| Built for Lal Lab          |
| Last updated: Jan 25, 2023 |
| Author: Michael Chen       |
==============================

Controls:
- Connect: connects to the IP address specified in the "Enter IP Address" field via SSH.
- Disconnect: disconnects from the connected microcontroller. Has no effect if not connected.
- Select file directory: opens a folder selector popup, enabling you to choose a location to
  download files to from the SSH connection.
- Baseline: runs firmware module on connected microcontroller to produce a data file in 80-90
  seconds, or if the maximum timeout of {MAX_DOWNLOAD_WAIT_TIME} is reached the data collection stops and times out.
  Requires active SSH connection.
- Sample: does the exact same thing as the Baseline button.
- Baseline from file: opens a file selector popup, enabling you to load an existing CSV file
  to perform analysis on.
- Sample from file: does the exact same thing as the Baseline from file button.
- Q/C Test: runs a quality control test on the second sweep of the data. Produces hyperbolic,
  parabolic, moving mean, and linear approximations of the data curve, and generates a score
  based on the calculated parameters of all approximations. Plots results that can be saved as
  PNGs. Compares the most recently gathered baseline with the most recently gathered sample.
- Calculate Dirac Shift: calculates the absolute dirac shift between the sample and baseline.
  Requires both a sample and a baseline to have been run. Plots second sweep of both sample
  and baseline.

To exit, close the window. This will also close the spawned Windows command prompt window.
"""