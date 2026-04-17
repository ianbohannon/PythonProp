# Port target: SourceCode/Forces.m
"""Compute propeller blade forces (thrust and torque)."""

import numpy as np


def Forces(G, RC, L, Z, VAC, VTC, UA, UT, CD, CoD):
    """Compute thrust and torque coefficients from blade circulation.

    Parameters
    ----------
    G : array_like, shape (Mp,)
        Non-dimensional circulation at control points.
    RC : array_like, shape (Mp,)
        Control-point radii (r/R).
    L : float
        Tip-speed ratio.
    Z : int
        Number of blades.
    VAC, VTC : array_like, shape (Mp,)
        Axial and tangential inflow velocity fractions.
    UA, UT : array_like, shape (Mp,)
        Axial and tangential induced velocities.
    CD : array_like, shape (Mp,)
        Section drag coefficients.
    CoD : array_like, shape (Mp,)
        Chord / diameter at each panel.

    Returns
    -------
    KT : float
        Thrust coefficient (stub — returns NaN).
    KQ : float
        Torque coefficient (stub — returns NaN).
    """
    return np.nan, np.nan
