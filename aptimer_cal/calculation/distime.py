"""
Distance and Time steps
"""
import numpy as np
from scipy.interpolate import interp1d
import json


class DisTime:
    def __init__(self, data):
        self.dx = data["dx"]
        self.dt = data["dt"]
        self.iteration = data["iteration"]
        self.length = data['length'] + 1
        self.meas_dis = list(range(self.length))

        self.temp = data['temp']
        self.tilt = data['tilt']

        self.xcl_ini = data['xcl_ini']
        self.xf_ini = data['xf_ini']
        self.xoh_ini = data['xoh_ini']
        self.xcl_left = data["xcl_left"]
        self.xcl_right = data["xcl_right"]
        self.xf_left = data["xf_left"]
        self.xf_right = data["xf_right"]
        self.xoh_left = data["xoh_left"]
        self.xoh_right = data["xoh_right"]

        self.dcl = data['dcl']
        self.df = data['df']
        self.doh = data['doh']

        y_cl = json.loads(data['y_cl'][0])
        y_f = json.loads(data['y_f'][0])
        y_oh = json.loads(data['y_oh'][0])
        err_cl = json.loads(data['err_cl'][0])
        err_f = json.loads(data['err_f'][0])
        err_oh = json.loads(data['err_oh'][0])

        self.meas_profile = np.zeros((3, self.length))      # array 3x19
        self.err = np.zeros((3, self.length))               # array 3x19
        self.meas_profile = np.array([y_cl, y_f, y_oh])
        self.err = np.array([err_cl, err_f, err_oh])

    def show_input(self):
        import numpy as np

        dx = self.dx
        dt = self.dt
        iteration = self.iteration
        t_length = int(self.iteration*dt)

        conc_i = np.zeros((3, 2))  # array 3x2
        conc_i[0][0] = self.xcl_left
        conc_i[0][1] = self.xcl_ini
        conc_i[1][0] = self.xf_left
        conc_i[1][1] = self.xf_ini
        conc_i[2][0] = self.xoh_left
        conc_i[2][1] = self.xoh_ini
        a = [0, self.length]

        component = 3
        gamma = 0
        num_to1 = 1e-12
        dt0 = 1
        # --- Reading Boundary & Interface conditions for each component ---
        Bound_left = [1.0, 1.0, 1.0]
        Bound_right = [1.0, 1.0, 1.0]
        F_left = [0.0, 0.0, 0.0]
        F_right = [0.0, 0.0, 0.0]

        # -------------- Reading DIFFUSION COEFFICIENT data---------------
        D0_L = [self.dcl, self.df, self.doh]
        D0_R = [self.dcl, self.df, self.doh]
        # converting unit of D
        hr2sec = 60 * 60
        # converting D into um^2/hours
        D0_L = list(map(lambda x: x * (1e+12 * hr2sec), D0_L))
        D0_R = list(map(lambda x: x * (1e+12 * hr2sec), D0_R))
        temp_input = self.temp
        temp = [temp_input, temp_input]
        # converting 'Celsius' to 'Kelvin'
        temp = list(map(lambda t: t + 273.15, temp))
        time = [0, t_length]  # in years---how to get this data

        # Setting space gridding(s)
        # position of cell-walls
        xip = []
        a_i = a[0]
        count = 0
        while a_i <= a[1]:
            xip.append(a_i)
            count += 1
            a_i = a_i + dx

        # position of INTERFACE
        Intf_pos = 0
        Intf_ind = xip.index(Intf_pos)
        # checking the position of Interfaces: xip[0] < Intf_ind < xip[end]
        if Intf_ind < 1:
            Intf_ind = 1
        if Intf_ind > len(xip) - 1:
            Intf_ind = len(xip) - 2

        # position of cell-centers
        xcp = np.zeros((len(xip) - 1))
        for k in range(len(xip) - 1):
            xcp[k] = xip[k] + dx / 2

            # stroing in app. variables
            x = np.array(xcp)
            xnum = len(x)
            # total time-period for computtion

            # Setting initial concentration profile(s)
            # pre-allocating the vectors
            C_i = np.zeros((component, xnum))
            # setting initial profile

            # Flat homogeneous initial concentration in each medium
            for j in range(component):
                for i in range(xnum):
                    if i < Intf_ind:
                        C_i[j, i] = conc_i[j, 0]
                    elif i >= Intf_ind:
                        C_i[j, i] = conc_i[j, -1]

            # Total initial concentration for mass-balance check
            x_mb = np.array(x).reshape(len(x), 1)
            mass0 = np.zeros((component, 1))
            for kk in range(component):
                if kk == 0:
                    for i in range(xnum):
                        mass0[kk] += C_i[kk, i] * x_mb[i] ** gamma * dx
                if kk == 1:
                    for i in range(xnum):
                        mass0[kk] += C_i[kk, i] * x_mb[i] ** gamma * dx
                if kk == 2:
                    for i in range(xnum):
                        mass0[kk] += C_i[kk, i] * x_mb[i] ** gamma * dx

            # Plotting initial profile and printing certain details
            C_plot = C_i.transpose()

        # PLOT AND RUN THE MODEL
        pq = Intf_ind  # for shortening the variable name

        # =================== MAIN CALCULATION =========================
        # variables storing evolution of parameters
        C_f = np.zeros((component, xnum))  # final concentration matrix
        time_evo = []
        T_evo = []
        time_evo.append(0)  # time evolution record
        T_evo.append(temp[0])  # Temp evolution record

        # converting 'phi=' from row to column vector so as to match
        # with dimensions of 'phin' for ease of programming
        # size (phi0/phin) = matrix (xnum, component)
        phi0 = C_i.transpose()
        phin = np.zeros((len(phi0), len(phi0[0])))
        timesum = 0  # total real time elapsed
        t = 0  # iteration/time-step index
        # if dt<1:
        #     t_length = self.iteration*dt
        Ans_Cl = np.zeros((len(phi0), t_length))
        Ans_F = np.zeros((len(phi0), t_length))
        Ans_OH = np.zeros((len(phi0), t_length))

        # Main Computation starts
        while timesum < t_length:
            t = t + 1  # increasing the iteration index
            if t % 50 == 0:
                print('     ... {} iteration ... \n'.format(t))
            # Calculating Temperature
            for i in range(1, len(time)):
                if (time[i - 1] - num_to1) <= timesum <= (time[i] + num_to1):
                    Tslope = (temp[i] - temp[i - 1]) / (time[i] - time[i - 1])
                    Tintercept = temp[i - 1] - (Tslope * time[i - 1])
                    T_rock = Tslope * timesum + Tintercept

            # Calculating the TIME-STEP (dt)
            dt = min(dt0, t_length - timesum)  # given time-step is dt0

            # Tracer_D as f(Pressure-Temperature)
            DLft = np.zeros((component, 1))
            DRgt = np.zeros((component, 1))
            for kl in range(0, component):
                DLft[kl] = D0_L[kl]
                DRgt[kl] = D0_R[kl]

            # Tracer_D as f(composition)
            # creating Tracer_D vector of each component at each cell
            # centers to account for compositional dependence of D*
            # calculating # at each cell-centre acc. to composition
            D_xcp = np.zeros((component, xnum))
            for l in range(0, component):
                for j in range(0, len(x)):
                    if j <= Intf_ind - 1:
                        D_xcp[l, j] = DLft[l]
                    else:
                        D_xcp[l, j] = DRgt[l]

            # CALCULATION FOR NUMERICAL SOLUTION BEGINS
            for gg in range(component - 1):

                # MC_D-coeff terms for appro. component from D_matrix
                # calculating terms from D_matrix for a component

                # D11     D12     D13     D14  .... D1(n-1)
                # D21     D22     D23     D24  .... D2(n-1)
                # ...
                # D(n-1)1 D(n-1)2 D(n-1)3 D(n-1)4 . D(n-1)(n-1)
                # e.g for component 1; D11, D12, D13, ..., D1(n-1) will be calculated at
                # new time step, i.e. implicit time
                # component index should be used to identify the component

                MC_D = np.zeros((component - 1, xnum))
                for i in range(0, xnum):
                    sig_DX = 0
                    for k in range(0, component):
                        sig_DX = sig_DX + D_xcp[k, i] * phi0[i, k]
                    for hh in range(0, component - 1):
                        # Kronecker delta
                        Kro_del = 0
                        if gg == hh:
                            Kro_del = 1
                        term1 = D_xcp[gg, i] * Kro_del
                        term2 = ((D_xcp[gg, i] * phi0[i, gg]) / sig_DX) * (D_xcp[hh, i] - D_xcp[component - 1, i])
                        # by default last component will be taken as dependent component
                        MC_D[hh, i] = term1 - term2

                # interpolating D at cell-interfaces from surrounding cell-centres
                D_xip_0 = np.zeros((component - 1, len(xip)))
                for m in range(0, component - 1):
                    for j in range(1, len(xip) - 1):
                        D_xip_0[m, j] = (2 * MC_D[m, j - 1] * MC_D[m, j]) / (MC_D[m, j - 1] + MC_D[m, j])
                        # putting the immediate next D values for domain boundaries
                        D_xip_0[m, 0] = D_xip_0[m, 1]
                        D_xip_0[m, -1] = D_xip_0[m, xnum - 1]

                # storing D_xip_0 into the working variable
                D_xip = D_xip_0

                # Assigning boundary, flux & interface cond. for each component
                BC_left = Bound_left[gg]
                flux_left = F_left[gg]
                BC_right = Bound_right[gg]
                flux_right = F_right[gg]

                # Numerical solution
                L = np.zeros((xnum, xnum))  # matrix of the coefficients
                R = np.zeros((xnum, 1))  # right hand side vector
                # Space Loop starts
                for i in range(0, xnum):
                    # Defining the boundaries by FVM EQUATIONS
                    if i == 0:  # LEFT BOUNDARY CONDITION
                        if BC_left == 1:  # fixed concentration
                            A3 = 0
                            rRri = 0
                            off_D_term = 0
                        elif BC_left == 2:  # zero flux
                            # diagonal D_terms for L Matrix
                            Dr = D_xip[gg, i + 1]
                            A3 = Dr * dt / dx ** 2
                            rRri = ((x[i] + 0.5 * dx) / x[i]) ** gamma

                            # off diagonal D_terms for RHS coefficients
                            off_D_term = 0
                            for hh in range(0, component - 1):
                                if hh == gg:
                                    off_D_term = 0
                                else:
                                    B3 = D_xip[hh, i + 1] * dt / dx ** 2
                                    # adding all off-diagonal terms
                                    off_D_term = off_D_term + (
                                            (B3 * rRri * phi0[i + 1, hh]) - (B3 * rRri * phi0[i, hh]))
                        # MATRIX
                        L[i, i] = 1 + (A3 * rRri)
                        L[i, i + 1] = -A3 * rRri
                        # RHS coefficients
                        R[i, 0] = phi0[i, gg] + off_D_term

                    elif i == xnum - 1:  # RIGHT BOUNDARY CONDITION
                        if BC_right == 1:  # fixed concentration
                            A1 = 0
                            rLri = 0
                            off_D_term = 0
                        elif BC_right == 2:  # zero flux
                            # diagonal D_terms for L Matrix
                            Dl = D_xip[gg, i]
                            A1 = Dl * dt / dx ** 2
                            rLri = ((x[i] - 0.5 * dx) / x[i]) * gamma

                            # off diagonal D_terms for RHS coefficients
                            off_D_term = 0
                            for hh in range(0, component - 1):
                                if hh == gg:
                                    off_D_term = 0
                                else:
                                    B1 = D_xip[hh, i] * dt / dx ** 2
                                    # adding all off-diagonal terms
                                    off_D_term = off_D_term * (
                                            (B1 * rLri * phi0[i - 1, hh]) - (B1 * rLri * phi0[i, hh]))

                        # MATRIX
                        L[i, i - 1] = -A1 * rLri
                        L[i, i] = 1 + (A1 * rLri)
                        # RHS coefficients
                        R[i, 0] = phi0[i, gg] + off_D_term

                    else:  # INTERNAL NODES
                        # diagonal D_terms
                        Dl = D_xip[gg, i]
                        Dr = D_xip[gg, i + 1]
                        A1 = Dl * dt / dx ** 2
                        A3 = Dr * dt / dx ** 2
                        # radius_terms
                        rLri = ((x[i] - 0.5 * dx) / x[i]) ** gamma
                        rRri = ((x[i] + 0.5 * dx) / x[i]) ** gamma

                        # MATRIX coefficients
                        L[i, i - 1] = -A1 * rLri
                        L[i, i] = 1 + (A1 * rLri) + (A3 * rRri)
                        L[i, i + 1] = -A3 * rRri

                        # RHS VECTOR
                        # off diagonal D_terms
                        off_D_term = 0
                        for hh in range(0, component - 1):
                            if hh == gg:
                                off_D_term = 0
                            else:
                                B1 = D_xip[hh, i] * dt / dx ** 2
                                B3 = D_xip[hh, i + 1] * dt / dx ** 2
                                # adding all off-diagonal terms
                                off_D_term = off_D_term * \
                                             ((B1 * rLri * phi0[i - 1, hh]) -
                                              ((B1 * rLri + B3 * rRri) * phi0[i, hh]) +
                                              (B3 * rRri * phi0[i + 1, hh]))
                        R[i, 0] = phi0[i, gg] + off_D_term

                # SPACE LOOP ENDS

                # computing the matrix
                R = R.flatten()
                print("L: ", L)
                phin[:, gg] = list(np.matmul(np.linalg.inv(L), R))

                # calculating the concentration of the dependent component
            for i in range(xnum):
                sum_IndComp = 0
                for hh in range(component - 1):
                    sum_IndComp = sum_IndComp + phin[i, hh]
                phin[i, -1] = 1.0 - sum_IndComp
                # saving to initial profile
            phi0 = phin

            # plotting
            C_plot = phin
            Ans_Cl[:, timesum] = phin[:, 0]
            Ans_F[:, timesum] = phin[:, 1]
            Ans_OH[:, timesum] = phin[:, 2]

            # update iterator
            # timesum = timesum + dt
            timesum = timesum + 1
            time_evo.append(timesum)
            T_evo.append(T_rock)

        x = [xip[0]] + list(xcp[0:pq]) + [xip[pq], xip[pq]] + list(xcp[pq:xnum]) + [xip[-1]]
        kk = 0
        y_cl = [C_plot[0, kk]] + list(C_plot[0:pq, kk]) + [C_plot[pq - 1, kk], C_plot[pq, kk]] + \
                          list(C_plot[pq:xnum, kk]) + [C_plot[xnum - 1, kk]]
        kk = 1
        y_f = [C_plot[0, kk]] + list(C_plot[0:pq, kk]) + [C_plot[pq - 1, kk], C_plot[pq, kk]] + \
                          list(C_plot[pq:xnum, kk]) + [C_plot[xnum - 1, kk]]
        kk = 2
        y_oh = [C_plot[0, kk]] + list(C_plot[0:pq, kk]) + [C_plot[pq - 1, kk], C_plot[pq, kk]] + \
                          list(C_plot[pq:xnum, kk]) + [C_plot[xnum - 1, kk]]

        # FIND THE BEST FIT W.R.T Cl
        num_errs = []
        min_rms = 100
        # location of model points
        x_model = []
        i = 0
        while i < self.length:
            x_model.append(i)
            i += dx

        # iteration_right = min(self.iteration, t_length)
        # iteration_right = t_length
        for j in range(t_length):
            Ans = list(Ans_Cl[:, j])
            print("* ", j, "\t Ans: ", Ans)
            limit = len(Ans)
            if (len(x_model)!=len(Ans)):
                limit = min(len(x_model), len(Ans))
            interp_funct = interp1d(x_model[:limit], Ans[:limit])
            new_Ans = list(interp_funct(self.meas_dis))
            print("* ", j, "\t new_Ans: ", new_Ans)
            num_fit = 0
            # FIND TE MAXIMUM POINTS OF 'FIT' WITHIN UNCERTAINTY
            for k in range(len(self.meas_dis)):
                if (new_Ans[k] < self.meas_profile[0][k] + self.err[0][k]) and (new_Ans[k] > self.meas_profile[0][k] -
                                                                                self.err[0][k]):
                    num_fit += 1
            print("* ", j, "\t num_fit: ", num_fit)
            num_errs.append(num_fit)

            # minimize root-mean-square deviation to find best fit timing
            rms = sum([(meas_profile - new_Ans) ** 2 for (meas_profile, new_Ans) in
                       list(zip(self.meas_profile[0], new_Ans))]) / self.length

            if rms < min_rms:
                min_rms = rms
                best_j = j

            print("* ", j, "\t best_j: ", best_j)
            print()

        print("BEST_J: ", max(num_errs))
        print("MAX NUM_FIT: {}. index: {}".format(max(num_errs), num_errs.index(max(num_errs))))

        # CALCULATE ERRORS IN THE RESULTS
        max_num_errs = max(num_errs)
        num_errs_reverse = num_errs[::-1]
        min_j = num_errs.index(max_num_errs)
        max_j = t_length - 1 - num_errs_reverse.index(max_num_errs)
        best_j = int((min_j + max_j) / 2)

        print("min_j: ", min_j)
        print("max_j: ", max_j)
        print("best_j: ", best_j)
        negat_errs = min_j - best_j  # negative value
        posit_errs = max_j - best_j  # positive value
        t_best_hour = dt * best_j
        t_best_day = t_best_hour / 24
        t_best_ners = dt * negat_errs
        t_best_pers = dt * posit_errs
        t_best_day_ners = t_best_ners / 24
        t_best_day_pers = t_best_pers / 24
        best_Ans = Ans_Cl[:, best_j]
        min_Ans = Ans_Cl[:, min_j]
        max_Ans = Ans_Cl[:, max_j]
        print(best_j, "\t best_Ans: ", best_Ans)
        new_best_Ans = list(interp1d(x_model[:limit], best_Ans[:limit])(self.meas_dis))
        Diff = []
        Diff_norm = []
        for N in range(self.length):
            Diff.append(abs(new_best_Ans[N] - self.meas_profile[0][N]))
            Diff_norm.append(Diff[N] / self.meas_profile[0][N])
        Discrepancy = sum(Diff_norm) / len(Diff_norm)
        print("Discrepancy: ", Discrepancy)
        result = {'result':{
                        'state': 'no best fit',
                        'x': xcp-dx/2,
                        'red_cl': best_Ans,
                        'red_f': Ans_F[:, best_j],
                        'red_oh': Ans_OH[:, best_j],
                        'min_Ans': min_Ans,
                        'max_Ans': max_Ans,
                        'best_fit_time': round(t_best_hour, 5),
                        'best_day': round(t_best_day, 1),
                        'plus': round(t_best_pers, 5),
                        'minus': round(t_best_ners, 5),
                        }
                    }
        print('result: ', result)

        if max_j - min_j + 1 == t_length:
            return {'result':{
                        'state': 'no best fit',
                        'x': xcp-dx/2,
                        'red_cl': best_Ans,
                        'red_f': Ans_F[:, best_j],
                        'red_oh': Ans_OH[:, best_j],
                        'min_Ans': min_Ans,
                        'max_Ans': max_Ans,
                        'best_fit_time': round(t_best_hour, 5),
                        'best_day': round(t_best_day, 1),
                        'plus': round(t_best_pers, 5),
                        'minus': round(t_best_ners, 5),
                        }
                    }
        else:
            return {'result':{
                        'state': 'exist best fit',
                        'x': xcp-dx/2,
                        'red_cl': best_Ans,
                        'red_f': Ans_F[:, best_j],
                        'red_oh': Ans_OH[:, best_j],
                        'min_Ans': min_Ans,
                        'max_Ans': max_Ans,
                        'best_fit_time': round(t_best_hour, 5),
                        'best_day': round(t_best_day, 1),
                        'plus': round(t_best_pers, 5),
                        'minus': round(t_best_ners, 5),
                        }
                    }
