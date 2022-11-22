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

import matlab_helpers as matlab
import helperfuncs as helpers

class GUI:
    """
    Class that defines a GUI. Attributes:
        window_root: Defines the root window. Top level container that contains everything else.
        frame_controls: Defines the frame for buttons. Placed at row 0.
        frame_prompt: Defines the frame for the prompt. Placed at row 1.
        frame_plot: Defines the frame for the embedded matplotlib plots. Placed at row 2.
        prompt_str: Text variable for displaying useful information, such as the dirac voltage.
        feedback_str: Text variable that is updated when a button is pressed.
        fx, bx: The forward and backward arrays of voltage vs Ids.
    """
    def __init__(self):
        self.window_root = tkinter.Tk()
        self.window_root.title("QC and Data Analytics GUI")
        self.window_root.geometry("1500x640")

        self.window_root.grid_rowconfigure(0)
        self.window_root.grid_rowconfigure(1)
        self.window_root.grid_rowconfigure(2)
        self.window_root.grid_columnconfigure(0)

        self.prompt_str = tkinter.StringVar() # TODO currently unused
        self.feedback_str = tkinter.StringVar()
        self.feedback_str.set("This is the temporary label for displaying button feedback information.")

        self.frame_controls = tkinter.Frame(self.window_root, background = "Green") # frame for buttons etc.
        self.frame_prompt = tkinter.Frame(self.window_root, background = "Blue") # frame for displaying prompt
        self.frame_plot = tkinter.Frame(self.window_root, background = "Red") # frame for the plot

        self.frame_controls.grid(row = 0, column = 0)
        self.frame_prompt.grid(row = 1, column = 0)
        self.frame_plot.grid(row = 2, column = 0)

        ttk.Button(self.frame_controls, text = "Connect", command = self.connect_action).grid(row = 0, column = 0)
        ttk.Button(self.frame_controls, text = "Disconnect", command = self.disconnect_action).grid(row = 0, column = 1)
        ttk.Button(self.frame_controls, text = "Close", command = self.close_action).grid(row = 0, column = 2)

        ttk.Button(self.frame_controls, text = "Baseline", command = self.baseline_action).grid(row = 1, column = 0)
        ttk.Button(self.frame_controls, text = "Sample", command = self.sample_action).grid(row = 1, column = 1)

        ttk.Button(self.frame_controls, text = "Q/C Test", command = self.qc_action).grid(row = 2, column = 0)
        ttk.Button(self.frame_controls, text = "Results", command = self.results_action).grid(row = 2, column = 1)

        ttk.Label(self.frame_prompt, textvariable = self.prompt_str).grid(row = 0, column = 0)

        ttk.Label(self.frame_prompt, textvariable = self.feedback_str).grid(row = 1, column = 0)

        self.fig = None
        self.initialize_plots()

        self.window_root.mainloop()

    ##### Plots #####

    def initialize_plots(self): # this function's sole purpose is to set the window controls in the right place
        self.empty_fig = Figure(figsize = (15, 5), layout = "tight")
        empty_canvas = FigureCanvasTkAgg(self.empty_fig, self.frame_plot)
        empty_canvas._tkcanvas.grid(row = 3, column = 0)

    def plot_qc_approximations(self, xdata, ydata, hyperbolic_fit, parabolic_fit, bl, br):
        self.fig = Figure(figsize = (15, 5), dpi = 100, layout = "tight")
        hyperbolic_plot = self.fig.add_subplot(1, 3, 1)
        hyperbolic_plot.plot(xdata, ydata, label="Data")
        hyperbolic_plot.plot(xdata, helpers.hyp_model(hyperbolic_fit, xdata), label="Hyperbolic fit")
        hyperbolic_plot.legend()
        #hyperbolic_plot.title("Hyperbolic data and model") # TODO find a way to add titles to the plots
        parabolic_plot = self.fig.add_subplot(1, 3, 2)
        parabolic_plot.plot(xdata, ydata, label="Data")
        parabolic_plot.plot(xdata, helpers.par_model(parabolic_fit, xdata), label="Parabolic fit")
        parabolic_plot.legend()
        #parabolic_plot.title("Parabolic fit")
        linear_plot = self.fig.add_subplot(1, 3, 3)
        linear_plot.plot(xdata, ydata, label="Data")
        linear_plot.plot(xdata, helpers.lin_model(bl, xdata), label="Left linear fit")
        linear_plot.plot(xdata, helpers.lin_model(br, xdata), label="Right linear fit")
        linear_plot.legend()
        #linear_plot.title("Linear data and model")
        canvas = FigureCanvasTkAgg(self.fig, self.frame_plot)
        canvas._tkcanvas.grid(row = 3, column = 0)
        self.feedback_str.set("Plotted the hyperbolic fit, parabolic fit, and linear fits with respect to the data.")

    def plot_to_window(self, xdata, ydata, hyperbolic_fit, parabolic_fit, bl, br):
        helpers.print_debug("Plotting hyperbolic data and model")
        plt.plot(xdata, ydata, label="Data")
        plt.plot(xdata, helpers.hyp_model(hyperbolic_fit.x, xdata), label="Hyperbolic fit")
        plt.legend()
        plt.title("Hyperbolic data and model")
        plt.show()
        helpers.print_debug("Plotting parabolic data and model")
        plt.plot(xdata, ydata, label="Data")
        plt.plot(xdata, helpers.par_model(parabolic_fit, xdata), label="Parabolic fit")
        plt.legend()
        plt.title("Parabolic data and model")
        plt.show()
        helpers.print_debug("Plotting linear data and model")
        plt.plot(xdata, ydata, label="Data")
        plt.plot(xdata, helpers.lin_model(bl, xdata), label="Left linear fit")
        plt.plot(xdata, helpers.lin_model(br, xdata), label="Right linear fit")
        plt.legend()
        plt.title("Linear data and model")
        plt.show()

    ##### Button actions #####

    def connect_action(self):
        self.feedback_str.set("Connect action not implemented yet.")

    def disconnect_action(self):
        self.feedback_str.set("Disconnect action not implemented yet.")

    def baseline_action(self):
        # does same thing as sample - probably runs curvefitting
        # steps
        # 1: check connection
        # 2: if connection, begin collecting data
        # 3: while collecting data, prompt user for file name (auto-generated one given if user inputs no name) (BASELINE_RAW_DATA_{TIMESTAMP}.csv)
        # 4: once file name given, csv file is saved to chosen (directory?)
        # 5: run the splitz function and give feedback to the user on its progress (because this step a long time)
        # 6: plot the raw data
        self.feedback_str.set("Baseline action not implemented yet. Currently just reads CSV data and puts that into graph form")
        file = "124_07_b2_SAMPLING_RAW_DATA.csv" # filepath + filename + fileext

        helpers.print_debug(f"Opening file {file}")
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
        helpers.print_debug(f"{len(Base)} rows read.")

        helpers.print_debug("Running splitz_new_opt")
        self.fx, self.bx = splitz_new_opt(Base) # Optimized splitz function for any length
        helpers.print_debug("Finished running splitz_new_opt")

    def sample_action(self):
        # see baseline_action
        self.feedback_str.set("Sample action not implemented yet.")

    def close_action(self):
        self.feedback_str.set("Closing window...")
        self.window_root.quit()
        self.window_root.destroy()

    def qc_action(self):
        # run curvefitting.py line 51+
        # plot parabolic, hyperbolic, and linear approximations
        # show text for the moving average approximation
        self.feedback_str.set("Running rudimentary quality control testing; generating fits")
        sweep_num = 1 # run QC test on the second sweep
        x = [obj[0] for obj in self.fx[sweep_num]] # voltages
        y = [obj[1] for obj in self.fx[sweep_num]] # ids
        xn = [item / max(x) for item in x] # normalized x
        yn = [item / max(y) for item in y] # normalized y

        # check curve data
        check_curve_data = []
        if len(xn) != len(yn):
            check_curve_data += [f"Data lists do not have same number of elements: len(xn) is {len(xn)}; len(yn) is {len(yn)}."]
        if not all([all([type(item) is float for item in xn]), all([type(item) is float for item in yn])]):
            check_curve_data += [f"Data lists must be entirely numeric."]
        if len(check_curve_data) > 0:
            print("Curve data is not proper.\n" + "\n".join(check_curve_data))
            return

        # Parabolic fit
        helpers.print_debug("Generating parabolic fit")
        B0p = [1, 1, 1] # initial search point for fminsearch
        parabolic_fit = scipy.optimize.fmin(func = helpers.par_residuals, x0 = B0p, args = (xn, yn))

        # Hyperbolic fit
        # fit data to model
        helpers.print_debug("Fitting data to model")
        start_point = [0.890903252535798, 0.959291425205444, 0.547215529963803, 0.138624442828679]
        hyperbolic_fit = scipy.optimize.least_squares(helpers.hyp_residuals, x0 = start_point, args = (xn, yn)) # does not return goodness of fit data

        # Moving average filter and noise tests calculate max difference and average
        fil = matlab.movmean(yn, 3)
        maxn = max([abs(fil[i]-yn[i]) for i in range(len(yn))])
        avgn = np.mean([abs(fil[i]-yn[i]) for i in range(len(yn))])
        self.prompt_str.set(f"Moving mean maximum: {maxn}; Moving mean average: {avgn}")

        # Linear fit: split at minima and calculate slope on either side
        val = min(yn)
        xmin = min(max(yn.index(val), 2), len(yn) - 2)
        minx = xn[xmin]
        bl = np.polynomial.polynomial.polyfit(xn[:xmin], yn[:xmin], 1) # returns numpy.nd_array([c_1, c_2]) for y = c_1 * x + c_2
        br = np.polynomial.polynomial.polyfit(xn[xmin:], yn[xmin:], 1)
        print("left linear fit:", bl, "right linear fit:", br)
        lsl = bl[0]
        rsl = br[0]
        # defining functions for linear fit

        sco, message = helpers.score(hyperbolic_fit.x, parabolic_fit, {"maxn": maxn, "avgn": avgn}, {"lsl": lsl, "rsl": rsl})
        self.feedback_str.set(f"Score: {sco}\n{message}")

        self.plot_qc_approximations(xn, yn, hyperbolic_fit.x, parabolic_fit, bl, br)
        #self.plot_to_window(xn, yn, hyperbolic_fit.x, parabolic_fit, bl, br)
        #self.feedback_str.set("Q/C Test action not implemented yet.")

    def results_action(self):
        # run sweepmean2: this calculates dirac_shift (difference in average minima)
        # refer to Main script and Process_new_min script
        self.feedback_str.set("Results action not implemented yet.")


# find a text field that allows highlighting/copying (for copying movmean parameters)