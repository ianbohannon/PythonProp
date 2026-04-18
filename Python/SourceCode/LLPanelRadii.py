# Port target: SourceCode/LLPanelRadii.m
"""Compute lifting-line panel radii (control points and vortex points)."""

import numpy as np


def LLPanelRadii(Mp, Rhub_oR=0.0, Hub_flag=0, Duct_flag=0):
    """Compute panel control-point and vortex-point radii.

    Ported from ``SourceCode/LLPanelRadii.m``.

    Parameters
    ----------
    Mp : int
        Number of vortex panels over the radius.
    Rhub_oR : float, optional
        Hub radius / propeller radius. Default 0.
    Hub_flag : int, optional
        1 if hub image vortices are used, 0 otherwise. Default 0.
    Duct_flag : int, optional
        1 if duct image vortices are used, 0 otherwise. Default 0.

    Returns
    -------
    RC : ndarray, shape (Mp,)
        Control-point radii (mid-panel), normalised by propeller radius.
    RV : ndarray, shape (Mp+1,)
        Vortex-point radii (panel edges), normalised by propeller radius.
    DR : ndarray, shape (Mp,)
        Panel widths (diff of RV).
    """
    mp_arr = np.arange(0, Mp + 1, dtype=float)  # 0 .. Mp
    rc_arr = np.arange(1, Mp + 1, dtype=float)  # 1 .. Mp

    if Duct_flag == 0 and Hub_flag == 0:
        # Constant spacing — 1/4 panel inset at hub and tip
        RV = Rhub_oR + (1 - Rhub_oR) * (mp_arr + 0.25) / (Mp + 0.50)
        RC = Rhub_oR + (1 - Rhub_oR) * (rc_arr - 0.25) / (Mp + 0.50)

    elif Duct_flag == 1 and Hub_flag == 0:
        # Constant spacing — 1/4 panel inset at hub only
        RV = Rhub_oR + (1 - Rhub_oR) * (mp_arr + 0.25) / (Mp + 0.25)
        RC = Rhub_oR + (1 - Rhub_oR) * (rc_arr - 0.25) / (Mp + 0.25)

    elif Duct_flag == 1 and Hub_flag == 1:
        # Constant spacing — no inset
        RV = Rhub_oR + (1 - Rhub_oR) * mp_arr / Mp
        RC = Rhub_oR + (1 - Rhub_oR) * (rc_arr - 0.50) / Mp

    else:  # Duct_flag == 0 and Hub_flag == 1
        # Constant spacing — 1/4 panel inset at tip only
        RV = Rhub_oR + (1 - Rhub_oR) * mp_arr / (Mp + 0.25)
        RC = Rhub_oR + (1 - Rhub_oR) * (rc_arr - 0.50) / (Mp + 0.25)

    DR = np.diff(RV)
    return RC, RV, DR
