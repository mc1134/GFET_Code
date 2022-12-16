from gui import GUI


def main():
	GUI()
	print("Done.")

if __name__ == "__main__":
	main()


# next meeting after 12/15 is on 1/5 4pm


# HIGH PRIORITY
# ENHANCEMENT: imports for microcontroller: openpyxl
#   new devices to come soon
# BUG: data picked was the last sweep when it should have been a "middle" sweep when running analytics (qc/dirac)
# ENHANCEMENT: feedback while waiting for file when clicking baseline or sample buttons
# ENHANCEMENT: begin testing compiling the program into a single executable

# Medium priority
# ENHANCEMENT: implement a drop down with the detected list of ip addresses and you choose one then click connect
#   BUG: the first time "connect" is clicked, the IP address field gets wiped
# BUG: firmware program does not exit after generating raw data file so it needs to be remotely terminated from the gui program
#   solution 1: the GUI kills the process after starting it (using ps | grep maybe) DO THIS ONE
#   solution 2: write a standalone script that kills all running processes on the microcontroller
#   when running firmware program manually by SSHing into device, need to CTRL+C twice to exit
# ENHANCEMENT: remove csv file from remote after downloading

# Low priority
# ENHANCEMENT: add axes to graphs
# ENHANCEMENT: add title text to graphs
# ENHANCEMENT: put some feedback to the terminal when and after connecting successfully
# ENHANCEMENT: notify the user if the ssh connection breaks any time
# ENHANCEMENT: rename "samplingThread" to "data collection" etc. (NOT 'sampling' from BASELINE/SAMPLING)
# ENHANCEMENT: when writing results with results button, add filenames for both baseline and sample files used into the JSON output