# Port target: SourceCode/GeometryFoil2D.m
"""Return foil section geometry parameters for chord optimisation."""

import numpy as np


# Default values for common profiles (from OpenProp source code)
_DEFAULTS = {
    # (Meanline, Thickness): (f0octilde, CLItilde, alphaItilde)
    ("NACA a=0.8 (modified)", "NACA 65A010"):     (0.0611, 0.7, 1.540),
    ("NACA a=0.8",            "NACA 65A010"):     (0.0679, 0.7, 1.540),
    ("parabolic",             "NACA 65A010"):     (0.0500, 0.7, 1.540),
}
_DEFAULT_F0OCTILDE  = 0.0611
_DEFAULT_CLITILDE   = 0.7
_DEFAULT_ALPHAITILDE = 1.540


def GeometryFoil2D(Meanline="NACA a=0.8 (modified)",
                   Thickness="NACA 65A010",
                   x0=None):
    """Return foil section geometry parameters.

    Ported from ``SourceCode/GeometryFoil2D.m``.

    In EppsOptimizer the function is called as::

        [f0octilde, CLItilde, ...] = GeometryFoil2D(Meanline, Thickness)

    returning at least seven outputs.

    Parameters
    ----------
    Meanline : str or int
        Meanline type (e.g. ``'NACA a=0.8 (modified)'`` or ``0``).
    Thickness : str or int
        Thickness form (e.g. ``'NACA 65A010'`` or ``1``).
    x0 : array_like, optional
        Chord-wise positions x/c (ignored in this stub).

    Returns
    -------
    f0octilde : float
        Non-dimensional camber parameter used in chord optimisation.
    CLItilde : float
        Ideal lift coefficient.
    alphaItilde : float
        Ideal angle of attack [deg].
    fof0 : ndarray
        Camber-line ordinate / f0 (stub — returns zeros).
    dfof0dxoc : ndarray
        Camber-line slope / f0 (stub — returns zeros).
    tot0 : ndarray
        Thickness / t0 (stub — returns zeros).
    As0 : float
        Leading-edge sharpness parameter (stub — 0).
    """
    # Normalise integer codes used in MATLAB
    _meanline_map = {
        0: "NACA a=0.8 (modified)",
        1: "NACA a=0.8",
        2: "parabolic",
    }
    _thickness_map = {
        1: "NACA 65A010",
        2: "elliptic",
        3: "parabolic",
        4: "NACA 65A010 (Epps modified)",
        5: "NACA 66 (DTRC modified)",
        6: "NACA 00xx",
    }
    if isinstance(Meanline,  int): Meanline  = _meanline_map.get(Meanline,  "NACA a=0.8 (modified)")
    if isinstance(Thickness, int): Thickness = _thickness_map.get(Thickness, "NACA 65A010")

    key = (Meanline, Thickness)
    f0octilde, CLItilde, alphaItilde = _DEFAULTS.get(
        key, (_DEFAULT_F0OCTILDE, _DEFAULT_CLITILDE, _DEFAULT_ALPHAITILDE)
    )

    if x0 is None:
        x0 = np.arange(0, 1.1, 0.1)
    x0 = np.asarray(x0, dtype=float)
    n  = len(x0)

    fof0      = np.zeros(n)
    dfof0dxoc = np.zeros(n)
    tot0      = np.zeros(n)
    As0       = 0.0

    return f0octilde, CLItilde, alphaItilde, fof0, dfof0dxoc, tot0, As0
