# Port target: Examples/Edited_Ducted_Propeller/Ducted_Prop_input.m
"""Build and return the input dictionary for the ducted-propeller example.

Ported from: Edited_Ducted_Propeller/Ducted_Prop_input.m
"""

import numpy as np


def build_input():
    """Construct the ``input`` dict for the ducted-propeller design case.

    Returns
    -------
    inp : dict
        Flat input dictionary suitable for passing to :func:`EppsOptimizer`.
    pt : dict
        Propeller/turbine data structure with keys
        ``filename``, ``notes``, ``input``, ``design``, ``geometry``, ``states``.
    """
    filename = "OpenProp"
    notes    = "Ducted propeller from Stubblefield (2008) M.S. thesis"

    # ------------------------------------------------------- Design parameters
    Z      = 4          # number of blades
    N      = 9000       # propeller speed [RPM]
    D      = 0.100      # propeller diameter [m]
        
    THRUST = 900        # required thrust [N]
    Vs     = 4.5        # ship velocity [m/s]
    Dhub   = 0.015      # hub diameter [m]

    Mp     = 20         # number of vortex panels over the radius
    Np     = 20         # number of points along the chord

    rho    = 1025       # sea water density [kg/m^3]

    # --------------------------------------------------------- Duct parameters
    TAU    = 0.9                # thrust ratio == prop thrust / total thrust
    Rduct  = D / 2 + 0.002     # duct radius [m]
    Cduct  = D                   # duct chord length [m]
    CDd    = 0.008              # duct viscous drag coefficient

    # --------------------------------------------- Blade 2-D section properties
    Meanline  = "NACA a=0.8"   # meanline type
    Thickness = 2               # thickness form (2 == elliptical)

    XR    = np.array([0.15,    0.3,    0.4,    0.5,    0.6,    0.7,    0.8,    0.9,    0.95,  1.0])
    XCoD  = np.array([0.1600, 0.1818, 0.2024, 0.2196, 0.2305, 0.2311, 0.2173, 0.1806, 0.1387, 0.0010])
    XCD   = np.array([0.0080, 0.0080, 0.0080, 0.0080, 0.0080, 0.0080, 0.0080, 0.0080, 0.0080, 0.0080])
    XVA   = np.ones(10)
    XVT   = np.zeros(10)
    t0oc0 = np.array([0.2056, 0.1551, 0.1181, 0.0902, 0.0694, 0.0541, 0.0419, 0.0332, 0.0324, 0.0000])
    skew0 = np.zeros(10)
    rake0 = np.zeros(10)

    # ------------------------------------------------------------------- Flags
    Propeller_flag = 1  # 0 == turbine, 1 == propeller
    Viscous_flag   = 1  # 0 == viscous forces off (CD = 0), 1 == viscous forces on
    Hub_flag       = 1  # 0 == no hub, 1 == hub
    Duct_flag      = 1  # 0 == no duct, 1 == duct
    Plot_flag      = 1  # 0 == do not display plots, 1 == display plots
    Chord_flag     = 1  # 0 == do not optimize chord lengths, 1 == optimize chord lengths

    # ---------------------------------------------- Compute derived quantities
    n        = N / 60                              # revolutions per second [rps]
    R        = D / 2                               # propeller radius [m]
    Rhub     = Dhub / 2                            # hub radius [m]
    Rhub_oR  = Rhub / R
    Js       = Vs / (n * D)                        # advance coefficient
    L        = np.pi / Js                          # tip-speed ratio
    CTDES    = THRUST / (0.5 * rho * Vs**2 * np.pi * R**2)

    dCLdALPHA = 2 * np.pi                          # d(CL)/d(alpha)

    # =========================================================================
    # Pack up input dictionary
    inp = {
        # Performance inputs
        "Z":        Z,
        "N":        N,
        "D":        D,
        "Vs":       Vs,
        "Js":       Js,
        "L":        L,
        "CTDES":    CTDES,
        # Geometry inputs
        "Mp":       Mp,
        "Np":       Np,
        "R":        R,
        "Rhub":     Rhub,
        "Rhub_oR":  Rhub_oR,
        "XR":       XR,
        "XVA":      XVA,
        "XVT":      XVT,
        "XCD":      XCD,
        "XCoD":     XCoD,
        "t0oc":     t0oc0,
        "skew0":    skew0,
        "rake0":    rake0,
        "Meanline":  Meanline,
        "Thickness": Thickness,
        "dCLdALPHA": dCLdALPHA,
        # Computational flags
        "Propeller_flag": Propeller_flag,
        "Viscous_flag":   Viscous_flag,
        "Hub_flag":       Hub_flag,
        "Duct_flag":      Duct_flag,
        "Plot_flag":      Plot_flag,
        "Chord_flag":     Chord_flag,
        # Duct inputs
        "TAU":    TAU,
        "Rduct":  Rduct,
        "Cduct":  Cduct,
        "CDd":    CDd,
        # Fluid properties
        "rho":    rho,
    }

    # Pack into propeller/turbine data structure
    pt = {
        "filename": filename,
        "notes":    notes,
        "input":    inp,
        "design":   None,
        "geometry": None,
        "states":   None,
    }

    return inp, pt


if __name__ == "__main__":
    inp, pt = build_input()
    print("Input dict assembled successfully.")
    print(f"  Js     = {inp['Js']:.4f}")
    print(f"  L      = {inp['L']:.4f}")
    print(f"  CTDES  = {inp['CTDES']:.4f}")
    print(f"  Rduct  = {inp['Rduct']:.4f} m")
