# Port target: SourceCode/Duct_Thrust.m
"""Compute duct thrust and drag contributions."""

import numpy as np


def Duct_Thrust(Gd, Rduct_oR, Cduct_oR, CDd, VAd, rho, Vs, R):
    """Compute thrust and torque contributed by the duct.

    Parameters
    ----------
    Gd : float
        Duct circulation (non-dimensional).
    Rduct_oR : float
        Duct radius / propeller radius.
    Cduct_oR : float
        Duct chord / propeller radius.
    CDd : float
        Duct viscous drag coefficient.
    VAd : float
        Axial inflow velocity at the duct.
    rho : float
        Fluid density [kg/m^3].
    Vs : float
        Ship velocity [m/s].
    R : float
        Propeller radius [m].

    Returns
    -------
    KTd : float
        Duct thrust coefficient (stub — returns NaN).
    """
    return np.nan
