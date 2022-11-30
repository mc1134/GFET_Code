def sweepmean2(s): # needs testing
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
    try:
        s_len = len(s)
    except Exception as e:
        print(e)
        return
    Rsq, jmin = [], []
    for i in range(s_len):
        f1 = [[item[0] for item in lst] for lst in s]
        f1_T = [[row[i] for i in range(len(row))] for row in f1]
        val = min(fl_T[1])
        xmin = f1_T[1].index(val)
        xmin = f1[xmin][0]
        jmin += xmin
    mina = mean(jmin)
    mins = np.std(jmin)
    return mina, mins, jmin  # call this function with fx/bx, then display/save the mina and mins somewhere