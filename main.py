from gui import GUI


def main():
	GUI()
	print("Done.")

if __name__ == "__main__":
	main()


# enhancement: export json of the qc parameters
# enhancement: add title text to the plots
# as of now, GUI sends user input to microcontroller, and microcontroller reads data
# future: when user interacts with microcontroller, gui should listen for that; need compatibility
	# add feedback text when buttons are pressed: "button 1/2/3 pressed"
# try to implement baseline and sample buttons to be real time - show this real time data in the plot
# try to implement connect and disconnect buttons

# keep the behavior of the lights the same if possible
	# flashing blue: baseline being taken
	# flashing red: sample being taken
	# amber / red / green: power connected
	# amber: idling
	# amber + green: ready to test
	# amber + purple + green + blue/red: turned on / connected to ip
	# might devise my own color scheme - tyler etc. don't really mind or have a specific color scheme

# results button calculates the dirac voltage shift (in millivolts) (taking the absolute difference between the average of the minima of the sample and baseline curves) and plot a baseline and sample (2nd or 3rd forw) curve on the same plot

# currently hard codes the ip addresses; the old program currently selects the first detected ip address; eventually will implement a drop down with the detected list of ip addresses and you choose one then click connect

# TODO 11/18:
# reformat the driver program so that it contains the bare minimum of what we want to test on Monday
# refactor the sampleThreading method

"""
to discuss
	future maintenance of this project: github or google drive?
	would it be ok to refactor the code so that it essentially calls the existing mcp_driver code (which requires you to press buttons on the microcontroller)? this would avoid having to decode the mcp_driver code which has many mysterious definitions
		two paths:
			on the GUI, press the "baseline" or "sample" buttons. this initiates a script on the microcontroller to gather data and send the data file back to the user's computer
			on the GUI, press the "baseline" or "sample" buttons. this displays messages similar to those on the ssh_to_covid_board program, instructing the user to place samples in the microcontroller, then gathering baseline/sample and sending data files to the user
"""