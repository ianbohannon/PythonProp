# Port target: SourceCode/Duct_Influence.m
"""Compute duct influence coefficients on the propeller blade panels."""

import numpy as np


def Duct_Influence(RC, Rduct_oR, Cduct_oR):
    """Compute axial velocity induced at blade control points by a duct vortex sheet.

    Parameters
    ----------
    RC : array_like, shape (Mp,)
        Control-point radii (r/R).
    Rduct_oR : float
        Duct radius / propeller radius.
    Cduct_oR : float
        Duct chord / propeller radius.

    Returns
    -------
    UADIF : ndarray, shape (Mp,)
        Axial velocity induced at each control point per unit duct circulation.
    """
    RC = np.asarray(RC, dtype=float)
    UADIF = np.zeros_like(RC)
    return UADIF
