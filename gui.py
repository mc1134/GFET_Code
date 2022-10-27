import tkinter
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def main(): # main method for running the gui

	def _quit():
		window_root.quit()
		window_root.destroy()

	def _plot():
		fig = Figure(figsize = (5, 5), dpi = 100)
		y = [i**2 for i in range(101)]
		plot1 = fig.add_subplot(111).plot(y)
		canvas = FigureCanvasTkAgg(fig, frame_plot)
		canvas._tkcanvas.grid(row = 3, column = 0)
		prompt_str.set(np.mean(y))
		feedback_str.set("Plotted y=x**2 for x in 0..100")

	def connect_action():
		feedback_str.set("Connect action not implemented yet.")

	def baseline_action():
		# does same thing as sample - probably runs curvefitting
		# steps
		# 1: check connection
		# 2: if connection, begin collecting data
		# 3: while collecting data, prompt user for file name (auto-generated one given if user inputs no name) (BASELINE_RAW_DATA_{TIMESTAMP}.csv)
		# 4: once file name given, csv file is saved to chosen (directory?)
		# 5: run the splitz function and give feedback to the user on its progress (because this step a long time)
		# 6: plot the raw data
		feedback_str.set("Baseline action not implemented yet.")

	def sample_action():
		# see baseline_action
		_plot()

	def close_action():
		_quit()

	def qc_action():
		# run curvefitting.py line 51+
		# plot parabolic, hyperbolic, and linear approximations
		# show text for the moving average approximation
		feedback_str.set("Q/C Test action not implemented yet.")

	def results_action():
		# run sweepmean2: this calculates dirac_shift (difference in average minima)
		# refere to Main script and Process_new_min script
		feedback_str.set("Results action not implemented yet.")

	def export_action():
		# remove for now since we are already saving csvs after baseline and sample actions and there are no other csvs to save
		feedback_str.set("Export CSV action not implemented yet.")

	window_root = tkinter.Tk()
	window_root.title("QC and Data Analytics GUI")
	window_root.geometry("800x600")

	window_root.grid_rowconfigure(0)
	window_root.grid_rowconfigure(1)
	window_root.grid_rowconfigure(2)
	window_root.grid_columnconfigure(0)

	prompt_str = tkinter.DoubleVar() # defining a tkinter variable that stores the dirac voltage so that it can be updated in real time
	feedback_str = tkinter.StringVar()
	feedback_str.set("This is the temporary label for displaying button feedback information.")

	frame_controls = tkinter.Frame(window_root, background = "Green") # frame for buttons etc.
	frame_prompt = tkinter.Frame(window_root, background = "Blue") # frame for displaying prompt
	frame_plot = tkinter.Frame(window_root, background = "Red") # frame for the plot

	frame_controls.grid(row = 0, column = 0)
	frame_prompt.grid(row = 1, column = 0)
	frame_plot.grid(row = 2, column = 0)

	ttk.Button(frame_controls, text = "Connect", command = connect_action).grid(row = 0, column = 0)
	ttk.Button(frame_controls, text = "Baseline", command = baseline_action).grid(row = 0, column = 1)
	ttk.Button(frame_controls, text = "Sample", command = sample_action).grid(row = 0, column = 2)
	ttk.Button(frame_controls, text = "Close", command = close_action).grid(row = 0, column = 3)

	ttk.Button(frame_controls, text = "Q/C Test", command = qc_action).grid(row = 1, column = 0)
	ttk.Button(frame_controls, text = "Results", command = results_action).grid(row = 1, column = 1)
	ttk.Button(frame_controls, text = "Export CSV", command = export_action).grid(row = 1, column = 2)

	ttk.Label(frame_prompt, textvariable = prompt_str).grid(row = 0, column = 0)

	ttk.Label(frame_prompt, textvariable = feedback_str).grid(row = 1, column = 0)

	window_root.mainloop()

	return "Done"


# TODO:
# add "disconnect" button - in row 0 with "connect" button
# when "disconnected" give some kind of feedback
# if "results" button pressed and no sample, but baseline has been set, 