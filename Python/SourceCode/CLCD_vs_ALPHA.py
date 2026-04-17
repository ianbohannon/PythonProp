# Port target: SourceCode/CLCD_vs_ALPHA.m
"""Return CL and CD as a function of angle of attack for a given section type."""

import numpy as np


def CLCD_vs_ALPHA(alpha, Meanline, Thickness, t0oc):
    """Compute section lift and drag coefficients at angle of attack *alpha*.

    Parameters
    ----------
    alpha : float or array_like
        Angle of attack [radians].
    Meanline : str or int
        Meanline type identifier (e.g. ``'NACA a=0.8'`` or ``1``).
    Thickness : int
        Thickness form identifier (1 = NACA 65A010, 2 = elliptical, 3 = parabolic).
    t0oc : float
        Maximum thickness / chord ratio.

    Returns
    -------
    CL : ndarray
        Lift coefficient (stub — returns zeros).
    CD : ndarray
        Drag coefficient (stub — returns zeros).
    """
    alpha = np.asarray(alpha, dtype=float)
    CL = np.zeros_like(alpha)
    CD = np.zeros_like(alpha)
    return CL, CD
