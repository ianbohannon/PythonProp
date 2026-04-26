"""Compute duct thrust and update duct circulation to meet a thrust target."""

import numpy as np


def Duct_Thrust(XdRING, Rduct_oR, VARING, UARING, URRING, GdRING, Gd, CDd, CTDDES):
    """Compute duct thrust coefficient and desired duct circulation.

    Ported from ``SourceCode/Duct_Thrust.m`` (OpenProp v3.3.4).

    This function computes:
        1. The duct thrust coefficient, CTD, given duct circulation, Gd, and
        2. The required circulation, GdDES, to provide the desired duct thrust
           coefficient, CTDDES.

    Model parameters:
        Rduct_oR      : duct radius / propeller radius
        Cduct_oR      : duct chord / propeller radius
        Xduct_oR      : location of duct mid-chord downstream of propeller

        XdRING        : x/R location of each vortex ring downstream of propeller
        VARING        : (axial free-stream velocity at duct) / Vs
        UARING        : (axial velocity induced at duct by prop) / Vs
        URRING        : (radial velocity induced at duct by prop) / Vs

        GdRING        : fraction of total non-dimensional duct circulation
                        (i.e. circulation per unit Gd), sum(GdRING) = 1
        Gd            : total non-dimensional circulation about the duct
                        Gd == Gamma_d / (2*pi*R*Vs)
        Gamma_d       : total dimensional circulation about the duct [m^2/s]

        CDd           : section drag coefficient for the duct
        CTDDES        : desired duct thrust coefficient
        CTD           : duct thrust coeff (viscous drag included) with 
                        total duct circulation of Gd

    Parameters
    ----------
    XdRING : array_like, shape (Nd,)
        Axial positions of duct vortex rings (x/R).
    Rduct_oR : float
        Duct radius / propeller radius.
    VARING : array_like, shape (Nd,)
        Axial free-stream velocity at duct / Vs.
    UARING : array_like, shape (Nd,)
        Axial velocity induced at duct rings by propeller / Vs.
    URRING : array_like, shape (Nd,)
        Radial velocity induced at duct rings by propeller / Vs.
    GdRING : array_like, shape (Nd,)
        Relative circulation of each duct ring (sums to 1).
        Non-dimensional circulation of ring n is Gd*GdRING[n].
    Gd : float
        Current total non-dimensional duct circulation.
    CDd : float
        Duct section drag coefficient.
    CTDDES : float
        Desired duct thrust coefficient.

    Returns
    -------
    CTD : float
        Current duct thrust coefficient (with current Gd).
        CTD = CTD_inviscid + CTD_viscous
    GdDES : float
        Required duct circulation to achieve CTDDES.

    Notes
    -----
    The duct thrust has two components:
        1. Inviscid Kutta-Joukowski thrust:
           CTD_inviscid = sum(4 * (-URRING) * (Gd*GdRING) * (2*pi*Rduct_oR))

        2. Viscous drag on duct (negative thrust):
           CTD_viscous = sum(-(VARING+UARING)^2 * CDd * delS * (2*Rduct_oR))

    The required circulation GdDES is computed by:
        CTD = CTD_inviscid + CTD_viscous
        CTDDES = CTD_inviscidDES + CTD_viscous
        GdDES = CTD_inviscidDES / (CTD_inviscid/Gd)
              = (CTDDES - CTD_viscous) / CTD_inviscid_oGd

    References
    ----------
    Stubblefield, J. M. (2008). Numerical Analysis of a Rim-Driven
    Thruster. MS Thesis, MIT.
    """
    XdRING = np.asarray(XdRING, dtype=float)
    VARING = np.asarray(VARING, dtype=float)
    UARING = np.asarray(UARING, dtype=float)
    URRING = np.asarray(URRING, dtype=float)
    GdRING = np.asarray(GdRING, dtype=float)

    # ---------------------------------------------------------- Compute forces
    # (vortex ring spacing) / R,   (linear spacing assumed)
    delS = abs(XdRING[1] - XdRING[0])

    # Inviscid Kutta-Joukowski thrust
    # CTD_inviscid = sum(4 * (-URRING) * (Gd*GdRING) * (2*pi*Rduct_oR))  # inviscid KJ thrust
    CTD_inviscid_oGd = np.sum(4.0 * (-URRING) * GdRING * (2.0 * np.pi * Rduct_oR))

    CTD_inviscid = CTD_inviscid_oGd * Gd

    # Viscous drag on duct (negative thrust)
    CTD_viscous = np.sum(-(VARING + UARING) ** 2 * CDd * delS * (2.0 * Rduct_oR))

    # Total duct thrust coefficient
    CTD = CTD_inviscid + CTD_viscous

    # ------------ Scale duct circulation so that duct provides required thrust
    # CTD    = CTD_inviscid    + CTD_viscous
    # CTDDES = CTD_inviscidDES + CTD_viscous
    # GdDES  = CTD_inviscidDES / (CTD_inviscid/Gd)
    GdDES = (CTDDES - CTD_viscous) / CTD_inviscid_oGd

    return CTD, GdDES


# ================================================= END Duct_Thrust Function
# =========================================================================
