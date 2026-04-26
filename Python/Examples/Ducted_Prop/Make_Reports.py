# Port target: SourceCode/Make_Reports.m
"""Generate graphical and text reports for a propeller design."""

import datetime
import numpy as np
from InterpolateChord import InterpolateChord


def Make_Reports(pt):
    """Create design summary reports (text and optional plots).

    Ported from ``SourceCode/Make_Reports.m``.

    Parameters
    ----------
    pt : dict
        Propeller/turbine data structure.  Must contain at minimum
        ``pt['input']`` and ``pt['design']``.  Accepts the shorthand
        aliases ``pt['i']`` for ``pt['input']`` and ``pt['d']`` for
        ``pt['design']``.

    Returns
    -------
    None
    """
    # ------------------------------------------------- Alias shortcuts
    if 'i' in pt and 'input' not in pt:
        pt['input'] = pt['i']
    if 'd' in pt and 'design' not in pt:
        pt['design'] = pt['d']

    # -------------------------------------------------- Unpack input
    input_ = pt['input']

    # Date string
    if 'date' in pt:
        Date_string = pt['date']
    else:
        Date_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Filename
    if 'filename' in pt:
        filename = pt['filename']
    elif 'name' in pt:
        filename = pt['name']
    elif 'filename' in input_:
        filename = input_['filename']
    else:
        filename = 'OpenProp'

    # --------------------------------------------------------- Required inputs
    Z = input_['Z']          # number of blades

    # --------------------------------------------------------- Geometry inputs
    Np   = input_.get('Np',   20)
    Vs   = input_.get('Vs',    1)    # m/s
    R    = input_.get('R',     1)    # m
    Rhub = input_.get('Rhub', 0.2)   # m
    rho  = input_.get('rho', 1000)   # kg/m^3

    # If propeller geometry / inflow not given, use empty arrays
    if 'XR' in input_:
        XR  = np.asarray(input_['XR'], dtype=float)
        X1  = np.ones(XR.shape)
        X0  = np.zeros(XR.shape)
        XCoD  = np.asarray(input_.get('XCoD',  X0), dtype=float)
        t0oc0 = np.asarray(input_.get('t0oc0', X0), dtype=float)
        XVA   = np.asarray(input_.get('XVA',   X1), dtype=float)
        XVT   = np.asarray(input_.get('XVT',   X0), dtype=float)
    else:
        XR    = np.array([])
        X1    = 1.0
        X0    = 0.0
        XCoD  = np.array([])
        t0oc0 = np.array([])
        XVA   = np.array([])
        XVT   = np.array([])

    if 'XCD' in input_:
        XCD = np.asarray(input_['XCD'], dtype=float)
        if XCD.size == 1:
            XCD = XCD * X1
    else:
        XCD = 0.008 * X1

    # ----------------------------------------------------------------- Flags
    Propeller_flag = input_['Propeller_flag']
    Viscous_flag   = input_['Viscous_flag']

    Hub_flag   = input_.get('Hub_flag',   1)
    Duct_flag  = input_.get('Duct_flag',  0)
    Chord_flag = input_.get('Chord_flag', 0)
    Plot_flag  = input_.get('Plot_flag',  0)
    Wake_flag  = input_.get('Wake_flag',  0)

    # -------------------------------------------------------- Propeller_flag
    if Propeller_flag == 1:
        Js = input_['Js']
        L  = np.pi / Js

        if 'THRUST' in input_:
            CTdes = input_['THRUST'] / (0.5 * rho * Vs**2 * np.pi * R**2)
        elif 'CTDES' in input_:
            CTdes = input_['CTDES']
        elif 'CT' in input_:
            CTdes = input_['CT']
        elif 'KTDES' in input_:
            CTdes = input_['KTDES'] * (8 / np.pi) / Js**2
        elif 'KT' in input_:
            CTdes = input_['KT'] * (8 / np.pi) / Js**2
        else:
            CTdes = 0.0
    else:
        L     = input_['L']
        Js    = np.pi / L
        CTdes = 0.0

    # ------------------------------------------------------------ Viscous_flag
    if Viscous_flag == 0:
        XCD   = X0
        CDoCL = 0.0

    # --------------------------------------------------------------- Duct_flag
    if Duct_flag == 1:
        TAU      = input_.get('TAU', 1)

        if 'Rduct_oR' in input_:
            Rduct_oR = input_['Rduct_oR']
        elif 'Rduct' in input_:
            Rduct_oR = input_['Rduct'] / R
        else:
            Rduct_oR = 1.0

        if 'Cduct_oR' in input_:
            Cduct_oR = input_['Cduct_oR']
        elif 'Cduct' in input_:
            Cduct_oR = input_['Cduct'] / R
        else:
            Cduct_oR = 1.0

        if 'Xduct_oR' in input_:
            Xduct_oR = input_['Xduct_oR']
        elif 'Xduct' in input_:
            Xduct_oR = input_['Xduct'] / R
        else:
            Xduct_oR = 0.0

        CDd = input_.get('CDd', 0.008)
    else:
        TAU      = 1.0
        Rduct_oR = 1.0
        CDd      = 0.0

    # ------------------------------------------------------ Computational inputs
    HUF = input_.get('HUF', 0)
    TUF = input_.get('TUF', 0)
    Rhv = input_.get('Rhv', 0.5)

    # ------------------------------------------------------- Cavitation inputs
    dVs  = input_.get('dVs',  0.30)    # m/s
    H    = input_.get('H',    3.048)   # m
    g    = input_.get('g',    9.81)    # m/s^2
    Patm = input_.get('Patm', 101325)  # Pa
    Pv   = input_.get('Pv',   2500)    # Pa

    # ------------------------------------------------- Unpack design variables
    design = pt['design']

    CT   = design['CT']
    CQ   = design['CQ']
    CP   = design['CP']
    VMIV = design['VMIV']

    if Propeller_flag == 1:
        KT   = design['KT']
        KQ   = design['KQ']
        EFFY = design['EFFY']

    RC      = np.asarray(design['RC'],      dtype=float)
    Mp      = len(RC)
    RV      = np.asarray(design['RV'],      dtype=float)
    G       = np.asarray(design['G'],       dtype=float).ravel()
    VAC     = np.asarray(design['VAC'],     dtype=float)
    VTC     = np.asarray(design['VTC'],     dtype=float)
    UASTAR  = np.asarray(design['UASTAR'],  dtype=float)
    UTSTAR  = np.asarray(design['UTSTAR'],  dtype=float)
    TANBC   = np.asarray(design['TANBC'],   dtype=float)
    TANBIC  = np.asarray(design['TANBIC'],  dtype=float)
    CoD     = np.asarray(design['CoD'],     dtype=float)
    CL      = np.asarray(design['CL'],      dtype=float)
    CD      = np.asarray(design['CD'],      dtype=float)

    if Duct_flag == 1:
        TAU    = design['TAU']
        XdRING = np.asarray(design['XdRING'], dtype=float)
        GdRING = np.asarray(design['GdRING'], dtype=float)
        UADIF  = np.asarray(design['UADIF'],  dtype=float)
        Gd     = design['Gd']
        UARING = np.asarray(design['UARING'], dtype=float)
        URRING = np.asarray(design['URRING'], dtype=float)
    else:
        TAU    = 1.0
        XdRING = np.array([1.0])
        GdRING = np.array([0.0])
        UADIF  = np.zeros(Mp)
        Gd     = 0.0
        UARING = np.array([0.0])
        URRING = np.array([0.0])
        Rduct_oR = 1.0

    Beta_c  = np.degrees(np.arctan(TANBC))   # [deg]
    BetaI_c = np.degrees(np.arctan(TANBIC))  # [deg]

    # -------------------------------------------------------------------------
    D       = 2 * R          # [m]
    Dhub    = 2 * Rhub        # [m]
    Rhub_oR = Rhub / R
    N       = 60 * Vs / (Js * D)   # [RPM]
    n       = N / 60                # [rev/s]

    # --------------------------------------------- Create Graphical Report
    if Plot_flag:
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.canvas.manager.set_window_title('Graphical Report')

            # Subplot 1: Circulation
            ax = axes[0, 0]
            ax.plot(RC, G)
            ax.set_xlabel('r/R')
            ax.set_ylabel('Gamma / 2piRVs')
            ax.grid(True)

            if Propeller_flag == 1:
                title_str = (f'J={Js:.3f}; Ct={CT:.3f}; Cq={CQ:.3f}; '
                             f'Kt={KT:.3f}; Kq={KQ:.3f}; '
                             f'eta={EFFY:.3f}; tau={TAU:.3f}')
            else:
                title_str = (f'J={Js:.3f}; Ct={CT:.3f}; '
                             f'Cq={CQ:.3f}; tau={TAU:.3f}')
            ax.set_title(title_str, fontsize=8)

            # Subplot 2: Velocities
            ax = axes[0, 1]
            ax.plot(RC, VAC,    '-b',  label='Va/Vs')
            ax.plot(RC, VTC,    '--b', label='Vt/Vs')
            ax.plot(RC, UASTAR, '-.r', label='Ua*/Vs')
            ax.plot(RC, UTSTAR, ':r',  label='Ut*/Vs')
            ax.set_xlabel('r/R')
            ax.grid(True)
            ax.legend()

            # Subplot 3: Flow angles
            ax = axes[1, 0]
            ax.plot(RC, Beta_c,  '--b', label='Beta')
            ax.plot(RC, BetaI_c, '-r',  label='BetaI')
            ax.set_xlabel('r/R')
            ax.set_ylabel('Degrees')
            ax.grid(True)
            ax.legend()

            # Subplot 4: Chord distribution
            ax = axes[1, 1]
            XXRC  = Rhub_oR + (1 - Rhub_oR) * np.sin(np.arange(61) * np.pi / (2 * 60))
            XXCoD = InterpolateChord(RC, CoD, XXRC)
            ax.plot(XXRC,  XXCoD, 'b')
            ax.plot(XXRC, -XXCoD, 'b')
            ax.plot(RC,  CoD, 'b.', markersize=8)
            ax.plot(RC, -CoD, 'b.', markersize=8)
            ax.set_xlabel('r/R')
            ax.set_ylabel('c/R')
            ax.grid(True)

            plt.tight_layout()
            plt.show()
        except ImportError:
            pass

    # ------------------------------------------------- Create text reports

    # --------------------------------------------- Make OpenProp_Input.txt
    filename_input = filename + '_Input.txt'
    with open(filename_input, 'wt') as fid:
        fid.write(f'\t\t\t\t\t {filename_input} \n\n')
        fid.write('\t\t\t\t\t OpenProp Input Table\n\n')
        fid.write(f'Date and time: {Date_string}\n\n')

        fid.write(f'{Mp:.0f} \tNumber of Vortex Panels over the Radius\n')
        fid.write(f'{Hub_flag:.0f} \tHub Image Flag: 1=YES, 0=NO\n')
        fid.write(f'{Duct_flag:.0f} \tDuct Flag:      1=YES, 0=NO\n')
        fid.write(f'{Rduct_oR * 2 * R:.3f} \tDuct Diameter\n')
        fid.write(f'{Rhv:.1f} \tHub Vortex Radius/Hub Radius\n')
        fid.write(f'{Z:.0f} \tNumber of Blades\n')
        fid.write(f'{Js:.3f} \tAdvance Coefficient Based on Ship Speed, Js\n')
        fid.write(f'{CTdes:.3f} \tDesired Thrust Coefficient, Ct\n')
        fid.write(f'{TAU:.3f} \tDesired Thrust Ratio, tau\n')
        fid.write(f'{CDd:.3f} \tDuct Section Drag Coefficient, CDd\n')
        fid.write(f'{HUF:.0f} \tHub Unloading Factor: 0 = optimum\n')
        fid.write(f'{TUF:.0f} \tTip Unloading Factor: 1 = Reduced Loading\n')
        fid.write('r/R  \t  C/D  \t   XCD\t    Va/Vs  Vt/Vs\n')

        N_R0 = len(XR)
        for i in range(N_R0):
            fid.write(f'{XR[i]:6.5f}  {XCoD[i]:6.5f}  '
                      f'{float(XCD[i] if np.ndim(XCD) > 0 else XCD):6.5f}  '
                      f'{XVA[i]:6.2f}  {XVT[i]:6.4f}\n')

        fid.write('\nr/R \t [ ], input radial position / propeller radius.\n')
        fid.write('c/D \t [ ], input section chord-length / propeller diameter.\n')
        fid.write('Cd \t [ ], input section drag coefficient.\n')
        fid.write('Va \t [ ], input axial inflow velocity / ship velocity.\n')
        fid.write('Vt \t [ ], input tangential inflow velocity / ship velocity.\n')

    # -------------------------------------------- Make OpenProp_Output.txt
    filename_output = filename + '_Output.txt'
    with open(filename_output, 'wt') as fid:
        fid.write(f'\t\t\t\t\t {filename_output} \n\n')
        fid.write('\t\t\t\t\t OpenProp Output Table\n\n')
        fid.write(f'Date and time: {Date_string}\n\n')

        fid.write(f'Js \t= {Js:5.4f}\n')
        fid.write(f'Ct \t= {CT:5.4f}\n')
        fid.write(f'Cq \t= {CQ:5.4f}\n')
        fid.write(f'Cp \t= {CP:5.4f}\n')
        fid.write(f'VMIV \t= {VMIV:5.4f}\n')
        if Propeller_flag == 1:
            fid.write(f'Kt \t= {KT:5.4f}\n')
            fid.write(f'Kq \t= {KQ:5.4f}\n')
            fid.write(f'Eff \t= {EFFY:5.4f}\n')
        fid.write(f'Tau \t= {TAU:5.4f}\n')
        fid.write(f'Duct Circulation \t= {Gd:5.4f}\n')

        fid.write('\nOutput at the control points for the propeller \n\n')
        fid.write('r/R\t\t G\t\t\t Va\t\t Vt\t\t Ua\t\t '
                  'Ua(ring)\t Ut\t\t Beta\t BetaI\t c/D\t Cd\n')

        for i in range(Mp):
            fid.write(f'{RC[i]:5.5f}  {G[i]:5.6f}  {VAC[i]:5.5f}  '
                      f'{VTC[i]:5.4f}  {UASTAR[i]:5.5f}  '
                      f'{Gd * UADIF[i]:5.5f}  {UTSTAR[i]:5.5f}  '
                      f'{Beta_c[i]:5.3f}  {BetaI_c[i]:5.3f}  '
                      f'{CoD[i]:5.5f}  {CD[i]:5.5f}\n')

        if Duct_flag == 1:
            fid.write('\nOutput on the duct ring vortices \n\n')
            fid.write('X/R\t\t G\t\t\t UA/VS\t UR/VS\n')
            for i in range(len(XdRING)):
                fid.write(f'{XdRING[i]:5.5f}  {Gd * GdRING[i]:5.6f}  '
                          f'{UARING[i]:5.5f}  {URRING[i]:5.4f}\n')
        else:
            fid.write('\nThe propeller does not have a duct.\n\n')

        fid.write('\nJs \t [ ], advance coefficient.\n')
        fid.write('Ct \t [ ], required thrust coefficient.\n')
        fid.write('Cp \t [ ], power coefficient. Cp = Cq*pi/J.\n')
        fid.write('Kt \t [ ], thrust coefficient. Kt = Ct*Js^2*pi/8.\n')
        fid.write('Kq \t [ ], torque coefficient. Kq = Cq*Js^2*pi/16.\n')
        fid.write('VMIV \t [ ], volumetric mean inflow velocity / ship velocity.\n')
        fid.write('Eff \t [ ], efficiency = Ct*VMIV/Cp.\n')
        fid.write('Tau \t [ ], thrust ratio = propeller thrust / total thrust.\n')

        fid.write('\nr/R \t [ ], radial position of control points / propeller radius.\n')
        fid.write('G  \t [ ], section circulation / 2*pi*R.\n')
        fid.write('Va \t [ ], axial inflow velocity / ship velocity.\n')
        fid.write('Vt \t [ ], tangential inflow velocity / ship velocity.\n')
        fid.write('Ua \t [ ], induced axial velocity / ship velocity.\n')
        fid.write('Ut \t [ ], induced tangential velocity / ship velocity.\n')
        fid.write('beta \t [deg], flow angle.\n')
        fid.write('betaI \t [deg], hydrodynamic Pitch angle.\n')
        fid.write('c/D \t [ ], section chord-length / propeller diameter.\n')
        fid.write('Cd \t [ ], section drag coefficient.\n')

        fid.write('\nX/R \t [ ], axial location of duct vortex rings / propeller radius.\n')
        fid.write('G  \t [ ], duct vortex ring circulation / 2*pi*R.\n')
        fid.write('UA/VS \t [ ], axial inflow induced by propeller / ship velocity.\n')
        fid.write('UR/VS \t [ ], radial inflow induced by propeller / ship velocity.\n')

    # ----------------------------- Calculate Propeller Section Performance
    w = 2 * np.pi * n                 # angular velocity [rad/s]
    dV = dVs * Vs

    Vstar  = np.zeros(Mp)
    Gamma  = np.zeros(Mp)
    CL_sec = np.zeros(Mp)
    Sigma  = np.zeros(Mp)
    dBetai = np.zeros(Mp)

    for k in range(Mp):
        Vstar[k] = (np.sqrt((VAC[k] + UASTAR[k])**2 +
                            (w * R * RC[k] / Vs + VTC[k] + UTSTAR[k])**2) * Vs)

        Gamma[k]  = G[k] * 2 * np.pi * R * Vs

        CL_sec[k] = 2 * Gamma[k] / (Vstar[k] * CoD[k] * D)

        Sigma[k]  = ((Patm + rho * g * (H - RC[k] * R) - Pv) /
                     (rho * Vstar[k]**2 / 2))

        dBetai[k] = (np.degrees(np.arctan((TANBIC[k] * w * RC[k] * R + dV) /
                                          (w * RC[k] * R))) -
                     np.degrees(np.arctan((TANBIC[k] * w * RC[k] * R - dV) /
                                          (w * RC[k] * R))))

    # --------------------------------------- Make OpenProp_Performance.txt
    filename_performance = filename + '_Performance.txt'
    with open(filename_performance, 'wt') as fid:
        fid.write(f'\t\t\t\t\t {filename_performance} \n\n')
        fid.write('\t\t\t\t\t OpenProp Performance Table\n\n')
        fid.write(f'Date and time: {Date_string}\n\n')

        fid.write(' r/R\t V*\t beta\t betai\t Gamma\t CL\t Sigma\t dBetai\n')
        for k in range(Mp):
            fid.write(f'{RC[k]:.3f}\t {Vstar[k]:.2f}\t {Beta_c[k]:.2f}\t '
                      f'{BetaI_c[k]:.2f}\t {Gamma[k]:.4f}\t {CL_sec[k]:.3f}\t '
                      f'{Sigma[k]:.3f}\t {dBetai[k]:.2f}\n')

        fid.write('\nr/R \t [ ], radial position of control points / propeller radius.\n')
        fid.write('V* \t [m/s], total inflow velocity.\n')
        fid.write('beta \t [deg], undisturbed flow angle.\n')
        fid.write('betai \t [deg], hydrodynamic Pitch angle.\n')
        fid.write('Gamma \t [m^2/s], vortex sheet strength.\n')
        fid.write('CL \t [ ], section lift coefficient.\n')
        fid.write('Sigma \t [ ], cavitation number.\n')
        fid.write('d_alpha  [deg], inflow variation bucket width.\n')
