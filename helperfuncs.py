import time

# helper function for logging timestamps
def get_time():
    return time.strftime("%Y-%m-%dT%H-%M-%SZ%z")

# helper function for logging stuff to terminal
DEBUG = True
def print_debug(s):
    if DEBUG:
        print(f"{get_time()} | {s}")

def score(hyperbolic_fit, parabolic_fit, moving_mean_fit, linear_fit):
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

    if hyperbolic_fit[0] < 0:
        sco += pw
        msg += 'Parabola b: fail\n'
    if hyperbolic_fit[1] > 1:
        sco += pw
        msg += 'Parabola c: fail\n'
    if hyperbolic_fit[2] < 0:
        sco += pw
        msg += 'Parabola p: fail\n'
    # parabolic_fit is a numpy.ndarray([a, b, c, h])
    if parabolic_fit.x[0] < -0.5 or parabolic_fit.x[0] > 0.5:
        sco += hw
        msg += 'Hyperbolic a: fail\n'
    if parabolic_fit.x[1] < -0.5 or parabolic_fit.x[1] > 1:
        sco += hw
        msg += 'Hyperbolic b: fail\n'
    if parabolic_fit.x[2] < -1 or parabolic_fit.x[2] > 1:
        sco += hw
        msg += 'Hyperbolic c: fail\n'
    if parabolic_fit.x[3] < 0 or parabolic_fit.x[3] > 1:
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