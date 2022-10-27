import tkinter
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize

import csv
from splitz_new_opt import splitz_new_opt
import time

import matlab_helpers
import helperfuncs

def main(): # main method for running the gui

	def plot_qc_approximations(xdata, ydata, hyperbolic_fit, parabolic_fit, linear_fit):
		fig = Figure(figsize = (5, 5), dpi = 100)
		plot1 = fig.add_subplot(111).plot(xdata, ydata)
		canvas = FigureCanvasTkAgg(fig, frame_plot)
		canvas._tkcanvas.grid(row = 3, column = 0)
		prompt_str.set(np.mean(y))
		feedback_str.set("Plotted y=x**2 for x in 0..100")

	def connect_action():
		feedback_str.set("Connect action not implemented yet.")

	def disconnect_action():
		feedback_str.set("Disconnect action not implemented yet.")

	def baseline_action():
		# does same thing as sample - probably runs curvefitting
		# steps
		# 1: check connection
		# 2: if connection, begin collecting data
		# 3: while collecting data, prompt user for file name (auto-generated one given if user inputs no name) (BASELINE_RAW_DATA_{TIMESTAMP}.csv)
		# 4: once file name given, csv file is saved to chosen (directory?)
		# 5: run the splitz function and give feedback to the user on its progress (because this step a long time)
		# 6: plot the raw data
		feedback_str.set("Baseline action not implemented yet. Currently just reads CSV data and puts that into graph form")
		file = "125_02_b1_SAMPLING_RAW_DATA.csv" # filepath + filename + fileext

		print_debug(f"Opening file {file}")
		Base = []
		with open(file) as csvfile:
		    csvbuffer = csv.reader(csvfile, delimiter=',', quotechar='"')
		    for row in csvbuffer: # filter out only the fifth and sixth columns
		        Base += [row[4:6]]
		"""format of Base, assuming CSV is proper. will be formatted like JSON
		[
		    ['Gate Voltage', 'Ids'],
		    ['-0.12345', '6.789e-05'],
		    ['0.2468', '-1.3579e-02'],
		    ...
		]
		"""
		# need to convert all read data to numeric
		Base = [[float(row[0]), float(row[1])] for row in Base[1:]] # filter out first row which is headers
		print_debug(f"{len(Base)} rows read.")

		print_debug("Running splitz_new_opt")
		fx, bx = splitz_new_opt(Base) # Optimized splitz function for any length
		# with open("fx.txt", "w") as f:
		#     f.write(str(fx))
		# with open("bx.txt", "w") as f:
		#     f.write(str(bx))
		# exit()
		print_debug("Finished running splitz_new_opt")

	def sample_action():
		# see baseline_action
		feedback_str.set("Sample action not implemented yet.")

	def close_action():
		window_root.quit()
		window_root.destroy()

	def qc_action():
		# run curvefitting.py line 51+
		# plot parabolic, hyperbolic, and linear approximations
		# show text for the moving average approximation
		sweep_num = 2
		x = [obj[0] for obj in fx[sweep_num]] # voltages
		y = [obj[1] for obj in fx[sweep_num]] # ids
		xn = [item / max(x) for item in x] # normalized x
		yn = [item / max(y) for item in y] # normalized y

		# Parabolic Fit
		print_debug("Generating parabolic fit")
		parab = lambda b, x: (((x-b[0])**2/4)*b[2]) + b[1] # Generalised Hyperbola
		NRCFp = lambda b: np.linalg.norm(yn - parab(b, xn)) # Residual Norm Cost Function
		B0p = [1, 1, 1] # initial search point for fminsearch
		Bp = scipy.optimize.fmin(func = NRCFp, x0 = B0p)

		# Hype fit with the fit function from curve fitting tool box this works
		# Fit: 'hyperbola bad data'.
		#[xData, yData] = prepareCurveData( xn, yn ); # may make matlab helper subroutine
		# for now will just check if lengths are the same and all data is numeric
		check_curve_data = []
		if len(xn) != len(yn):
		    check_curve_data += [f"Data lists do not have same number of elements: len(xn) is {len(xn)}; len(yn) is {len(yn)}."]
		if not all([all([type(item) is float for item in xn]), all([type(item) is float for item in yn])]):
		    check_curve_data += [f"Data lists must be entirely numeric."]
		if len(check_curve_data) > 0:
		    print("Curve data is not proper.\n" + "\n".join(check_curve_data))
		    exit()

		# Set up fittype and options.
		"""ft = fittype( 'sqrt((((x-h).^2)./(a.^2)+1).*(b.^2))+c', 'independent', 'x', 'dependent', 'y' )
		opts = fitoptions( 'Method', 'NonlinearLeastSquares' )
		opts.Display = 'Off'
		opts.StartPoint = [0.890903252535798 0.959291425205444 0.547215529963803 0.138624442828679]
		# Fit model to data.
		[fitresult, gof(11)] = fit( xData, yData, ft, opts )"""

		# defining functions for the least squares fit
		def ft_model(fun_params, x): # this will evaluate the fit function
		    a, b, c, h = fun_params[0], fun_params[1], fun_params[2], fun_params[3]
		    return np.sqrt(b**2 * ((x-h)**2/(a**2) + 1)) + c
		def residual_fun(model_params): # this evaluates the residuals of the function ft_model
		    return yn - ft_model(model_params, xn)

		# fit data to model
		print_debug("Fitting data to model")
		start_point = [0.890903252535798, 0.959291425205444, 0.547215529963803, 0.138624442828679]
		fit_result = scipy.optimize.least_squares(residual_fun, start_point) # does not return goodness of fit data

		# Plot fit with data figure 1 Plots are probably not necessary for general
		# figure( 'Name', 'hpyerbola bad data' );
		print_debug("Plotting data and model")
		plt.plot(xn, yn, label="Data")
		plt.plot(xn, ft_model(fit_result.x, xn), label="Fit")
		plt.legend()
		plt.show()
		# h = plot( fitresult, xn, yn );
		# legend( h, 'yn vs. xn', 'hyperbola bad data', 'Location', 'NorthEast', 'Interpreter', 'none' );
		# % Label axes
		# xlabel( 'xn', 'Interpreter', 'none' );
		# ylabel( 'yn', 'Interpreter', 'none' );
		# grid on

		# moving average filter and noise tests calculate max difference and average
		fil = matlab_helpers.movmean(yn, 3)
		maxn = max([abs(fil[i]-yn[i]) for i in range(len(yn))])
		avgn = np.mean([abs(fil[i]-yn[i]) for i in range(len(yn))])

		# Split at minima and calculate slope on either side
		val = min(yn)
		xmin = yn.index(val)
		xmin = min(max(xmin, 2), len(yn)-2)
		minx = xn[xmin]

		bl = np.polynomial.polynomial.polyfit(xn[1:xmin], yn[1:xmin], 1) # returns numpy.nd_array([c_1, c_2]) for y = c_1 + c_2 * x
		br = np.polynomial.polynomial.polyfit(xn[xmin:], yn[xmin:], 1)

		lsl = bl[0]
		rsl = br[0]
		plot_qc_approximations()
		#feedback_str.set("Q/C Test action not implemented yet.")

	def results_action():
		# run sweepmean2: this calculates dirac_shift (difference in average minima)
		# refere to Main script and Process_new_min script
		feedback_str.set("Results action not implemented yet.")

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
	ttk.Button(frame_controls, text = "Disconnect", command = disconnect_action).grid(row = 0, column = 1)
	ttk.Button(frame_controls, text = "Close", command = close_action).grid(row = 0, column = 2)

	ttk.Button(frame_controls, text = "Baseline", command = baseline_action).grid(row = 1, column = 0)
	ttk.Button(frame_controls, text = "Sample", command = sample_action).grid(row = 1, column = 1)

	ttk.Button(frame_controls, text = "Q/C Test", command = qc_action).grid(row = 2, column = 0)
	ttk.Button(frame_controls, text = "Results", command = results_action).grid(row = 2, column = 1)

	ttk.Label(frame_prompt, textvariable = prompt_str).grid(row = 0, column = 0)

	ttk.Label(frame_prompt, textvariable = feedback_str).grid(row = 1, column = 0)

	window_root.mainloop()

	return "Done"


# TODO:
# add "disconnect" button - in row 0 with "connect" button
# when "disconnected" give some kind of feedback
# if "results" button pressed and no sample, but baseline has been set, 