import tkinter
from tkinter import ttk, filedialog
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
import ssh_to_device
import constants as CONSTANTS

class GUI:
    """
    Class that defines a GUI.
    """
    def __init__(self):
        # ssh client
        self.ssh_client = ssh_to_device.ssh_to_device()

        # initializing main window
        self.window_root = tkinter.Tk()
        self.window_root.title("QC and Data Analytics GUI")
        self.window_root.geometry("720x420")

        # configuring valid window grid positions
        self.window_root.grid_rowconfigure(0)
        self.window_root.grid_rowconfigure(1)
        self.window_root.grid_rowconfigure(2)
        self.window_root.grid_rowconfigure(3)
        self.window_root.grid_columnconfigure(0)

        # configuring textvariables for GUI
        self.feedback_str = tkinter.StringVar()
        self.feedback_str.set("This is the temporary label for displaying button feedback information.")
        self.IP = tkinter.StringVar()
        #self.IP.set("Querying IP addresses...")
        self.IP.set("10.0.0.0")

        # configuring text variables used by the Text widgets
        self.qc_score_str = "No Q/C Test run."
        self.abs_dirac_shift = "No dirac shift run."
        self.download_dir = CONSTANTS.DOWNLOAD_STR
        self.baseline_filename = "No baseline file loaded."
        self.sampling_filename = "No sampling file loaded."
        self.fx_filename = None

        # defining frames
        self.frame_connection = tkinter.Frame(self.window_root, background = "Yellow") # frame for connection controls
        self.frame_data = tkinter.Frame(self.window_root, background = "Green") # frame for data collection
        self.frame_analytics = tkinter.Frame(self.window_root, background = "Blue") # frame for analytics
        self.frame_feedback = tkinter.Frame(self.window_root, background = "Black") # frame for displaying feedback
        self.frame_connect_buttons = tkinter.Frame(self.frame_connection) # frame for connect buttons

        # defining frame positioning
        self.frame_connection.grid(row = 0, column = 0, sticky = "nw", padx = 10, pady = 10)
        self.frame_data.grid(row = 1, column = 0, sticky = "nw", padx = 10, pady = 10)
        self.frame_analytics.grid(row = 2, column = 0, sticky = "nw", padx = 10, pady = 10)
        self.frame_feedback.grid(row = 3, column = 0, sticky = "nw", padx = 10, pady = 10)

        # help!
        ttk.Button(self.frame_connection, text = "Help", command = self.help_action, width = 20).grid(row = 0, column = 0, sticky = "w", padx = 4, pady = 4)

        # connection controls
        ttk.Label(self.frame_connection, text = "Enter IP Address", width = 20).grid(row = 1, column = 0, sticky = "w", padx = 4, pady = 4)
        self.IP_entry = ttk.Entry(self.frame_connection, textvariable = self.IP)
        self.IP_entry.grid(row = 1, column = 1)
        self.frame_connect_buttons.grid(row = 1, column = 2, sticky = "w", padx = 4, pady = 4)
        ttk.Button(self.frame_connect_buttons, text = "Connect", command = self.connect_action, width = 20).grid(row = 0, column = 0, sticky = "w", padx = 4, pady = 4)
        ttk.Button(self.frame_connect_buttons, text = "Disconnect", command = self.disconnect_action, width = 20).grid(row = 0, column = 1, sticky = "w", padx = 4, pady = 4)

        # file name entry
        ttk.Label(self.frame_connection, text = "File name", width = 20).grid(row = 2, column = 0, sticky = "w", padx = 4, pady = 4)
        self.filename_entry = ttk.Entry(self.frame_connection, text = helpers.get_time())
        self.filename_entry.grid(row = 2, column = 1)
        ttk.Label(self.frame_connection, text = "File directory", width = 20).grid(row = 3, column = 0, sticky = "w", padx = 4, pady = 4)
        ttk.Button(self.frame_connection, text = "Select file directory", command = self.choose_download_dir, width = 20).grid(row = 3, column = 1, sticky = "w", padx = 4, pady = 4)
        self.download_dir_textbox = tkinter.Text(self.frame_connection, width = 40, height = 1)
        self.download_dir_textbox.grid(row = 3, column = 2, sticky = "w", padx = 4, pady = 4)
        self.modify_Text(self.download_dir_textbox, self.download_dir)

        # baseline controls
        ttk.Button(self.frame_data, text = "Baseline", command = self.baseline_action, width = 20).grid(row = 0, column = 0, sticky = "w", padx = 4, pady = 4)
        ttk.Button(self.frame_data, text = "Baseline from file", command = self.baseline_from_file_action, width = 20).grid(row = 0, column = 1, sticky = "w", padx = 4, pady = 4)
        self.baseline_file_textbox = tkinter.Text(self.frame_data, width = 40, height = 1)
        self.baseline_file_textbox.grid(row = 0, column = 2, sticky = "w", padx = 4, pady = 4)
        self.modify_Text(self.baseline_file_textbox, self.baseline_filename)

        # sample controls
        ttk.Button(self.frame_data, text = "Sample", command = self.sample_action, width = 20).grid(row = 1, column = 0, sticky = "w", padx = 4, pady = 4)
        ttk.Button(self.frame_data, text = "Sample from file", command = self.sample_from_file_action, width = 20).grid(row = 1, column = 1, sticky = "w", padx = 4, pady = 4)
        self.sampling_file_textbox = tkinter.Text(self.frame_data, width = 40, height = 1)
        self.sampling_file_textbox.grid(row = 1, column = 2, sticky = "w", padx = 4, pady = 4)
        self.modify_Text(self.sampling_file_textbox, self.sampling_filename)

        # analytics controls
        ttk.Button(self.frame_analytics, text = "Q/C Test", command = self.qc_action, width = 20).grid(row = 0, column = 0, sticky = "w", padx = 4, pady = 4)
        ttk.Label(self.frame_analytics, text = "Q/C Results: ", width = 20).grid(row = 0, column = 1, sticky = "w", padx = 4, pady = 4)
        self.qc_score_textbox = tkinter.Text(self.frame_analytics, width = 40, height = 1)
        self.qc_score_textbox.grid(row = 0, column = 2, sticky = "w", padx = 4, pady = 4)
        self.modify_Text(self.qc_score_textbox, self.qc_score_str)
        ttk.Button(self.frame_analytics, text = "Calculate Dirac Shift", command = self.calculate_dirac_action, width = 20).grid(row = 1, column = 0, sticky = "w", padx = 4, pady = 4)
        ttk.Label(self.frame_analytics, text = "Absolute Dirac Shift: ", width = 20).grid(row = 1, column = 1, sticky = "w", padx = 4, pady = 4)
        self.abs_dirac_shift_textbox = tkinter.Text(self.frame_analytics, width = 40, height = 1)
        self.abs_dirac_shift_textbox.grid(row = 1, column = 2, sticky = "w", padx = 4, pady = 4)
        self.modify_Text(self.abs_dirac_shift_textbox, self.abs_dirac_shift)

        # feedback string fields
        ttk.Label(self.frame_feedback, text = "Feedback String:", width = 20).grid(row = 1, column = 0, sticky = "w", padx = 4, pady = 4)
        ttk.Label(self.frame_feedback, textvariable = self.feedback_str).grid(row = 1, column = 1, sticky = "w", padx = 4, pady = 4)

        # strings for firmware file locations
        self.local_firmware = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONSTANTS.LOCAL_FIRMWARE_FILE_NAME)
        self.remote_firmware = CONSTANTS.REMOTE_FIRMWARE_PATH

        # analytics variables
        self.fx = None
        self.baseline_fx = None
        self.sampling_fx = None
        self.baseline_dirac = None
        self.sampling_dirac = None

        # variables for maintaining state of additional tkinter widgets
        self.popup_entry = None

        # search for IP addresses
        # self.update_ip_addresses()

        # start the window
        self.window_root.mainloop()

    ##### Additional TK components and methods #####

    def text_popup(self, title, prompt, button_action, geometry="300x100"):
        # Spawns a new window with an entry field and a submit button.
        window_popup = tkinter.Tk()
        window_popup.geometry(geometry)
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

    def modify_Text(self, widget, text):
        widget.config(state = "normal")
        widget.config(height = len(str(text).split("\n")))
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.config(state = "disabled")

    ##### Plots #####

    def plot_qc_approximations(self, xdata, ydata, hyperbolic_fit, parabolic_fit, linear_left, linear_right, mode="baseline"):
        helpers.print_debug(f"Plotting {mode} hyperbolic data and model")
        fig, ax = plt.subplots(1, 3)
        fig.set_size_inches(16, 5)
        ax[0].plot(xdata, ydata, label=f"Data {mode}")
        ax[0].plot(xdata, helpers.hyp_model(hyperbolic_fit, xdata), label=f"Hyperbolic fit {mode}")
        ax[0].legend()
        ax[0].set_xlabel("Voltage (scaled w.r.t. max V)")
        ax[0].set_ylabel("Current (scaled w.r.t. max A)")
        ax[0].set_title(f"Hyperbolic quality control plot ({mode})")
        helpers.print_debug(f"Plotting {mode} parabolic data and model")
        ax[1].plot(xdata, ydata, label=f"Data {mode}")
        ax[1].plot(xdata, helpers.par_model(parabolic_fit, xdata), label=f"Parabolic fit {mode}")
        ax[1].legend()
        ax[1].set_xlabel("Voltage (scaled w.r.t. max V)")
        ax[1].set_ylabel("Current (scaled w.r.t. max A)")
        ax[1].set_title(f"Parabolic quality control plot ({mode})")
        helpers.print_debug(f"Plotting {mode} linear data and model")
        ax[2].plot(xdata, ydata, label=f"Data {mode}")
        ax[2].plot(xdata, helpers.lin_model(linear_left, xdata), label=f"Left linear fit {mode}")
        ax[2].plot(xdata, helpers.lin_model(linear_right, xdata), label=f"Right linear fit {mode}")
        ax[2].legend()
        ax[2].set_xlabel("Voltage (scaled w.r.t. max V)")
        ax[2].set_ylabel("Current (scaled w.r.t. max A)")
        ax[2].set_title(f"Linear quality control plot ({mode})")
        plt.show()

    def plot_dirac_voltage(self, x_baseline, y_baseline, x_sampling, y_sampling, delta):
        helpers.print_debug("Plotting dirac voltage graph")
        fig, ax = plt.subplots(1, 1)
        ax.plot(x_baseline, y_baseline, label = "Baseline")
        ax.plot(x_sampling, y_sampling, label = "Sampling")
        ax.legend()
        ax.set_xlabel("Voltage (mV)")
        ax.set_ylabel("Current (μA)")
        ax.set_title(f"Dirac voltage comparison graph (|Δ|={delta})")
        plt.show()

    ##### File operations #####

    def select_file(self):
        filename = filedialog.askopenfilename()
        helpers.print_debug(f"Selected file: {filename}")
        return filename

    def select_directory(self):
        directory = filedialog.askdirectory()
        helpers.print_debug(f"Selected directory: {directory}")
        if directory == "":
            directory = CONSTANTS.DOWNLOAD_STR
        return directory

    def read_raw_data(self, file):
        helpers.print_debug(f"Opening file {file}")
        self.fx_filename = file
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
        def print_stuff(s):
            helpers.print_debug(s)
            self.feedback_str.set(s)
        IP = self.IP.get()
        if not helpers.validate_ip(IP):
            print_stuff(f'The IP address "{IP}" is not valid.')
            return
        print_stuff(f"Connecting to device ({IP})...")
        if not self.ssh_client.connect(IP, CONSTANTS.PORT):
            print_stuff(f"Could not connect to {IP}.")
            return
        print_stuff(f"Connected to {IP}. Uploading firmware to device...")
        if not self.ssh_client.upload_firmware(self.local_firmware, self.remote_firmware):
            print_stuff("Could not upload firmware.")
            return
        print_stuff("Connected to SSH device.")

    def disconnect_action(self):
        self.ssh_client.disconnect()
        self.feedback_str.set("Disconnected from SSH device.")

    def choose_download_dir(self):
        self.feedback_str.set("Selecting directory...")
        self.download_dir = self.select_directory()
        self.modify_Text(self.download_dir_textbox, self.download_dir)
        if self.download_dir == CONSTANTS.DOWNLOAD_STR:
            self.feedback_str.set(self.download_dir)
        else:
            self.feedback_str.set(f"Selected {self.download_dir}")

    def baseline_action(self):
        if not self.ssh_client.connected:
            self.feedback_str.set('Device is not connected. Please press the "Connect" button.')
            return
        if self.download_dir == CONSTANTS.DOWNLOAD_STR:
            self.feedback_str.set("No download directory selected. Please select one prior to running a baseline.")
            return
        filename, mode = self.filename_entry.get(), "BASELINE"
        if filename == "":
            self.feedback_str.set("Cannot run baseline using empty file name.")
            return
        self.ssh_client.collect_data(self.remote_firmware, filename, mode)
        local_baseline_raw_data_file = f"{self.download_dir}/{filename}_{mode}_RAW_DATA.csv"
        self.feedback_str.set(f"Using file {local_baseline_raw_data_file}")
        downloaded, time_elapsed, start_time = False, 0, time.time()
        remote_baseline_raw_data_file = f"/home/root/{filename}_{mode}_RAW_DATA.csv"
        while not downloaded and time_elapsed < CONSTANTS.MAX_DOWNLOAD_WAIT_TIME:
            helpers.print_debug(f"Waiting for baseline data file from device ({time_elapsed} seconds elapsed)...")
            time.sleep(CONSTANTS.DOWNLOAD_DELAY - (time.time() - start_time) % CONSTANTS.DOWNLOAD_DELAY)
            downloaded = self.ssh_client.download_file(remote_baseline_raw_data_file, local_baseline_raw_data_file)
            time_elapsed += CONSTANTS.DOWNLOAD_DELAY
        if not downloaded:
            helpers.print_debug(f"Maximum wait time {CONSTANTS.MAX_DOWNLOAD_WAIT_TIME} reached. Baseline data file was not downloaded.")
        else:
            helpers.print_debug(f"Downloaded file in {time.time() - start_time} seconds.")
        helpers.print_debug("Removing from device...")
        if not self.ssh_client.delete_file(remote_baseline_raw_data_file):
            helpers.print_debug(f"Warning: file {remote_baseline_raw_data_file} was not removed from device.")
        helpers.print_debug(f"Ending process from device...")
        if not self.ssh_client.kill_script():
            helpers.print_debug("Warning: process not ended.")
        if not downloaded:
            self.feedback_str.set("Baseline file not downloaded. Stopping")
            return
        self.read_raw_data(local_baseline_raw_data_file)
        self.baseline_fx = self.fx
        mina, mins, jmin = helpers.sweepmean(self.fx)
        self.baseline_dirac = {"mean": mina, "std": mins, "data": jmin}
        self.baseline_filename = local_baseline_raw_data_file
        self.modify_Text(self.baseline_file_textbox, self.baseline_filename)

    def sample_action(self):
        if not self.ssh_client.connected:
            self.feedback_str.set('Device is not connected. Please press the "Connect" button.')
            return
        if self.baseline_dirac is None:
            self.feedback_str.set("Please run a baseline first")
            return
        if self.download_dir == CONSTANTS.DOWNLOAD_STR:
            self.feedback_str.set("No download directory selected. Please select one prior to running a sample.")
            return
        filename, mode = self.filename_entry.get(), "SAMPLING"
        if filename == "":
            self.feedback_str.set("Cannot run sampling using empty file name.")
            return
        self.ssh_client.collect_data(self.remote_firmware, filename, mode)
        local_sampling_raw_data_file = f"{self.download_dir}/{filename}_{mode}_RAW_DATA.csv"
        self.feedback_str.set(f"Using file {local_sampling_raw_data_file}")
        downloaded, time_elapsed, start_time = False, 0, time.time()
        remote_sampling_raw_data_file = f"/home/root/{filename}_{mode}_RAW_DATA.csv"
        while not downloaded and time_elapsed < CONSTANTS.MAX_DOWNLOAD_WAIT_TIME:
            helpers.print_debug(f"Waiting for sampling data file from device ({time_elapsed} seconds elapsed)...")
            time.sleep(CONSTANTS.DOWNLOAD_DELAY - (time.time() - start_time) % CONSTANTS.DOWNLOAD_DELAY)
            downloaded = self.ssh_client.download_file(remote_sampling_raw_data_file, local_sampling_raw_data_file)
            time_elapsed += CONSTANTS.DOWNLOAD_DELAY
        if not downloaded:
            helpers.print_debug(f"Maximum wait time {CONSTANTS.MAX_DOWNLOAD_WAIT_TIME} reached. Sampling data file was not downloaded.")
        else:
            helpers.print_debug(f"Downloaded file in {time.time() - start_time} seconds.")
        helpers.print_debug("Removing from device...")
        if not self.ssh_client.delete_file(remote_sampling_raw_data_file):
            helpers.print_debug(f"Warning: file {remote_sampling_raw_data_file} was not removed from device.")
        helpers.print_debug("Ending process from device...")
        if not self.ssh_client.kill_script():
            helpers.print_debug("Warning: process not ended.")
        if not downloaded:
            self.feedback_str.set("Sampling file not downloaded. Stopping")
            return
        self.read_raw_data(local_sampling_raw_data_file)
        self.sampling_fx = self.fx
        mina, mins, jmin = helpers.sweepmean(self.fx)
        self.sampling_dirac = {"mean": mina, "std": mins, "data": jmin}
        self.sampling_filename = local_sampling_raw_data_file
        self.modify_Text(self.sampling_file_textbox, self.sampling_filename)

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
        self.baseline_filename = local_baseline_raw_data_file
        self.modify_Text(self.baseline_file_textbox, self.baseline_filename)
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
        self.sampling_filename = local_sampling_raw_data_file
        self.modify_Text(self.sampling_file_textbox, self.sampling_filename)
        self.feedback_str.set(f"Successfully loaded sampling file {local_sampling_raw_data_file}")

    def qc_action(self):
        if self.baseline_fx is None or self.sampling_fx is None:
            self.feedback_str.set("Both forward sweep arrays not present. Please run a baseline and a sample.")
            return
        self.feedback_str.set("Running quality control testing; generating fits")
        sweep_num = 1 # run QC test on the second sweep
        bx = [obj[0] for obj in self.baseline_fx[sweep_num]] # voltages
        by = [obj[1] for obj in self.baseline_fx[sweep_num]] # ids
        bxn = [item / max(bx) for item in bx] # normalized x
        byn = [item / max(by) for item in by] # normalized y
        sx = [obj[0] for obj in self.sampling_fx[sweep_num]]
        sy = [obj[1] for obj in self.sampling_fx[sweep_num]]
        sxn = [item / max(sx) for item in sx]
        syn = [item / max(sy) for item in sy]

        # check curve data
        check_curve_data = []
        if len(bxn) != len(byn):
            check_curve_data += [f"Baseline data lists do not have same number of elements: len(bxn) is {len(bxn)}; len(byn) is {len(byn)}."]
        if len(sxn) != len(syn):
            check_curve_data += [f"Sampling data lists do not have same number of elements: len(sxn) is {len(sxn)}; len(syn) is {len(syn)}."]
        if not all([type(item) is float for item in bxn + byn + sxn + syn]):
            check_curve_data += [f"Data lists must be entirely numeric."]
        if len(check_curve_data) > 0:
            print("Curve data is not proper.\n" + "\n".join(check_curve_data))
            return

        # Parabolic fits
        helpers.print_debug("Generating parabolic fits")
        B0p = [1, 1, 1] # initial search point for fminsearch
        parabolic_fit_baseline = scipy.optimize.fmin(func = helpers.par_residuals, x0 = B0p, args = (bxn, byn))
        parabolic_fit_sampling = scipy.optimize.fmin(func = helpers.par_residuals, x0 = B0p, args = (sxn, syn))

        # Hyperbolic fits
        helpers.print_debug("Generating hyperbolic fits")
        start_point = [0.890903252535798, 0.959291425205444, 0.547215529963803, 0.138624442828679]
        hyperbolic_fit_baseline = scipy.optimize.least_squares(helpers.hyp_residuals, x0 = start_point, args = (bxn, byn)) # does not return goodness of fit data
        hyperbolic_fit_sampling = scipy.optimize.least_squares(helpers.hyp_residuals, x0 = start_point, args = (sxn, syn))

        # Moving average filter and noise tests calculate max difference and average
        fil = matlab.movmean(byn, 3)
        bmaxn = max([abs(fil[i]-byn[i]) for i in range(len(byn))])
        bavgn = np.mean([abs(fil[i]-byn[i]) for i in range(len(byn))])
        fil = matlab.movmean(syn, 3)
        smaxn = max([abs(fil[i]-syn[i]) for i in range(len(syn))])
        savgn = np.mean([abs(fil[i]-syn[i]) for i in range(len(syn))])

        # Linear fit: split at minima and calculate slope on either side
        val = min(byn)
        xmin = min(max(byn.index(val), 2), len(byn) - 2)
        minx = bxn[xmin]
        bl = np.polynomial.polynomial.polyfit(bxn[:xmin], byn[:xmin], 1) # returns numpy.nd_array([c_1, c_2]) for y = c_1 * x + c_2
        br = np.polynomial.polynomial.polyfit(bxn[xmin:], byn[xmin:], 1)
        val = min(syn)
        xmin = min(max(syn.index(val), 2), len(syn) - 2)
        minx = sxn[xmin]
        sl = np.polynomial.polynomial.polyfit(sxn[:xmin], syn[:xmin], 1)
        sr = np.polynomial.polynomial.polyfit(sxn[xmin:], syn[xmin:], 1)

        score_baseline, message_baseline = helpers.score(hyperbolic_fit_baseline.x, parabolic_fit_baseline, {"maxn": bmaxn, "avgn": bavgn}, {"lsl": bl[1], "rsl": br[1]})
        score_sampling, message_sampling = helpers.score(hyperbolic_fit_sampling.x, parabolic_fit_sampling, {"maxn": smaxn, "avgn": savgn}, {"lsl": sl[1], "rsl": sr[1]})
        self.qc_score_str = f"Baseline score: {score_baseline}\n{message_baseline}\nSampling score: {score_sampling}\n{message_sampling}"
        self.modify_Text(self.qc_score_textbox, self.qc_score_str)
        helpers.print_debug(self.qc_score_str)

        self.feedback_str.set("Plotting baseline curves to new window...")
        self.plot_qc_approximations(bxn, byn, hyperbolic_fit_baseline.x, parabolic_fit_baseline, bl, br, mode = "baseline")
        self.feedback_str.set("Plotting sampling curves to new window...")
        self.plot_qc_approximations(sxn, syn, hyperbolic_fit_sampling.x, parabolic_fit_sampling, sl, sr, mode = "sampling")

        output_qc_parameters = {
            "data used": self.fx_filename,
            "hyperbolic fit": {
                "baseline params": {
                    "a": hyperbolic_fit_baseline.x[0],
                    "b": hyperbolic_fit_baseline.x[1],
                    "c": hyperbolic_fit_baseline.x[2],
                    "h": hyperbolic_fit_baseline.x[3]
                },
                "sampling params": {
                    "a": hyperbolic_fit_sampling.x[0],
                    "b": hyperbolic_fit_sampling.x[1],
                    "c": hyperbolic_fit_sampling.x[2],
                    "h": hyperbolic_fit_sampling.x[3]
                },
                "model": "(b**2 * ((x - h)**2 / (a**2) + 1))**0.5 + c"
            },
            "parabolic fit": {
                "baseline params": {
                    "a": parabolic_fit_baseline[0],
                    "b": parabolic_fit_baseline[1],
                    "c": parabolic_fit_baseline[2]
                },
                "sampling params": {
                    "a": parabolic_fit_sampling[0],
                    "b": parabolic_fit_sampling[1],
                    "c": parabolic_fit_sampling[2]
                },
                "model": "(((x - a)**2/4) * c) + b"
            },
            "linear fit": {
                "baseline params": {
                    "left fit": {
                        "b": bl[0],
                        "m": bl[1]
                    },
                    "right fit": {
                        "b": br[0],
                        "m": br[1]
                    }
                },
                "sampling params": {
                    "left fit": {
                        "b": sl[0],
                        "m": sl[1]
                    },
                    "right fit": {
                        "b": sr[0],
                        "m": sr[1]
                    }
                },
                "model": "m * x + b"
            },
            "moving average filter fits": {
                "baseline params": {
                    "moving mean maximum": bmaxn,
                    "moving mean average": bavgn
                },
                "sampling params": {
                    "moving mean maximum": smaxn,
                    "moving mean average": savgn
                }
            },
            "scores": {
                "baseline score": score_baseline,
                "baseline message": message_baseline,
                "sampling score": score_sampling,
                "sampling message": message_sampling
            }
        }
        output_qc_file = f"qc_params_{helpers.get_time()}.json"
        with open(output_qc_file, "w") as f:
            f.write(json.dumps(output_qc_parameters, indent = 4))
        self.feedback_str.set(f"Wrote results to {output_qc_file}")

    def calculate_dirac_action(self):
        if self.baseline_dirac is None:
            self.feedback_str.set("Please run a baseline first.")
            return
        if self.sampling_dirac is None:
            self.feedback_str.set("Please run a sample first.")
            return
        dirac_shift = abs(self.baseline_dirac["mean"] - self.sampling_dirac["mean"])
        dirac_shift = str(dirac_shift * 1000) + " mV"
        sweep_num = 1 # run QC test on the second sweep
        x_baseline = [obj[0] * 1000    for obj in self.baseline_fx[sweep_num]] # voltage converted to millivolts
        y_baseline = [obj[1] * 1000000 for obj in self.baseline_fx[sweep_num]] # amps converted to microamps
        x_sampling = [obj[0] * 1000    for obj in self.sampling_fx[sweep_num]] # millivolts!
        y_sampling = [obj[1] * 1000000 for obj in self.sampling_fx[sweep_num]] # microamps!
        self.feedback_str.set("Plotting absolute dirac voltage shift to new window")
        self.plot_dirac_voltage(x_baseline, y_baseline, x_sampling, y_sampling, dirac_shift)

        output_dirac_shift = {
            "data used": {
                "baseline": self.baseline_filename,
                "sampling": self.sampling_filename
            },
            "sweep number": sweep_num + 1,
            "absolute dirac shift": dirac_shift
        }
        self.abs_dirac_shift = dirac_shift
        self.modify_Text(self.abs_dirac_shift_textbox, self.abs_dirac_shift)

        output_dirac_file = f"dirac_shift_{helpers.get_time()}.json"
        with open(output_dirac_file, "w") as f:
            f.write(json.dumps(output_dirac_shift, indent = 4))
        self.feedback_str.set(f"Wrote results to {output_dirac_file}")

    def help_action(self):
        self.feedback_str.set(f"Opened help window")
        help_popup = tkinter.Tk()
        window_height = len(CONSTANTS.HELP_STRING.split("\n")) * 16
        help_popup.geometry(f"800x{window_height}")
        help_popup.title("Program Help Page")
        help_text = tkinter.Text(help_popup, width = 100, height = len(CONSTANTS.HELP_STRING))
        help_text.place(x = 0, y = 0)
        self.modify_Text(help_text, CONSTANTS.HELP_STRING)
        help_popup.mainloop()