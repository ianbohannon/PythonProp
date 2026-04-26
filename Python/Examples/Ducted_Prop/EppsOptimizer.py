# Port target: SourceCode/EppsOptimizer.m
"""Epps lifting-line propeller/turbine design optimizer — full port of EppsOptimizer.m."""

import sys
import numpy as np
from scipy.interpolate import pchip_interpolate
from scipy.linalg import solve as linsolve

from LLPanelRadii          import LLPanelRadii
from RepairSpline          import RepairSpline, RepairSplineMatrix
from InterpolateChord      import InterpolateChord
from GeometryFoil2D        import GeometryFoil2D
from Horseshoe110628       import Horseshoe110628
from Horseshoe_intr_110830 import Horseshoe_intr_110830
from Duct_Influence        import Duct_Influence
from Duct_Thrust           import Duct_Thrust
from Forces                import Forces


# ---------------------------------------------------------------------------
# Turbine actuator-disk theory stub
# ---------------------------------------------------------------------------
def _Turbine_ADS_Theory(L, Z, CDoCL, RC):
    """Stub for turbine actuator-disk initialisation (Betz optimal)."""
    RC = np.asarray(RC, dtype=float)
    Mp = len(RC)
    CPBetz = 16.0 / 27.0          # Betz limit
    BetzRC = RC.copy()
    BetzG  = np.zeros(Mp)
    BetzUA = np.zeros(Mp)
    BetzUT = np.zeros(Mp)
    BetzTAN = (np.ones(Mp)) / (L * RC)
    BetzGRC = np.zeros(Mp)
    return CPBetz, BetzRC, BetzG, BetzUA, BetzUT, BetzTAN, BetzGRC


