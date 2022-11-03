import numpy as np
import ruptures as rpt

def splitz_new_opt(data):
    """data assumed to possess the following structure:
    [
        ['Gate Voltage', 'Ids'],
        ['-0.12345', '6.789e-05'],
        ['0.2468', '-1.3579e-02'],
        ...
    ]
    """
    forw = []
    back = []
    """both arrays will represent the original 3D matrix with the following structure:
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
    third dimension is first layer, i.e. the different [['0','0'],['1','1']]
    accessing A(:,:,2) converts to A[1] in python
    accessing A(1,:,5) converts to [obj[0] for obj in A[4]]
    accessing A(3,:,:) converts to [obj[2] for obj in A[idx] for idx in len(A)]
    """

    # Finding where the voltage changes direction in the sweep + to - viceversa
    V = [float(d[0]) for d in data[1:]] # casts [[header1,header2],[a1,a2],[b1,b2],[c1,c2],...] list of str lists into [a1,b1,c1,...] list of floats
    dv = np.diff(V)

    # Number of splits calculation
    numsweep = 793 # Number of datapoints per sweep
    swns = int(len(dv)/numsweep) # Number of sweeps roughly

    pts = rpt.Binseg(model = "l2").fit(dv).predict(n_bkps = swns) # find change points. this takes a very long time (5 minutes for 700 data points?)

    # Splitting the forward and backward into two separate arrays
    sam = np.mean(dv[pts[1]:pts[2]])
    if sam > 0:
        pidx = 1 # Cycle through the pts array
        for val in range(1,(len(pts)-1)//2):
            forw += [data[pts[pidx]  +20:pts[pidx]  +numsweep-20]]
            back += [data[pts[pidx+1]+20:pts[pidx+1]+numsweep-20]]
            pidx += 2
    else:
        pidx = 1
        for val in range(1, (len(pts)-1)//2):
            back += [data[pts[pidx]  +20:pts[pidx]  +numsweep-20]]
            forw += [data[pts[pidx+1]+20:pts[pidx+1]+numsweep-20]]
            pidx += 2

    return forw, back