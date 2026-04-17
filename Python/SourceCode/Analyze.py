# Port target: SourceCode/Analyze.m
"""Analyze off-design operating states for a given propeller design."""

import numpy as np


def Analyze(pt, LAMBDAall):
    """Compute performance across a range of advance coefficients.

    Parameters
    ----------
    pt : dict
        Propeller/turbine data structure (must include ``pt['input']`` and
        ``pt['design']``).
    LAMBDAall : array_like
        Tip-speed ratios at which to evaluate performance.

    Returns
    -------
    states : dict
        Off-design states dictionary with stub keys ``Js``, ``KT``, ``KQ``,
        ``EFFY`` (all NaN arrays for this iteration).
    """
    LAMBDAall = np.asarray(LAMBDAall, dtype=float)
    n = len(LAMBDAall)
    states = {
        "Js": np.full(n, np.nan),
        "KT": np.full(n, np.nan),
        "KQ": np.full(n, np.nan),
        "EFFY": np.full(n, np.nan),
    }
    return states
