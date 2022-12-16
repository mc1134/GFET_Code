import tkinter
from tkinter import ttk, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize

import csv
from splitz_new_opt import splitz_new_opt
import time
import os
import json

import matlab_helpers as matlab
import helperfuncs as helpers
from ssh_to_device import ssh_to_device
import constants as CONSTANTS

class GUI:
    """
    Class that defines a GUI. Attributes:
        window_root: Defines the root window. Top level container that contains everything else.
        frame_controls: Defines the frame for buttons. Placed at row 0.
        frame_prompt: Defines the frame for the prompt. Placed at row 1.
        frame_plot: Defines the frame for the embedded matplotlib plots. Placed at row 2.
        feedback_str: Text variable that is updated when a button is pressed.
        fx, bx: The forward and backward arrays of voltage vs Ids.
    """
    def __init__(self):
        # initializing main window
        self.window_root = tkinter.Tk()
        self.window_root.title("QC and Data Analytics GUI")
        self.window_root.geometry("1500x640")

        # configuring valid window grid positions
        self.window_root.grid_rowconfigure(0)
        self.window_root.grid_rowconfigure(1)
        self.window_root.grid_rowconfigure(2)
        self.window_root.grid_columnconfigure(0)

        # configuring textvariables for GUI
        self.qc_score_str = tkinter.StringVar()
        self.qc_score_str.set("No Q/C Test run.")
        self.abs_dirac_shift = tkinter.StringVar()
        self.abs_dirac_shift.set("")
        self.feedback_str = tkinter.StringVar()
        self.feedback_str.set("This is the temporary label for displaying button feedback information.")
        self.IP = tkinter.StringVar()
        self.IP.set("10.0.0.0")

        # defining frames
        self.frame_controls = tkinter.Frame(self.window_root, background = "Green") # frame for buttons etc.
        self.frame_prompt = tkinter.Frame(self.window_root, background = "Blue") # frame for displaying prompt
        self.frame_plot = tkinter.Frame(self.window_root, background = "Red") # frame for the plot

        # defining frame positioning
        self.frame_controls.grid(row = 0, column = 0)
        self.frame_prompt.grid(row = 1, column = 0)
        self.frame_plot.grid(row = 2, column = 0)

        # connection controls
        ttk.Label(self.frame_controls, text = "Enter IP Address").grid(row = 0, column = 0)
        self.IP_entry = ttk.Entry(self.frame_controls, textvariable = self.IP)
        self.IP_entry.grid(row = 0, column = 1)
        ttk.Button(self.frame_controls, text = "Connect", command = self.connect_action).grid(row = 0, column = 2)
        ttk.Button(self.frame_controls, text = "Disconnect", command = self.disconnect_action).grid(row = 0, column = 3)
        #ttk.Button(self.frame_controls, text = "Close", command = self.close_action).grid(row = 0, column = 4)

        # file name entry
        ttk.Label(self.frame_controls, text = "Enter file name to be used in baseline/sampling data collection").grid(row = 1, column = 0)
        self.filename_entry = ttk.Entry(self.frame_controls, text = helpers.get_time())
        self.filename_entry.grid(row = 1, column = 1)

        # baseline controls
        ttk.Button(self.frame_controls, text = "Baseline", command = self.baseline_action).grid(row = 2, column = 0)
        ttk.Button(self.frame_controls, text = "Baseline from file", command = self.baseline_from_file_action).grid(row = 2, column = 1)

        # sample controls
        ttk.Button(self.frame_controls, text = "Sample", command = self.sample_action).grid(row = 3, column = 0)
        ttk.Button(self.frame_controls, text = "Sample from file", command = self.sample_from_file_action).grid(row = 3, column = 1)

        # analytics controls
        ttk.Button(self.frame_controls, text = "Q/C Test", command = self.qc_action).grid(row = 4, column = 0)
        ttk.Label(self.frame_controls, text = "Q/C Results: ").grid(row = 4, column = 1)
        ttk.Label(self.frame_controls, textvariable = self.qc_score_str).grid(row = 4, column = 2)
        ttk.Button(self.frame_controls, text = "Calculate Dirac Shift", command = self.results_action).grid(row = 5, column = 0)
        ttk.Label(self.frame_controls, text = "Absolute Dirac Shift: ").grid(row = 5, column = 1)
        ttk.Label(self.frame_controls, textvariable = self.abs_dirac_shift).grid(row = 5, column = 2)

        # TEST BUTTON
        ttk.Button(self.frame_controls, text = "TEST BUTTON", command = self.test_button_action).grid(row = 5, column = 0)

        # text fields
        ttk.Label(self.frame_prompt, text = "Feedback String:").grid(row = 1, column = 0)
        ttk.Label(self.frame_prompt, textvariable = self.feedback_str).grid(row = 1, column = 1)

        # for embedding matplotlib plots into the GUI
        self.fig = None
        self.empty_fig = None
        self.initialize_plots()

        # ssh client
        self.ssh_client = ssh_to_device()

        # strings for firmware file locations
        self.local_firmware = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONSTANTS.LOCAL_FIRMWARE_FILE_NAME)
        self.remote_firmware = CONSTANTS.REMOTE_FIRMWARE_PATH

        # analytics variables
        self.fx = None
        self.baseline_dirac = None
        self.sampling_dirac = None

        # variables for maintaining state of additional tkinter widgets
        self.popup_entry = None

        self.window_root.mainloop()

    def test_button_action(self):
        self.feedback_str.set("Test button pressed")
        def popup_action():
            self.IP = self.IP_entry.get()
        self.text_popup("title of popup", "prompt", popup_action)
        filename = filedialog.askopenfilename()
        self.feedback_str.set(f"File name: {filename}")

    ##### Additional TK components #####

    def text_popup(self, title, prompt, button_action):
        window_popup = tkinter.Tk()
        window_popup.geometry("300x100")
        window_popup.title(title)
        ttk.Label(window_popup, text = prompt).place(x = 0, y = 0)
        self.popup_entry = ttk.Entry(window_popup, width = 20)
        self.popup_entry.place(x = 0, y = 20)
        def close_popup():
            button_action()
            window_popup.quit()
            window_popup.destroy()
        ttk.Button(window_popup, text = "Submit", command = close_popup).place(x = 0, y = 40)
        window_popup.mainloop()

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

    def plot_results(self, x_baseline, y_baseline, x_sampling, y_sampling):
        helpers.print_debug("Plotting result graph")
        self.fig = Figure(figsize = (15, 5), dpi = 100, layout = "tight")
        result_plot = self.fig.add_subplot(1, 3, 2)
        result_plot.plot(x_baseline, y_baseline, label="Baseline")
        result_plot.plot(x_sampling, y_sampling, label="Sampling")
        result_plot.legend()
        #result_plot.title("Plot of second forward sweeps for baseline and sample data")
        canvas = FigureCanvasTkAgg(self.fig, self.frame_plot)
        canvas._tkcanvas.grid(row = 3, column = 0)

    ##### File operations #####

    def select_file(self):
        filename = filedialog.askopenfilename()
        helpers.print_debug(f"Selected file: {filename}")
        return filename

    def read_raw_data(self, file):
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

    ##### Button actions #####

    def connect_action(self):
        self.IP = self.IP_entry.get()
        if not helpers.validate_ip(self.IP):
            self.feedback_str.set(f'The IP address "{self.IP}" is not valid.')
            return
        helpers.print_debug(f"Connecting to device ({self.IP})...")
        if not self.ssh_client.connect(self.IP, CONSTANTS.PORT):
            self.feedback_str.set(f"Could not connect to {self.IP}.")
            return
        self.feedback_str.set(f"Connected to {self.IP}.")
        helpers.print_debug("Uploading firmware to device...")
        if not self.ssh_client.upload_firmware(self.local_firmware, self.remote_firmware):
            self.feedback_str.set("Could not upload firmware.")
            return
        self.feedback_str.set("Connect action completed.")
        #self.feedback_str.set("Connect action not implemented yet.")

    def disconnect_action(self):
        self.ssh_client.disconnect()
        self.feedback_str.set("Disconnected from SSH device.")
        #self.feedback_str.set("Disconnect action not implemented yet.")

    def baseline_action(self):
        if not self.ssh_client.connected:
            self.feedback_str.set('Device is not connected. Please press the "Connect" button.')
            return
        filename, mode = self.filename_entry.get(), "BASELINE"
        if filename == "":
            self.feedback_str.set("Cannot run baseline using empty file name.")
            return
        self.ssh_client.collect_data(self.remote_firmware, filename, mode)
        local_baseline_raw_data_file = f"data/{filename}_{mode}_RAW_DATA.csv"
        self.feedback_str.set(f"Using file {local_baseline_raw_data_file}")
        downloaded, time_elapsed, start_time = False, 0, time.time()
        remote_baseline_raw_data_file = f"/home/root/{filename}_{mode}_RAW_DATA.csv"
        while not downloaded and time_elapsed < CONSTANTS.MAX_DOWNLOAD_WAIT_TIME:
            helpers.print_debug(f"Waiting for baseline data file from device ({time_elapsed} seconds elapsed)...")
            time.sleep(CONSTANTS.DOWNLOAD_DELAY - (time.time() - start_time) % CONSTANTS.DOWNLOAD_DELAY)
            downloaded = self.ssh_client.download_file(remote_baseline_raw_data_file, local_baseline_raw_data_file)
            time_elapsed += CONSTANTS.DOWNLOAD_DELAY
        if not downloaded:
            self.feedback_str.set(f"Maximum wait time {CONSTANTS.MAX_DOWNLOAD_WAIT_TIME} reached. Baseline data file was not downloaded.")
            return
        else:
            helpers.print_debug(f"Downloaded file in {time.time() - start_time} seconds. Removing from device...")
            self.ssh_client.delete_file(remote_baseline_raw_data_file)
        self.read_raw_data(local_baseline_raw_data_file)
        self.baseline_fx = self.fx
        mina, mins, jmin = helpers.sweepmean(self.fx)
        self.baseline_dirac = {"mean": mina, "std": mins, "data": jmin}

    def sample_action(self):
        if not self.ssh_client.connected:
            self.feedback_str.set('Device is not connected. Please press the "Connect" button.')
            return
        if self.baseline_dirac is None:
            self.feedback_str.set("Please run a baseline first")
            return
        filename, mode = self.filename_entry.get(), "SAMPLING"
        if filename == "":
            self.feedback_str.set("Cannot run sampling using empty file name.")
            return
        self.ssh_client.collect_data(self.remote_firmware, filename, mode)
        local_sampling_raw_data_file = f"data/{filename}_{mode}_RAW_DATA.csv"
        self.feedback_str.set(f"Using file {local_sampling_raw_data_file}")
        downloaded, time_elapsed, start_time = False, 0, time.time()
        remote_sampling_raw_data_file = f"/home/root/{filename}_{mode}_RAW_DATA.csv"
        while not downloaded and time_elapsed < CONSTANTS.MAX_DOWNLOAD_WAIT_TIME:
            helpers.print_debug(f"Waiting for sampling data file from device ({time_elapsed} seconds elapsed)...")
            time.sleep(CONSTANTS.DOWNLOAD_DELAY - (time.time() - start_time) % CONSTANTS.DOWNLOAD_DELAY)
            downloaded = self.ssh_client.download_file(remote_sampling_raw_data_file, local_sampling_raw_data_file)
            time_elapsed += CONSTANTS.DOWNLOAD_DELAY
        if not downloaded:
            self.feedback_str.set(f"Maximum wait time {CONSTANTS.MAX_DOWNLOAD_WAIT_TIME} reached. Sampling data file was not downloaded.")
            return
        else:
            helpers.print_debug(f"Downloaded file in {time.time() - start_time} seconds. Removing from device...")
            self.ssh_client.delete_file(remote_sampling_raw_data_file)
        self.read_raw_data(local_sampling_raw_data_file)
        self.sampling_fx = self.fx
        mina, mins, jmin = helpers.sweepmean(self.fx)
        self.sampling_dirac = {"mean": mina, "std": mins, "data": jmin}

    def baseline_from_file_action(self):
        self.feedback_str.set("Selecting file...")
        local_baseline_raw_data_file = self.select_file()
        try:
            self.read_raw_data(local_baseline_raw_data_file)
        except Exception as e:
            helpers.print_debug(e)
            self.feedback_str.set(f"Could not open file {local_baseline_raw_data_file}")
            return
        self.baseline_fx = self.fx
        mina, mins, jmin = helpers.sweepmean(self.fx)
        self.baseline_dirac = {"mean": mina, "std": mins, "data": jmin}
        self.feedback_str.set(f"Successfully loaded baseline file {local_baseline_raw_data_file}")

    def sample_from_file_action(self):
        self.feedback_str.set("Selecting file...")
        local_sampling_raw_data_file = self.select_file()
        try:
            self.read_raw_data(local_sampling_raw_data_file)
        except Exception as e:
            helpers.print_debug(e)
            self.feedback_str.set(f"Could not open file {local_sampling_raw_data_file}")
            return
        self.sampling_fx = self.fx
        mina, mins, jmin = helpers.sweepmean(self.fx)
        self.sampling_dirac = {"mean": mina, "std": mins, "data": jmin}
        self.feedback_str.set(f"Successfully loaded sampling file {local_sampling_raw_data_file}")

    def close_action(self): # currently unused. user can just click x button to close window
        self.feedback_str.set("Closing window...")
        self.window_root.quit()
        self.window_root.destroy()

    def qc_action(self):
        # run curvefitting.py line 51+
        # plot parabolic, hyperbolic, and linear approximations
        # show text for the moving average approximation
        if self.fx is None:
            self.feedback_str.set("No forward sweep array in memory. Please run a baseline or sample.")
            return
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

        # Linear fit: split at minima and calculate slope on either side
        val = min(yn)
        xmin = min(max(yn.index(val), 2), len(yn) - 2)
        minx = xn[xmin]
        bl = np.polynomial.polynomial.polyfit(xn[:xmin], yn[:xmin], 1) # returns numpy.nd_array([c_1, c_2]) for y = c_1 * x + c_2
        br = np.polynomial.polynomial.polyfit(xn[xmin:], yn[xmin:], 1)
        helpers.print_debug(f"left linear fit: {bl}; right linear fit: {br}")
        lsl = bl[1]
        rsl = br[1]
        # defining functions for linear fit

        score, message = helpers.score(hyperbolic_fit.x, parabolic_fit, {"maxn": maxn, "avgn": avgn}, {"lsl": lsl, "rsl": rsl})
        self.qc_score_str.set(f"Score: {score}\n{message}")
        helpers.print_debug(f"Score: {score}\n{message}")

        self.plot_qc_approximations(xn, yn, hyperbolic_fit.x, parabolic_fit, bl, br)
        #self.plot_to_window(xn, yn, hyperbolic_fit.x, parabolic_fit, bl, br)
        #self.feedback_str.set("Q/C Test action not implemented yet.")

        output_qc_parameters = {
            "hyperbolic fit": {
                "params": {
                    "a": hyperbolic_fit.x[0],
                    "b": hyperbolic_fit.x[1],
                    "c": hyperbolic_fit.x[2],
                    "h": hyperbolic_fit.x[3]
                },
                "model": "(b**2 * ((x - h)**2 / (a**2) + 1))**0.5 + c"
            },
            "parabolic fit": {
                "params": {
                    "a": parabolic_fit[0],
                    "b": parabolic_fit[1],
                    "c": parabolic_fit[2]
                },
                "model": "(((x - a)**2/4) * c) + b"
            },
            "linear fit": {
                "params": {
                    "left fit": {
                        "b": bl[0],
                        "m": bl[1]
                    },
                    "right fit": {
                        "b": br[0],
                        "m": br[1]
                    }
                },
                "model": "m * x + b"
            },
            "moving average filter fit": {
                "params": {
                    "moving mean maximum": maxn,
                    "moving mean average": avgn
                }
            },
            "score": {
                "score": score,
                "message": message
            }
        }
        with open(f"qc_params_{helpers.get_time()}.json", "w") as f:
            f.write(json.dumps(output_qc_parameters, indent = 4))

    def results_action(self):
        # run sweepmean2: this calculates dirac_shift (difference in average minima)
        # refer to Main script and Process_new_min script
        if self.baseline_dirac is None:
            self.feedback_str.set("Please run a baseline first.")
            return
        if self.sampling_dirac is None:
            self.feedback_str.set("Please run a sample first.")
            return
        dirac_shift = abs(self.baseline_dirac["mean"] - self.sampling_dirac["mean"])
        # plot second forward sweeps
        sweep_num = 2 # run QC test on the second sweep
        x_baseline = [obj[0] for obj in self.baseline_fx[sweep_num]]
        y_baseline = [obj[1] for obj in self.baseline_fx[sweep_num]]
        x_sampling = [obj[0] for obj in self.sampling_fx[sweep_num]]
        y_sampling = [obj[1] for obj in self.sampling_fx[sweep_num]]
        self.plot_results(x_baseline, y_baseline, x_sampling, y_sampling)
        self.feedback_str.set(f"Absolute dirac shift: {dirac_shift}")

        output_dirac_shift = {
            "sweep number": sweep_num + 1,
            "absolute dirac shift": dirac_shift
        }

        with open(f"dirac_shift_{helpers.get_time()}.json", "w") as f:
            f.write(json.dumps(output_dirac_shift, indent = 4))

