import time
import numpy as np
import json

# helper function for logging timestamps
def get_time():
    return time.strftime("%Y-%m-%dT%H-%M-%SZ%z")

# helper function for logging stuff to terminal
DEBUG = True
def print_debug(s):
    if DEBUG:
        print(f"{get_time()} | {s}")


# helper function for scoring goodness of fit
def score(hyperbolic_fit, parabolic_fit, moving_mean_fit, linear_fit):
    print(hyperbolic_fit)
    print(parabolic_fit)
    print(moving_mean_fit)
    print(linear_fit)
    # score criteria based on weights of each parameter and cutoff
    scorelimit = 1

    # weights of each parameter
    sco = 0
    pw = .5
    hw = 2
    nw = .5
    sw = 3

    # return variable
    msg = ""

    if parabolic_fit[0] < 0:
        sco += pw
        msg += 'Parabola b: fail\n'
    if parabolic_fit[1] > 1:
        sco += pw
        msg += 'Parabola c: fail\n'
    if parabolic_fit[2] < 0:
        sco += pw
        msg += 'Parabola p: fail\n'
    # parabolic_fit is a numpy.ndarray([a, b, c, h])
    if hyperbolic_fit[0] < -0.5 or hyperbolic_fit[0] > 0.5:
        sco += hw
        msg += 'Hyperbolic a: fail\n'
    if hyperbolic_fit[1] < -0.5 or hyperbolic_fit[1] > 1:
        sco += hw
        msg += 'Hyperbolic b: fail\n'
    if hyperbolic_fit[2] < -1 or hyperbolic_fit[2] > 1:
        sco += hw
        msg += 'Hyperbolic c: fail\n'
    if hyperbolic_fit[3] < 0 or hyperbolic_fit[3] > 1:
        sco += hw
        msg += 'Hyperbolic h: fail\n'
    if moving_mean_fit["avgn"] < -0.0005 or moving_mean_fit["avgn"] > 0.005:
        sco += nw
        msg += 'Smooth avg: fail\n'
    if moving_mean_fit["maxn"] > 0.1:
        sco += nw
        msg += 'Smooth max: fail\n'
    if linear_fit["lsl"] > 0:
        sco += sw
        msg += 'Left slope: fail\n'
    if linear_fit["rsl"] < 0:
        sco += sw
        msg += 'Right slope: fail\n'

    if sco > scorelimit:
        msg += 'This data set is bad'
    else:
        msg += 'This data set is good'
    return sco, msg


##### helper fitting functions #####
def par_model(fun_params, x): # this will evaluate the parabolic fit function
    a, b, c = fun_params[0], fun_params[1], fun_params[2]
    return (((x - a)**2 / 4) * c) + b

def par_residuals(fun_params, xn, yn): # this evaluate the normalized residuals of the par_model function
    return np.linalg.norm(yn - par_model(fun_params, xn))

def hyp_model(fun_params, x): # this will evaluate the hyperbolic fit function
    a, b, c, h = fun_params[0], fun_params[1], fun_params[2], fun_params[3]
    return np.sqrt(b**2 * ((x - h)**2 / (a**2) + 1)) + c

def hyp_residuals(fun_params, xn, yn): # this will evaluate the residuals of the hyp_model function
    return yn - hyp_model(fun_params, xn)

def lin_model(fun_params, x): # this will evaluate the linear fit function
    b, m = fun_params[0], fun_params[1]
    return [m * item for item in x] + b # cannot multiple float by list of floats

def parse_device_id():# parse local calib.json file from connected device for device id
    try:
        with open("calib.json") as f:
            dev_file = json.load(f)
    except Exception as e:
        print("Couldn't load json file from local")
        print(f"Reason: {e}")
    return dev_file["ADC_CALIB"][0]["DEVICE_ID"]
    

def sweepmean(s): # needs testing
    """s assumed to have the following structure:
    [
        [
            [gate_voltages_1, ids_1],
            ['-0.1234', '6.78e-05'],
            ...
        ],
        [
            [gate_voltages_2, ids_2],
            ['0.2468', '-1.3579e-02'],
            ...
        ],
        ...
    ]
    note that this is the same as "fx" from the splitz_new_opt function
    """
    jmin = []
    i = 0
    for row in s: # each iteration finds the smallest ID, then adds the corresponding voltage to jmin
        IDs = [item[1] for item in row]
        voltages = [item[0] for item in row]
        min_id = min(IDs)
        min_voltage = voltages[IDs.index(min_id)]
        jmin += [min_voltage]
        print(f"sweepmean iteration {i}\n\tmin current: {1000000*min_id}uA at {IDs.index(min_id)}\n\tmin voltage: {1000*min_voltage}mV")
        i += 1
    mina = np.mean(jmin)
    mins = np.std(jmin)
    print(f"sweepmean average minimum voltage: {1000*mina}mV with stdev {1000*mins}mV")
    return mina, mins, jmin  # call this function with fx/bx, then display/save the mina and mins somewhere


# validation functions
def validate_ip(ip):
    parts = ip.split(".")
    try:
        if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
            return True
        else:
            print_debug(f"Invalid IP address: {ip}")
    except ValueError as e:
        print_debug(f"Invalid IP address: {ip}")
    return False