# Port target: SourceCode/Duct_Thrust.m
"""Compute duct thrust and update duct circulation to meet a thrust target."""

import numpy as np


def Duct_Thrust(XdRING, Rduct_oR, VARING, UARING, URRING,
                GdRING, Gd, CDd, CTDdes):
    """Compute duct thrust coefficient and desired duct circulation.

    Ported from ``SourceCode/Duct_Thrust.m``.

    Parameters
    ----------
    XdRING : array_like, shape (Nd,)
        Axial positions of duct vortex rings (x/R).
    Rduct_oR : float
        Duct radius / propeller radius.
    VARING : float
        Axial free-stream velocity at duct / Vs.
    UARING : array_like, shape (Nd,)
        Axial velocity induced at duct rings by propeller / Vs.
    URRING : array_like, shape (Nd,)
        Radial velocity induced at duct rings by propeller / Vs.
    GdRING : array_like, shape (Nd,)
        Relative circulation of each duct ring (sums to 1).
    Gd : float
        Current total non-dimensional duct circulation.
    CDd : float
        Duct viscous drag coefficient.
    CTDdes : float
        Desired duct thrust coefficient.

    Returns
    -------
    CTD : float
        Current duct thrust coefficient (with current *Gd*).
    GdDES : float
        Required duct circulation to achieve *CTDdes*.
    """
    XdRING = np.asarray(XdRING, dtype=float)
    UARING = np.asarray(UARING, dtype=float)
    URRING = np.asarray(URRING, dtype=float)
    GdRING = np.asarray(GdRING, dtype=float)

    # Assume uniform spacing
    if len(XdRING) > 1:
        delS = abs(XdRING[1] - XdRING[0])
    else:
        delS = 1.0

    # Inviscid Kutta-Joukowski thrust per unit Gd
    CTD_inviscid_oGd = np.sum(4.0 * (-URRING) * GdRING * (2.0 * np.pi * Rduct_oR))
    CTD_inviscid     = CTD_inviscid_oGd * Gd

    # Viscous drag on duct (negative thrust)
    CTD_viscous = np.sum(-(VARING + UARING) ** 2 * CDd * delS * (2.0 * Rduct_oR))

    CTD = CTD_inviscid + CTD_viscous

    # Scale duct circulation to meet desired thrust
    if CTD_inviscid_oGd != 0.0:
        GdDES = (CTDdes - CTD_viscous) / CTD_inviscid_oGd
    else:
        GdDES = Gd

    return CTD, GdDES
