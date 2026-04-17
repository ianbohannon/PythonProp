# Port target: SourceCode/Horseshoe_intr_110830.m
"""Horseshoe vortex influence coefficients with intrinsic wake (version 110830)."""

import numpy as np


def Horseshoe_intr_110830(Mp, Z, RC, RV, L, Rhub_oR, Hub_flag, Duct_flag, Rduct_oR):
    """Compute intrinsic-wake horseshoe vortex influence coefficient matrices.

    Parameters
    ----------
    Mp : int
        Number of blade panels.
    Z : int
        Number of blades.
    RC : array_like, shape (Mp,)
        Control-point radii.
    RV : array_like, shape (Mp+1,)
        Vortex-point radii.
    L : float
        Tip-speed ratio.
    Rhub_oR : float
        Hub radius / propeller radius.
    Hub_flag : int
        1 to include hub image vortices, 0 otherwise.
    Duct_flag : int
        1 to include duct, 0 otherwise.
    Rduct_oR : float
        Duct radius / propeller radius.

    Returns
    -------
    UASTAR : ndarray, shape (Mp, Mp)
        Axial induced velocity coefficients.
    UTSTAR : ndarray, shape (Mp, Mp)
        Tangential induced velocity coefficients.
    """
    UASTAR = np.zeros((Mp, Mp))
    UTSTAR = np.zeros((Mp, Mp))
    return UASTAR, UTSTAR