def EppsOptimizer(inp):
    """Run the Epps lifting-line design optimisation.

    Full port of ``SourceCode/EppsOptimizer.m`` (Brenden Epps, 2011).

    Determines the optimum circulation, chord, and thickness distributions
    that satisfy the input operating conditions using a variational
    optimisation algorithm for the propeller case (Coney, 1989) or a hybrid
    blade-element-momentum / vortex-lattice method for the turbine case
    (Epps & Kimball, 2011).

    Parameters
    ----------
    inp : dict
        Input parameter dictionary assembled by the caller (e.g.
        ``Ducted_Prop_input.py``).  See source for the full list of
        recognised keys.

    Returns
    -------
    design : dict
        Design output dictionary with keys matching the MATLAB ``design``
        struct (``RC``, ``G``, ``UASTAR``, ``UTSTAR``, ``VSTAR``,
        ``TANBIC``, ``CoD``, ``CL``, ``CD``, ``KT``, ``KQ``, ``EFFY``,
        etc.).
    """
    # =========================================================================
    # Unpack input variables
    # =========================================================================
    def _get(key, default):
        return inp.get(key, default)

    # --------------------------------------------------------- Geometry inputs
    Z  = inp["Z"]                    # number of blades
    Mp = int(_get("Mp", 20))
    Vs = _get("Vs", 1.0)             # ship speed [m/s]

    if   "D"    in inp: R = inp["D"] / 2.0
    elif "R"    in inp: R = inp["R"]
    else:               R = 1.0

    if   "Dhub"  in inp: Rhub = inp["Dhub"] / 2.0
    elif "Rhub"  in inp: Rhub = inp["Rhub"]
    else:                Rhub = 0.2 * R

    Rcirc = _get("Rcirc", Rhub)
    Rroot = _get("Rroot", Rhub)

    if Rcirc < Rhub:
        print("ERROR: Rcirc must be >= Rhub.  Setting Rcirc = Rhub.")
        Rcirc = Rhub
    if Rroot < Rcirc:
        print("ERROR: Rroot must be >= Rcirc. Setting Rroot = Rcirc.")
        Rroot = Rcirc

    # ----- Blade geometry -----
    if "XR" in inp:
        XR  = np.asarray(inp["XR"], dtype=float)
        X1  = np.ones_like(XR)
        X0  = np.zeros_like(XR)

        if "XCoD" in inp:
            XCoD = np.asarray(inp["XCoD"], dtype=float)
            if   "Xt0oD" in inp: Xt0oD = np.asarray(inp["Xt0oD"], dtype=float)
            elif "t0oc0" in inp: Xt0oD = np.asarray(inp["t0oc0"], dtype=float) * XCoD
            else:                Xt0oD = 0.1 * XCoD
        else:
            XXR    = np.array([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0])
            XXCoD  = np.array([0.1600, 0.1818, 0.2024, 0.2196, 0.2305,
                               0.2311, 0.2173, 0.1806, 0.1387, 0.0010])
            Xt0oc0 = np.array([0.2056, 0.1551, 0.1181, 0.0902, 0.0694,
                               0.0541, 0.0419, 0.0332, 0.0324, 0.0000])
            XCoD  = pchip_interpolate(XXR, XXCoD,  XR)
            t0oc0 = pchip_interpolate(XXR, Xt0oc0, XR)
            Xt0oD = inp["Xt0oD"] if "Xt0oD" in inp else t0oc0 * XCoD

        XVA  = np.asarray(_get("XVA",  X1), dtype=float)
        XVT  = np.asarray(_get("XVT",  X0), dtype=float)
        dXVA = np.asarray(_get("dXVA", X0), dtype=float)
    else:
        XR    = np.array([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0])
        X1    = np.ones_like(XR);  X0 = np.zeros_like(XR)
        XCoD  = np.array([0.1600, 0.1818, 0.2024, 0.2196, 0.2305,
                          0.2311, 0.2173, 0.1806, 0.1387, 0.0010])
        t0oc0 = np.array([0.2056, 0.1551, 0.1181, 0.0902, 0.0694,
                          0.0541, 0.0419, 0.0332, 0.0324, 0.0000])
        Xt0oD = t0oc0 * XCoD
        XVA   = X1.copy()
        XVT   = X0.copy()
        dXVA  = X0.copy()

    # ---- Inflow velocity profiles ----
    if "ri" in inp:
        RI   = np.asarray(inp["ri"],   dtype=float) / R
        VAI  = np.asarray(_get("VAI",  np.ones_like(RI)),  dtype=float)
        VTI  = np.asarray(_get("VTI",  np.zeros_like(RI)), dtype=float)
        dVAI = np.asarray(_get("dVAI", np.zeros_like(RI)), dtype=float)
    else:
        RI   = XR.copy()
        VAI  = XVA.copy()
        VTI  = XVT.copy()
        dVAI = dXVA.copy()

    VAI = RepairSpline(RI, VAI)
    VTI = RepairSpline(RI, VTI)

    # ---- Section drag ----
    if "XCD" in inp:
        XCD = np.asarray(inp["XCD"], dtype=float)
        if XCD.ndim == 0 or len(XCD) == 1:
            XCD = float(XCD) * np.ones_like(XR)
    else:
        XCD = 0.008 * np.ones_like(XR)

    # ---- Computational inputs ----
    ITER = int(_get("ITER", 50))
    HUF  = _get("HUF",  0.0)
    TUF  = _get("TUF",  0.0)
    Rhv  = _get("Rhv",  0.5)

    # ---- Cavitation inputs ----
    rho  = _get("rho",  1000.0)
    dVs  = _get("dVs",  0.30)
    H    = _get("H",    3.048)
    g    = _get("g",    9.81)
    Patm = _get("Patm", 101325.0)
    Pv   = _get("Pv",   2500.0)

    SIGMAs = (Patm + rho * g * H - Pv) / (0.5 * rho * Vs ** 2)

    # ---- Flags ----
    Propeller_flag = int(inp["Propeller_flag"])
    Viscous_flag   = int(inp["Viscous_flag"])
    Hub_flag       = int(_get("Hub_flag",   0))
    Duct_flag      = int(_get("Duct_flag",  0))
    Chord_flag     = int(_get("Chord_flag", 0))
    ChordMethod    = _get("ChordMethod", "CLmax")
    Plot_flag      = int(_get("Plot_flag",  0))
    Wake_flag      = int(_get("Wake_flag",  0))

    # ---- Tip-speed ratio / advance coefficient ----
    if Propeller_flag == 1:
        Js = float(inp["Js"])
        L  = np.pi / Js
    else:
        L  = float(inp["L"])
        Js = np.pi / L

    D = 2.0 * R
    n = Vs / (Js * D)       # [rev/s]
    N = 60.0 * n             # [RPM]

    # ---- Duct ----
    if Duct_flag == 1:
        TAU = float(_get("TAU", 1.0))

        if   "Rduct_oR" in inp: Rduct_oR = float(inp["Rduct_oR"])
        elif "Rduct"    in inp: Rduct_oR = float(inp["Rduct"]) / R
        else:                   Rduct_oR = 1.0

        if   "Cduct_oR" in inp: Cduct_oR = float(inp["Cduct_oR"])
        elif "Cduct"    in inp: Cduct_oR = float(inp["Cduct"]) / R
        else:                   Cduct_oR = 1.0

        if   "Xduct_oR" in inp: Xduct_oR = float(inp["Xduct_oR"])
        elif "Xduct"    in inp: Xduct_oR = float(inp["Xduct"]) / R
        else:                   Xduct_oR = 0.0

        CDd = float(_get("CDd", 0.008))
    else:
        TAU      = 1.0
        Rduct_oR = 1.0
        CDd      = 0.0
        Cduct_oR = 1.0
        Xduct_oR = 0.0

    # ---- Thrust/torque requirement ----
    if Propeller_flag == 1:
        if   "THRUST" in inp: CTdes = float(inp["THRUST"]) / (0.5 * rho * Vs**2 * np.pi * R**2)
        elif "CTDES"  in inp: CTdes = float(inp["CTDES"])
        elif "CT"     in inp: CTdes = float(inp["CT"])
        elif "KTDES"  in inp: CTdes = float(inp["KTDES"]) * (8.0/np.pi) / Js**2
        elif "KT"     in inp: CTdes = float(inp["KT"])    * (8.0/np.pi) / Js**2
        else:                 CTdes = 0.0

        if   "TORQUE" in inp: CQdes = float(inp["TORQUE"]) / (0.5 * rho * Vs**2 * np.pi * R**3)
        elif "CQDES"  in inp: CQdes = float(inp["CQDES"])
        elif "CQ"     in inp: CQdes = float(inp["CQ"])
        elif "KQDES"  in inp: CQdes = float(inp["KQDES"]) * (16.0/np.pi) / Js**2
        elif "KQ"     in inp: CQdes = float(inp["KQ"])    * (16.0/np.pi) / Js**2
        else:                 CQdes = 0.0

        TorqueSpec_flag = 0 if CTdes > 0 else 1

        CTPdes = CTdes *     TAU
        CTDdes = CTdes * (1.0 - TAU)
    else:
        if   "THRUSTduct" in inp: CTDdes = float(inp["THRUSTduct"]) / (0.5*rho*Vs**2*np.pi*R**2)
        elif "CTD"        in inp: CTDdes = float(inp["CTD"])
        elif "KTD"        in inp: CTDdes = float(inp["KTD"]) * (8.0/np.pi) / Js**2
        else:                     CTDdes = 0.0

        TAU             = 0.0
        CTPdes          = 0.0
        TorqueSpec_flag = 0       # not used for turbine
        CQdes           = 0.0

    # ---- Chord optimisation setup ----
    if Chord_flag == 1:
        if "XCLmax" in inp:
            XCLmax = np.asarray(inp["XCLmax"], dtype=float)
            if XCLmax.ndim == 0 or len(XCLmax) == 1:
                XCLmax = float(XCLmax) * np.ones_like(XR)
        else:
            XCLmax = 0.5 + (0.2 - 0.5) / (1.0 - XR[0]) * (XR - XR[0])

        CDoCL  = float(np.mean(np.abs(XCD / XCLmax)))
        EARspec = float(_get("EAR", 0.0))

        if ChordMethod == "FAST2011dCTP":
            Vh     = float(_get("Vh", Vs))
            Jh     = Js
            if   "THRUSTh" in inp: CTDESh = float(inp["THRUSTh"]) / (0.5*rho*Vh**2*np.pi*R**2)
            elif "CTDESh"  in inp: CTDESh = float(inp["CTDESh"])
            elif "CTh"     in inp: CTDESh = float(inp["CTh"])
            else:                  CTDESh = CTdes
            SIGMAh = (Patm + rho*g*H - Pv) / (0.5*rho*Vh**2)
    else:
        XCLmax  = np.ones_like(XR)
        CDoCL   = 0.0
        EARspec = 0.0

    if Propeller_flag == 0:
        XCLmax = -np.abs(XCLmax)

    # ---- Viscous_flag ----
    if Viscous_flag == 0:
        XCD   = np.zeros_like(XR)
        CDoCL = 0.0
        CDd   = 0.0

    # ---- Foil section parameters ----
    Meanline  = _get("Meanline",  "NACA a=0.8 (modified)")
    Thickness = _get("Thickness", "NACA 65A010")

    if isinstance(Meanline, list):
        if len(Meanline) != len(XR):
            print("<ERROR> Meanline given as list but different length as XR.")
            return {}
        Xf0octilde = np.zeros_like(XR)
        XCLItilde  = np.zeros_like(XR)
        for j in range(len(XR)):
            f0, cli, *_ = GeometryFoil2D(Meanline[j], Thickness[j])
            Xf0octilde[j] = f0
            XCLItilde[j]  = cli
    else:
        f0octilde_s, CLItilde_s, *_ = GeometryFoil2D(Meanline, Thickness)
        Xf0octilde = f0octilde_s * np.ones_like(XR)
        XCLItilde  = CLItilde_s  * np.ones_like(XR)

    # =========================================================================
    # Initialise design
    # =========================================================================
    Rhub_oR  = Rhub  / R
    Rroot_oR = Rroot / R
    Rcirc_oR = Rcirc / R

    # Volumetric Mean Inflow Velocity
    XRtemp  = np.linspace(Rhub_oR, 1.0, 100)
    XVAtemp = pchip_interpolate(RI, VAI, XRtemp)
    VMIV    = 2.0 * np.trapezoid(XRtemp * XVAtemp, XRtemp) / (1.0 - Rhub_oR**2)

    # Vortex and control-point radii
    RC, RV, DR = LLPanelRadii(Mp, Rhub_oR, Hub_flag, Duct_flag)

    # Interpolate inflow / section properties at control points
    VAC  = pchip_interpolate(RI, VAI,  RC)
    dVAC = pchip_interpolate(RI, dVAI, RC)
    VTC  = pchip_interpolate(RI, VTI,  RC)
    CD   = pchip_interpolate(XR, XCD,  RC)
    t0oD = pchip_interpolate(XR, Xt0oD,    RC)
    CLmax = pchip_interpolate(XR, XCLmax, RC)

    f0octilde = pchip_interpolate(XR, Xf0octilde, RC)
    CLItilde  = pchip_interpolate(XR, XCLItilde,  RC)

    if (abs(XR[-1] - 1.0) < 1e-4) and (XCoD[-1] <= 0.01):
        CoD = InterpolateChord(XR, XCoD, RC)
    else:
        CoD = pchip_interpolate(XR, XCoD, RC)

    # ---- Initial estimates ----
    if Propeller_flag == 1:
        G      = np.zeros(Mp)
        UASTAR = np.full(Mp, 0.5 * (np.sqrt(1.0 + CTPdes) - 1.0))
        UTSTAR = np.zeros(Mp)
        if VMIV < 0.05:
            UASTAR = np.full(Mp, 0.5 * np.sqrt(CTPdes))
    else:
        CPBetz, BetzRC, BetzG, BetzUA, BetzUT, BetzTAN, BetzGRC = \
            _Turbine_ADS_Theory(L, Z, CDoCL, RC)
        G      = BetzGRC.copy()
        UASTAR = pchip_interpolate(BetzRC, BetzUA, RC)
        UTSTAR = pchip_interpolate(BetzRC, BetzUT, RC)

    TANBC  = VAC / (L * RC + VTC)
    TANBIC = (VAC + UASTAR) / (L * RC + VTC + UTSTAR)
    VSTAR  = np.sqrt((VAC + UASTAR)**2 + (L * RC + VTC + UTSTAR)**2)
    dVdG   = np.zeros((Mp, Mp))

    if Chord_flag == 1:
        if Propeller_flag == 1:
            CoD = 0.1 * np.ones(Mp)
        else:
            with np.errstate(divide='ignore', invalid='ignore'):
                CoD = np.where(VSTAR * CLmax != 0, 2.0 * np.pi * G / (VSTAR * CLmax), 0.0)

    # ---- Initial Horseshoe Influence Functions ----
    if Wake_flag == 0:
        UAHIF, UTHIF = Horseshoe110628(Mp, Z, TANBIC, RC, RV,
                                       Hub_flag, Rhub_oR,
                                       Duct_flag, Rduct_oR)
    else:
        print("ERROR: Wake_Geometry / Wake_Horseshoe not supported.")
        return {}

    # ---- Initialise duct variables ----
    if Duct_flag == 1:
        print(" ")
        print("Computing rotor-duct interaction...be patient...")
        print(" ")
        XdRING, GdRING, UADIF = Duct_Influence(Rduct_oR, Cduct_oR, Xduct_oR, RC)

        VARING = pchip_interpolate(RI, VAI, np.array([Rduct_oR]))[0]

        Gd     = 0.0
        UADUCT = UADIF * Gd

        DAHIF_times_TANBIC, DTHIF, DRHIF_times_TANBIC = \
            Horseshoe_intr_110830(XdRING, Rduct_oR, RC, np.ones(Mp), RV,
                                  Z, Hub_flag, Rhub_oR, Duct_flag, Rduct_oR)

        DAHIF = np.zeros_like(DAHIF_times_TANBIC)
        DRHIF = np.zeros_like(DRHIF_times_TANBIC)
        for m in range(Mp):
            if abs(TANBIC[m]) > 1e-10:
                DAHIF[:, m] = DAHIF_times_TANBIC[:, m] / TANBIC[m]
                DRHIF[:, m] = DRHIF_times_TANBIC[:, m] / TANBIC[m]
    else:
        Gd       = 1.0
        UADUCT   = np.zeros(Mp)
        CTD      = 0.0
        XdRING   = np.array([0.0])
        GdRING   = np.array([0.0])
        UADIF    = np.zeros(Mp)
        UARING   = np.array([0.0])
        URRING   = np.array([0.0])
        VARING   = 0.0
        DAHIF_times_TANBIC = np.zeros((1, Mp))
        DRHIF_times_TANBIC = np.zeros((1, Mp))
        DAHIF              = np.zeros((1, Mp))
        DRHIF              = np.zeros((1, Mp))

    # ---- Smoothing matrix ----
    Bsmooth = RepairSplineMatrix(RC)

    # =========================================================================
    # Optimiser method flags
    # =========================================================================
    EppsOptimizer02_flag = int(_get("EppsOptimizer02_flag", 1))
    EppsOptimizer23_flag = int(_get("EppsOptimizer23_flag", 0))
    EppsOptimizer53_flag = int(_get("EppsOptimizer53_flag", 0))
    if EppsOptimizer23_flag == 1 or EppsOptimizer53_flag == 1:
        EppsOptimizer02_flag = 0

    # =========================================================================
    # Optimisation loop
    # =========================================================================
    LM      = -1.0
    LM_last = LM
    G_last  = np.zeros(Mp)
    Gd_last = 0.0
    G_iter  = 1
    G_res   = np.ones(Mp)
    Gd_res  = 1.0
    C_res   = 0.0
    relax   = 0.9
    G_TOL   = 1e-4

    if Chord_flag == 1 and ChordMethod in ("FAST2011dCTP", "FAST2011dVAC", "Brizzolara2007"):
        ITER = ITER * 3

    print("--------- Begin circulation optimisation")
    print(" ")

    while G_iter <= ITER and (np.any(G_res > G_TOL) or Gd_res > G_TOL):

        # =====================================================================
        # UPDATE: G, UASTAR, UTSTAR, TANBIC, (duct), LM
        # =====================================================================
        if Propeller_flag == 1:

            # -----------------------------------------------------------------
            # "LL-Linear" (EppsOptimizer02)
            # -----------------------------------------------------------------
            if EppsOptimizer02_flag == 1:
                A = np.zeros((Mp + 1, Mp + 1))
                B = np.zeros(Mp + 1)

                for i in range(Mp):
                    for m in range(Mp):
                        A[i, m] = (UAHIF[m, i] * RC[m] * DR[m]
                                   + UAHIF[i, m] * RC[i] * DR[i]
                                   + LM_last * UTHIF[m, i] * DR[m]
                                   + LM_last * UTHIF[i, m] * DR[i])
                    B[i]        = -(VAC[i] + UADUCT[i]) * RC[i] * DR[i]
                    A[i, Mp]    =  (L * RC[i] + VTC[i]) * DR[i]

                if TorqueSpec_flag == 0:
                    for m in range(Mp):
                        A[Mp, m] = (L * RC[m] + VTC[m] + UTSTAR[m]) * DR[m]
                    B[Mp] = (CTPdes / (4.0 * Z)
                             + (1.0/(2.0*np.pi)) * np.sum(
                                 CD * VSTAR * CoD * (VAC + UADUCT + UASTAR) * DR))
                    if Hub_flag == 1:
                        B[Mp] += (Z / 8.0) * (np.log(1.0/Rhv) + 3.0) * G_last[0]**2
                else:
                    for m in range(Mp):
                        A[Mp, m] = (VAC[m] + UADUCT[m] + UASTAR[m]) * RC[m] * DR[m]
                    B[Mp] = (CQdes / (4.0 * Z)
                             - (1.0/(2.0*np.pi)) * np.sum(
                                 CD * VSTAR * CoD * (L*RC + VTC + UTSTAR) * RC * DR))

                try:
                    GLM = linsolve(A, B)
                except Exception:
                    GLM = np.full(Mp + 1, np.nan)

                G   = GLM[:Mp]
                LM  = GLM[Mp]

                UASTAR = UAHIF @ G
                UTSTAR = UTHIF @ G

                TANBIC = (VAC + UADUCT + UASTAR) / (L*RC + VTC + UTSTAR)

                if np.any(np.isnan(GLM)) or not np.all(np.isreal(GLM)) or np.max(G - G_last) > 10:
                    G      = np.zeros(Mp)
                    UASTAR = np.zeros(Mp)
                    UTSTAR = np.zeros(Mp)
                    TANBIC = TANBC.copy()
                    print(" ")
                    print("<WARNING> GLM == NaN or imaginary... switching to Newton solver...")
                    print(" ")
                    EppsOptimizer02_flag = 0
                    EppsOptimizer23_flag = 1

                TANBICsmooth = TANBIC @ Bsmooth

                if Duct_flag == 1:
                    for m in range(Mp):
                        if abs(TANBICsmooth[m]) > 1e-10:
                            DAHIF[:, m] = DAHIF_times_TANBIC[:, m] / TANBICsmooth[m]
                            DRHIF[:, m] = DRHIF_times_TANBIC[:, m] / TANBICsmooth[m]
                    UARING = DAHIF @ G
                    URRING = DRHIF @ G
                    if TorqueSpec_flag == 1:
                        CTP = 4.0 * Z * np.sum(
                            G * (L*RC + VTC + UTSTAR) * DR
                            - (1.0/(2.0*np.pi)) * VSTAR * CoD * CD * (VAC + UADUCT + UASTAR) * DR
                        )
                        if Hub_flag == 1:
                            CTP -= 0.5 * (np.log(1.0/Rhv) + 3.0) * (Z * G[0])**2
                        CTDdes = ((1.0 - TAU) / TAU) * CTP
                    _, Gd = Duct_Thrust(XdRING, Rduct_oR, VARING,
                                        UARING, URRING, GdRING, Gd, CDd, CTDdes)
                    UADUCT = UADIF * Gd

            # -----------------------------------------------------------------
            # "LL-Newton" (EppsOptimizer23 / EppsOptimizer53)
            # -----------------------------------------------------------------
            if EppsOptimizer23_flag == 1 or EppsOptimizer53_flag == 1:
                RNS = np.zeros(4*Mp + 1)
                JNS = np.zeros((4*Mp + 1, 4*Mp + 1))

                UASTARtemp = UAHIF @ G
                UTSTARtemp = UTHIF @ G

                for i in range(Mp):
                    RNS[i] = ((VAC[i] + UADUCT[i] + UASTAR[i]) * RC[i] * DR[i]
                              + np.sum(UAHIF[:, i] * G * RC * DR)
                              + LM * (np.sum(UTHIF[:, i] * G * DR)
                                      + (L*RC[i] + VTC[i] + UTSTAR[i]) * DR[i]))
                    RNS[i + Mp]   = UASTAR[i] - UASTARtemp[i]
                    RNS[i + 2*Mp] = UTSTAR[i] - UTSTARtemp[i]
                    RNS[i + 3*Mp] = (TANBIC[i]
                                     - (VAC[i] + UADUCT[i] + UASTAR[i])
                                       / (L*RC[i] + VTC[i] + UTSTAR[i]))

                if TorqueSpec_flag == 0:
                    RNS[1 + 4*Mp - 1] = (
                        np.sum((L*RC + VTC + UTSTAR) * G * DR
                               - (1.0/(2.0*np.pi)) * CD * CoD * VSTAR
                               * (VAC + UADUCT + UASTAR) * DR)
                        - CTPdes / (4.0 * Z)
                    )
                    if Hub_flag == 1 and EppsOptimizer23_flag == 1:
                        RNS[4*Mp] -= (Z/8.0) * (np.log(1.0/Rhv)+3.0) * G_last[0]**2
                    elif Hub_flag == 1 and EppsOptimizer53_flag == 1:
                        RNS[0]    -= (Z/4.0) * (np.log(1.0/Rhv)+3.0) * (G[0] * LM)
                        RNS[4*Mp] -= (Z/8.0) * (np.log(1.0/Rhv)+3.0) * G[0]**2
                else:
                    RNS[4*Mp] = (
                        np.sum((VAC + UADUCT + UASTAR) * G * RC * DR
                               + (1.0/(2.0*np.pi)) * CD * CoD * VSTAR
                               * (L*RC + VTC + UTSTAR) * RC * DR)
                        - CQdes / (4.0 * Z)
                    )

                for i in range(Mp):
                    JNS[i, :Mp] = UAHIF[:, i] * RC * DR + LM * UTHIF[:, i] * DR
                    JNS[i, i + Mp]   += RC[i] * DR[i]
                    JNS[i, i + 2*Mp] += LM * DR[i]
                    JNS[i, 4*Mp] = ((L*RC[i] + VTC[i] + UTSTAR[i]) * DR[i]
                                    + np.sum(UTHIF[:, i] * G * DR))

                    JNS[i + Mp,  :Mp]        = -UAHIF[i, :Mp]
                    JNS[i + Mp,  i + Mp]     = 1.0
                    JNS[i + 2*Mp, :Mp]       = -UTHIF[i, :Mp]
                    JNS[i + 2*Mp, i + 2*Mp]  = 1.0

                    denom = L*RC[i] + VTC[i] + UTSTAR[i]
                    if abs(denom) > 1e-10:
                        JNS[i + 3*Mp, i + Mp]   = -1.0 / denom
                        JNS[i + 3*Mp, i + 2*Mp] = (VAC[i]+UADUCT[i]+UASTAR[i]) / denom**2
                    JNS[i + 3*Mp, i + 3*Mp] = 1.0

                    if TorqueSpec_flag == 0:
                        JNS[4*Mp, i]       = (L*RC[i] + VTC[i] + UTSTAR[i]) * DR[i]
                        JNS[4*Mp, i + Mp]  = -(1.0/(2.0*np.pi)) * CD[i]*CoD[i]*VSTAR[i]*DR[i]
                        JNS[4*Mp, i + 2*Mp] = G[i] * DR[i]
                        if Hub_flag == 1 and EppsOptimizer53_flag == 1:
                            JNS[0, 0]      -= (Z/4.0) * (np.log(1.0/Rhv)+3.0) * LM
                            JNS[0, 4*Mp]   -= (Z/4.0) * (np.log(1.0/Rhv)+3.0) * G[0]
                            JNS[4*Mp, 0]   -= (Z/4.0) * (np.log(1.0/Rhv)+3.0) * G[0]
                    else:
                        JNS[4*Mp, i]       = (VAC[i]+UADUCT[i]+UASTAR[i]) * RC[i]*DR[i]
                        JNS[4*Mp, i + Mp]  = G[i] * RC[i] * DR[i]
                        JNS[4*Mp, i+2*Mp]  = (1.0/(2.0*np.pi))*CD[i]*CoD[i]*VSTAR[i]*RC[i]*DR[i]

                try:
                    DX = linsolve(JNS, -RNS)
                except Exception:
                    DX = np.full(4*Mp + 1, np.nan)

                if np.any(np.isnan(DX)) or not np.all(np.isreal(DX)) or np.any(np.abs(DX) > 999):
                    print(f"\n!!! ITERATION {G_iter} CRASH DIAGNOSTIC !!!")
                    print(f"DX stats: min={np.nanmin(DX):.2e}, max={np.nanmax(DX):.2e}, has_nan={np.any(np.isnan(DX))}")
                    print(f"Condition(JNS): {np.linalg.cond(JNS):.2e}")
                    print(f"L*RC+VTC+UTSTAR min: {np.min(L*RC + VTC + UTSTAR):.6e}")
                    print(f"UAHIF has NaN: {np.any(np.isnan(UAHIF))}")
                    print(f"UTHIF has NaN: {np.any(np.isnan(UTHIF))}")
                    print(f"CTPdes = {CTPdes:.6f}, CTdes = {CTdes:.6f}")
                    G      = np.zeros(Mp)
                    UASTAR = np.zeros(Mp)
                    UTSTAR = np.zeros(Mp)
                    TANBIC = TANBC.copy()
                    print(" ")
                    print("<WARNING> DX == NaN or imaginary... crash avoided...")
                    print(" ")
                    G_iter = 999

                G      = G      + relax * DX[:Mp]
                UASTAR = UASTAR + relax * DX[Mp:2*Mp]
                UTSTAR = UTSTAR + relax * DX[2*Mp:3*Mp]
                TANBIC = TANBIC + relax * DX[3*Mp:4*Mp]
                LM     = LM     + relax * DX[4*Mp]

                if np.any(np.isnan(DX)) or not np.all(np.isreal(DX)) or np.any(np.abs(DX) > 999):
                    G      = np.zeros(Mp)
                    UASTAR = np.zeros(Mp)
                    UTSTAR = np.zeros(Mp)
                    TANBIC = TANBC.copy()
                    print(" ")
                    print("<WARNING> DX == NaN or imaginary... crash avoided...")
                    print(" ")
                    G_iter = 999

                TANBICsmooth = TANBIC @ Bsmooth

                if Duct_flag == 1:
                    for m in range(Mp):
                        if abs(TANBICsmooth[m]) > 1e-10:
                            DAHIF[:, m] = DAHIF_times_TANBIC[:, m] / TANBICsmooth[m]
                            DRHIF[:, m] = DRHIF_times_TANBIC[:, m] / TANBICsmooth[m]
                    UARING = DAHIF @ G
                    URRING = DRHIF @ G
                    if TorqueSpec_flag == 1:
                        CTP = 4.0 * Z * np.sum(
                            G * (L*RC + VTC + UTSTAR) * DR
                            - (1.0/(2.0*np.pi)) * VSTAR * CoD * CD * (VAC + UADUCT + UASTAR) * DR
                        )
                        if Hub_flag == 1:
                            CTP -= 0.5 * (np.log(1.0/Rhv) + 3.0) * (Z * G[0])**2
                        CTDdes = ((1.0 - TAU) / TAU) * CTP
                    _, Gd = Duct_Thrust(XdRING, Rduct_oR, VARING,
                                        UARING, URRING, GdRING, Gd, CDd, CTDdes)
                    UADUCT = UADIF * Gd

        else:
            # -----------------------------------------------------------------
            # TURBINE optimisation ("Robust" method, EppsOptimizer06)
            # -----------------------------------------------------------------
            RNS = np.zeros(4*Mp)
            JNS = np.zeros((4*Mp, 4*Mp))

            UASTARtemp = UAHIF @ G
            UTSTARtemp = UTHIF @ G

            for i in range(Mp):
                if Chord_flag == 1 and ChordMethod == "CLmax":
                    RNS[i] = ((VAC[i]+UADUCT[i]+2*UASTAR[i]) * (VAC[i]+UADUCT[i]+UASTAR[i])
                              - (L*RC[i]+VTC[i]+2*UTSTAR[i]) * UTSTAR[i]
                              + (VAC[i]+UADUCT[i]+2*UASTAR[i]) * (L*RC[i]+VTC[i]+2*UTSTAR[i])
                              * CD[i] / CLmax[i])
                else:
                    RNS[i] = ((VAC[i]+UADUCT[i]+2*UASTAR[i]) * (VAC[i]+UADUCT[i]+UASTAR[i])
                              - (L*RC[i]+VTC[i]+2*UTSTAR[i]) * UTSTAR[i])

                RNS[i + Mp]   = UASTAR[i] - UASTARtemp[i]
                RNS[i + 2*Mp] = UTSTAR[i] - UTSTARtemp[i]
                denom = L*RC[i] + VTC[i] + UTSTAR[i]
                if abs(denom) > 1e-10:
                    RNS[i + 3*Mp] = TANBIC[i] - (VAC[i]+UADUCT[i]+UASTAR[i]) / denom

            for i in range(Mp):
                if Chord_flag == 1 and ChordMethod == "CLmax":
                    JNS[i, i+Mp]   = (3*(VAC[i]+UADUCT[i]) + 4*UASTAR[i]
                                      + 2*(L*RC[i]+VTC[i]+2*UTSTAR[i])*CD[i]/CLmax[i])
                    JNS[i, i+2*Mp] = (-(L*RC[i]+VTC[i]+4*UTSTAR[i])
                                      + 2*(VAC[i]+UADUCT[i]+2*UASTAR[i])*CD[i]/CLmax[i])
                else:
                    JNS[i, i+Mp]   =  3*(VAC[i]+UADUCT[i]) + 4*UASTAR[i]
                    JNS[i, i+2*Mp] = -(L*RC[i]+VTC[i]+4*UTSTAR[i])

                JNS[i+Mp,  :Mp]        = -UAHIF[i, :Mp]
                JNS[i+Mp,  i+Mp]       = 1.0
                JNS[i+2*Mp, :Mp]       = -UTHIF[i, :Mp]
                JNS[i+2*Mp, i+2*Mp]    = 1.0

                denom = L*RC[i] + VTC[i] + UTSTAR[i]
                if abs(denom) > 1e-10:
                    JNS[i+3*Mp, i+Mp]      = -1.0 / denom
                    JNS[i+3*Mp, i+2*Mp]    = TANBIC[i] / denom
                JNS[i+3*Mp, i+3*Mp]    = 1.0

            try:
                DX = linsolve(JNS, -RNS)
            except Exception:
                DX = np.full(4*Mp, np.nan)

            G      = G      + relax * DX[:Mp]
            UASTAR = UASTAR + relax * DX[Mp:2*Mp]
            UTSTAR = UTSTAR + relax * DX[2*Mp:3*Mp]
            TANBIC = TANBIC + relax * DX[3*Mp:4*Mp]

            if np.any(np.isnan(DX)) or not np.all(np.isreal(DX)):
                G      = np.zeros(Mp)
                UASTAR = np.zeros(Mp)
                UTSTAR = np.zeros(Mp)
                TANBIC = TANBC.copy()
                print(" ")
                print("<WARNING> DX == NaN or imaginary... crash avoided...")
                print(" ")
                G_iter = 999

            TANBICsmooth = TANBIC @ Bsmooth

            if Duct_flag == 1:
                for m in range(Mp):
                    if abs(TANBICsmooth[m]) > 1e-10:
                        DAHIF[:, m] = DAHIF_times_TANBIC[:, m] / TANBICsmooth[m]
                        DRHIF[:, m] = DRHIF_times_TANBIC[:, m] / TANBICsmooth[m]
                UARING = DAHIF @ G
                URRING = DRHIF @ G
                _, GdNEW = Duct_Thrust(XdRING, Rduct_oR, VARING,
                                       UARING, URRING, GdRING, Gd, CDd, CTDdes)
                Gd = 0.5 * GdNEW + 0.5 * Gd
                UADUCT = UADIF * Gd

        # ----------------------------------------------------------------
        # Update VSTAR
        # ----------------------------------------------------------------
        VSTAR = np.sqrt((VAC + UADUCT + UASTAR)**2 + (L*RC + VTC + UTSTAR)**2)

        # ----------------------------------------------------------------
        # Update Horseshoe Influence Functions
        # ----------------------------------------------------------------
        if Wake_flag == 0:
            UAHIF, UTHIF = Horseshoe110628(Mp, Z, TANBIC, RC, RV,
                                           Hub_flag, Rhub_oR,
                                           Duct_flag, Rduct_oR)

        # ----------------------------------------------------------------
        # Update chord distribution
        # ----------------------------------------------------------------
        if Chord_flag == 1 and G_iter <= ITER:
            if ChordMethod == "CLmax":
                with np.errstate(divide='ignore', invalid='ignore'):
                    CoD = np.where(VSTAR * CLmax != 0, 2.0 * np.pi * G / (VSTAR * CLmax), 0.0)
            elif ChordMethod == "ConeyPLL":
                SIGMA = SIGMAs / VSTAR**2
                f0oD  = (2.0*np.pi*G / VSTAR) * f0octilde / CLItilde
                disc  = (8.09*f0oD + 3.033*t0oD)**2 + 4*SIGMA*(26.67*f0oD**2 + 10*f0oD*t0oD)
                CoD   = ((8.09*f0oD + 3.033*t0oD) / (2*SIGMA)
                         + np.sqrt(np.maximum(disc, 0.0)) / (2*SIGMA))
            # (FAST2011 and Brizzolara methods require additional functions
            #  not ported here; fall through to CLmax if selected)

            # Scale to specified EAR
            if EARspec > 0:
                XXRear = np.linspace(Rhub_oR, 1.0, 100)
                try:
                    EAR = (2.0 * Z / np.pi) * np.trapezoid(
                        pchip_interpolate(RC, CoD, XXRear), XXRear)
                    if EAR > 0:
                        CoD = (EARspec / EAR) * CoD
                except Exception:
                    pass

            if np.all(CoD == 0) or np.any(np.isnan(CoD)):
                G      = np.zeros(Mp)
                UASTAR = np.zeros(Mp)
                UTSTAR = np.zeros(Mp)
                TANBIC = TANBC.copy()
                CoD    = 0.1 * np.ones(Mp)
                print(" ")
                print("<WARNING> CoD == NaN or zero... crash avoided...")
                print(" ")
                G_iter = 999

        # ----------------------------------------------------------------
        # Convergence check
        # ----------------------------------------------------------------
        with np.errstate(invalid="ignore", divide="ignore"):
            G_res = np.where(np.abs(G) > 1e-15,
                             np.abs((G - G_last) / G),
                             0.0)
        G_last  = G.copy()

        if Gd != 0:
            Gd_res = abs((Gd - Gd_last) / Gd)
        else:
            Gd_res = 0.0
        Gd_last = Gd
        LM_last = LM

        if G_iter < 10:
            print(f"The max  G_res for iteration  {G_iter} is: {np.max(G_res):.6f}")
        else:
            print(f"The max  G_res for iteration {G_iter} is: {np.max(G_res):.6f}")

        if (Chord_flag == 1
                and ChordMethod in ("FAST2011dCTP", "FAST2011dVAC", "Brizzolara2007")):
            if G_iter % 3 != 0:
                G_res = np.ones(Mp)
            else:
                G_res = np.maximum(G_res, C_res / 10.0)

        G_iter += 1

    # =========================================================================
    # End of optimisation loop
    # =========================================================================
    if G_iter > ITER:
        print(" ")
        print("<WARNING> While loop G1 did NOT converge.")
        Converge_flag = 0
    else:
        print(" ")
        print("Design optimisation complete")
        Converge_flag = 1

    # =========================================================================
    # Compute actual duct thrust with final Gd
    # =========================================================================
    if Duct_flag == 1:
        CTD, _ = Duct_Thrust(XdRING, Rduct_oR, VARING,
                              UARING, URRING, GdRING, Gd, CDd, CTDdes)
    else:
        CTD = 0.0

    # =========================================================================
    # Compute performance
    # =========================================================================
    (CT, CQ, CP, KT, KQ,
     CTH, TAU_out,
     Ja, Jw, VMWV,
     EFFYo, EFFY, ADEFFY, QF, QFo, QFw) = Forces(
        RC, DR, VAC, VTC, UASTAR, UTSTAR, UADUCT,
        CD, CoD, G, Z, Js, VMIV, Hub_flag, Rhub_oR, Rhv, CTD
    )

    CL = np.where(VSTAR * CoD != 0.0, 2.0 * np.pi * G / (VSTAR * CoD), 0.0)

    XRear  = np.linspace(Rhub_oR, 1.0, 100)
    try:
        EAR = (2.0 * Z / np.pi) * np.trapezoid(
            pchip_interpolate(RC, CoD, XRear), XRear)
    except Exception:
        EAR = np.nan

    if Chord_flag == 1 and ChordMethod in ("FAST2011dCTP", "FAST2011dVAC", "Brizzolara2007"):
        t0oD = t0oc * CoD
    else:
        t0oc = np.where(CoD != 0.0, t0oD / CoD, 0.0)

    # =========================================================================
    # Print summary
    # =========================================================================
    print(" ")
    print("Forces after circulation optimisation:")
    if Propeller_flag == 1:
        print(f"    Js = {Js}")
        print(f"    KT = {KT}")
        print(f"    KQ = {KQ}")
        print(f"    CT = {CT}")
        if abs(VMIV - 1.0) > 1e-8:
            print(f"    Ja = {Ja}")
        print(f"  EFFY = {EFFY}")
        print(f"ADEFFY = {ADEFFY}")
        print(f"    QF = {QF}")
    else:
        print(f"L      =  {L}")
        print(f"CP     =  {CP}")
        print(f"CPBetz =  {CPBetz}")
        print(f"QF     =  {CP/CPBetz if CPBetz != 0 else 'N/A'}")
    print(" ")

    # =========================================================================
    # Package results
    # =========================================================================
    design = {}
    design["part1"]   = "------ Section properties, size (1,Mp) ------"
    design["RC"]      = RC
    design["DR"]      = DR
    design["G"]       = G
    design["VAC"]     = VAC
    design["VTC"]     = VTC
    design["UASTAR"]  = UASTAR
    design["UTSTAR"]  = UTSTAR
    design["VSTAR"]   = VSTAR
    design["TANBC"]   = TANBC
    design["TANBIC"]  = TANBIC
    design["CL"]      = CL
    design["CD"]      = CD
    design["CoD"]     = CoD
    design["t0oc"]    = t0oc
    design["t0oD"]    = t0oD

    design["part2"]     = "------ Other properties  ------"
    design["converged"] = Converge_flag
    design["iteration"] = G_iter
    design["RV"]        = RV
    design["Rhub_oR"]   = Rhub_oR
    if Rroot_oR > Rhub_oR:
        design["Rroot_oR"] = Rroot_oR
    if Rcirc_oR > Rhub_oR:
        design["Rcirc_oR"] = Rcirc_oR
    design["EAR"]   = EAR
    design["LM"]    = LM
    design["VMIV"]  = VMIV
    design["VMWV"]  = VMWV
    design["SIGMAs"] = SIGMAs

    if Duct_flag == 1:
        design["part3"]    = "------ Duct parameters ------"
        design["Rduct_oR"] = Rduct_oR
        design["Cduct_oR"] = Cduct_oR
        design["Xduct_oR"] = Xduct_oR
        design["Gd"]       = Gd
        design["VARING"]   = VARING
        design["XdRING"]   = XdRING
        design["UARING"]   = UARING
        design["URRING"]   = URRING
        design["GdRING"]   = GdRING
        design["DAHIFtT"]  = DAHIF_times_TANBIC
        design["DRHIFtT"]  = DRHIF_times_TANBIC
        design["UADIF"]    = UADIF
        design["UADUCT"]   = UADUCT
        design["CTPdes"]   = CTPdes
        design["CTDdes"]   = CTDdes
        design["TAU"]      = TAU_out
        design["CTD"]      = CTD
        design["part4"]    = "------ Performance metrics ------"
    else:
        design["part3"] = "------ Performance metrics ------"

    if Propeller_flag == 1:
        design["L"]     = L
        design["Js"]    = Js
        design["KT"]    = KT
        design["KQ"]    = KQ
        design["CT"]    = CT
        design["CQ"]    = CQ
        design["CP"]    = CP
        design["CTH"]   = CTH
        if abs(VMIV - 1.0) > 1e-8:
            design["EFFYo"] = EFFYo
            design["Ja"]    = Ja
        design["EFFY"]   = EFFY
        design["ADEFFY"] = ADEFFY
        design["QF"]     = QF
        if VMIV < 0.05:
            design["QFo"] = QFo
            design["QFw"] = QFw
    else:
        design["L"]     = L
        design["Js"]    = Js
        design["CT"]    = CT
        design["CQ"]    = CQ
        design["CP"]    = CP
        design["CPBetz"] = CPBetz
        design["QF"]    = CP / CPBetz if CPBetz != 0 else np.nan

    return design
