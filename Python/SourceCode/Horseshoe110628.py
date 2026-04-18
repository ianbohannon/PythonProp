# Port target: SourceCode/Horseshoe110628.m
"""Horseshoe vortex influence coefficient matrices (version 110628)."""

import numpy as np
from Wrench import Wrench


def Horseshoe110628(Mp, Z, TANBIC, RC, RV, Hub_flag, Rhub_oR, Duct_flag, Rduct_oR):
    """Compute horseshoe vortex influence coefficient matrices.

    Ported from ``SourceCode/Horseshoe110628.m``.

    ``UAHIF(n, m)`` is the axial velocity induced at control point *n* by
    a unit horseshoe vortex shed from panel *m* (scaled by ``2*pi*R``).

    Parameters
    ----------
    Mp : int
        Number of blade panels.
    Z : int
        Number of blades.
    TANBIC : array_like, shape (Mp,)
        tan(beta_i) at each control point.
    RC : array_like, shape (Mp,)
        Control-point radii (r/R).
    RV : array_like, shape (Mp+1,)
        Vortex-point radii (r/R).
    Hub_flag : int
        1 to include hub image vortices, 0 otherwise.
    Rhub_oR : float
        Hub radius / propeller radius.
    Duct_flag : int
        1 to include duct image vortices, 0 otherwise.
    Rduct_oR : float
        Duct radius / propeller radius.

    Returns
    -------
    UAHIF : ndarray, shape (Mp, Mp)
        Axial horseshoe influence functions  (``2*pi*R * HIF``).
    UTHIF : ndarray, shape (Mp, Mp)
        Tangential horseshoe influence functions (``2*pi*R * HIF``).
    """
    TANBIC = np.asarray(TANBIC, dtype=float)
    RC     = np.asarray(RC,     dtype=float)
    RV     = np.asarray(RV,     dtype=float)

    UAHIF = np.zeros((Mp, Mp))
    UTHIF = np.zeros((Mp, Mp))

    for n in range(Mp):          # control point index
        for m in range(Mp):      # vortex panel index
            # r1 = RV[m+1],  r2 = RV[m]
            tanbiv1 = TANBIC[m] * RC[m] / RV[m + 1]
            tanbiv2 = TANBIC[m] * RC[m] / RV[m]

            UAW1, UTW1 = Wrench(Z, tanbiv1, RC[n], RV[m + 1])
            UAW2, UTW2 = Wrench(Z, tanbiv2, RC[n], RV[m])

            # Hub-image vortices (Kerwin p.181)
            if Hub_flag == 1:
                rh1 = Rhub_oR ** 2 / RV[m + 1]
                rh2 = Rhub_oR ** 2 / RV[m]
                UAWh1, UTWh1 = Wrench(Z, TANBIC[m] * RC[m] / rh1, RC[n], rh1)
                UAWh2, UTWh2 = Wrench(Z, TANBIC[m] * RC[m] / rh2, RC[n], rh2)
                UAW1 -= UAWh1
                UAW2 -= UAWh2
                UTW1 -= UTWh1
                UTW2 -= UTWh2

            # Duct-image vortices
            if Duct_flag == 1:
                rd1 = Rduct_oR ** 2 / RV[m + 1]
                rd2 = Rduct_oR ** 2 / RV[m]
                UAWd1, UTWd1 = Wrench(Z, TANBIC[m] * RC[m] / rd1, RC[n], rd1)
                UAWd2, UTWd2 = Wrench(Z, TANBIC[m] * RC[m] / rd2, RC[n], rd2)
                UAW1 -= UAWd1
                UAW2 -= UAWd2
                UTW1 -= UTWd1
                UTW2 -= UTWd2

            UAHIF[n, m] = UAW1 - UAW2
            UTHIF[n, m] = UTW1 - UTW2

    return UAHIF, UTHIF
