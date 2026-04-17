# Port target: SourceCode/GeometryFoil2D.m
"""Generate 2-D foil section geometry (camber line and thickness distribution)."""

import numpy as np


def GeometryFoil2D(Np, Meanline, Thickness, t0oc, f0oc=0.0):
    """Return x/c, camber-line y/c, and half-thickness y/c arrays for a 2-D section.

    Parameters
    ----------
    Np : int
        Number of points along the chord.
    Meanline : str or int
        Meanline type (e.g. ``'NACA a=0.8'`` or ``1``).
    Thickness : int
        Thickness form (1 = NACA 65A010, 2 = elliptical, 3 = parabolic).
    t0oc : float
        Maximum thickness / chord.
    f0oc : float, optional
        Maximum camber / chord. Default 0.

    Returns
    -------
    xoc : ndarray, shape (Np,)
        Chord-wise positions x/c in [0, 1].
    yc : ndarray, shape (Np,)
        Camber-line y/c (stub — returns zeros).
    yt : ndarray, shape (Np,)
        Half-thickness y/c (stub — returns zeros).
    """
    xoc = np.linspace(0.0, 1.0, Np)
    yc = np.zeros(Np)
    yt = np.zeros(Np)
    return xoc, yc, yt
