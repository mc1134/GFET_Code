from gui import GUI


def main():
	GUI()
	print("Done.")

if __name__ == "__main__":
	main()

"""
to discuss
	future maintenance of this project: github or google drive?
	would it be ok to refactor the code so that it essentially calls the existing mcp_driver code (which requires you to press buttons on the microcontroller)? this would avoid having to decode the mcp_driver code which has many mysterious definitions
		two paths:
			on the GUI, press the "baseline" or "sample" buttons. this initiates a script on the microcontroller to gather data and send the data file back to the user's computer
			on the GUI, press the "baseline" or "sample" buttons. this displays messages similar to those on the ssh_to_covid_board program, instructing the user to place samples in the microcontroller, then gathering baseline/sample and sending data files to the user
"""

# currently hard codes the ip addresses; the old program currently selects the first detected ip address; eventually will implement a drop down with the detected list of ip addresses and you choose one then click connect
# add axes to the graphs!!!
# driver program does not exit after generating raw data file so it needs to be remotely terminated from the gui program
# enhancement: export json of the qc parameters
# enhancement: add title text to the plots
# user input for the IP address and file name

# put some feedback to the terminal when and after connecting successfully
# imports for microcontroller: openpyxl
#   new devices to come soon
# add buttons called "baseline from file" and "sample from file"
# bad data from microcontroller might mess up the quality control algorithm
#   solved by adding buttons to read from file (after user separately cleans file)
#   data picked was the last sweep when it should have been a "middle" sweep