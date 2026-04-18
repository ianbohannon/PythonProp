# Port target: SourceCode/Horseshoe_intr_110830.m
"""Horseshoe vortex influence coefficients: propeller on duct (version 110830)."""

import numpy as np


def Horseshoe_intr_110830(XC2, RC2, RC1, TANBIC1, RV1, Z1,
                          Hub_flag, Rhub_oR1, Duct_flag, Rduct_oR1):
    """Compute influence of propeller horseshoe vortices on duct control points.

    Ported from ``SourceCode/Horseshoe_intr_110830.m``.

    Called in EppsOptimizer with ``TANBIC1 == ones(size(TANBIC))`` so that
    the result can be divided by the actual ``TANBIC`` afterwards::

        DAHIF(:,m) = DAHIF_times_TANBIC(:,m) / TANBIC(m)

    Parameters
    ----------
    XC2 : array_like, shape (Nd,)
        Axial positions of duct control points (x/R).
    RC2 : float
        Radial position of duct (= Rduct_oR).
    RC1 : array_like, shape (Mp,)
        Propeller control-point radii (r/R).
    TANBIC1 : array_like, shape (Mp,)
        tan(beta_i) at propeller control points (pass ones for proportional
        form).
    RV1 : array_like, shape (Mp+1,)
        Propeller vortex-point radii (r/R).
    Z1 : int
        Number of propeller blades.
    Hub_flag : int
        1 to include hub image vortices, 0 otherwise.
    Rhub_oR1 : float
        Hub radius / propeller radius.
    Duct_flag : int
        1 to include duct image vortices, 0 otherwise.
    Rduct_oR1 : float
        Duct radius / propeller radius.

    Returns
    -------
    UAHIF21 : ndarray, shape (Nd, Mp)
        Axial influence of propeller on duct (times TANBIC).
    UTHIF21 : ndarray, shape (Nd, Mp)
        Tangential influence of propeller on duct.
    URHIF21 : ndarray, shape (Nd, Mp)
        Radial influence of propeller on duct (times TANBIC).
    """
    XC2    = np.asarray(XC2,    dtype=float)
    RC1    = np.asarray(RC1,    dtype=float)
    RV1    = np.asarray(RV1,    dtype=float)

    Nd = len(XC2)
    Mp = len(RC1)

    UAHIF21 = np.zeros((Nd, Mp))
    UTHIF21 = np.zeros((Nd, Mp))
    URHIF21 = np.zeros((Nd, Mp))

    return UAHIF21, UTHIF21, URHIF21
