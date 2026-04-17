# Port target: SourceCode/Find_dCLCDdALPHA.m
"""Find d(CL)/d(alpha) and d(CD)/d(alpha) for a given 2-D section."""

import numpy as np


def Find_dCLCDdALPHA(Meanline, Thickness, t0oc):
    """Return lift and drag curve slopes for a 2-D section.

    Parameters
    ----------
    Meanline : str or int
        Meanline type identifier.
    Thickness : int
        Thickness form identifier.
    t0oc : float
        Maximum thickness / chord ratio.

    Returns
    -------
    dCLdALPHA : float
        Lift curve slope [1/rad] (stub — returns 2*pi).
    dCDdALPHA : float
        Drag curve slope [1/rad] (stub — returns 0).
    """
    dCLdALPHA = 2.0 * np.pi
    dCDdALPHA = 0.0
    return dCLdALPHA, dCDdALPHA
