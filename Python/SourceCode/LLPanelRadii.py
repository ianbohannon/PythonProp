# Port target: SourceCode/LLPanelRadii.m
"""Compute lifting-line panel radii (control points and vortex points)."""

import numpy as np


def LLPanelRadii(Mp, Rhub_oR=0.0):
    """Compute panel control-point and vortex-point radii.

    Parameters
    ----------
    Mp : int
        Number of vortex panels over the radius.
    Rhub_oR : float, optional
        Hub radius / propeller radius. Default 0.

    Returns
    -------
    RC : ndarray, shape (Mp,)
        Control-point radii (mid-panel), normalised by propeller radius.
    RV : ndarray, shape (Mp+1,)
        Vortex-point radii (panel edges), normalised by propeller radius.
    """
    RV = np.linspace(Rhub_oR, 1.0, Mp + 1)
    RC = 0.5 * (RV[:-1] + RV[1:])
    return RC, RV
