# Port target: SourceCode/elliptic12.m
"""Incomplete elliptic integrals of the first and second kind."""

import numpy as np
from scipy.special import ellipk, ellipe


def elliptic12(m):
    """Return (K, E) — complete elliptic integrals of the first and second kind.

    Parameters
    ----------
    m : float or array_like
        Parameter (0 <= m < 1).

    Returns
    -------
    K : ndarray
        Complete elliptic integral of the first kind.
    E : ndarray
        Complete elliptic integral of the second kind.
    """
    m = np.asarray(m, dtype=float)
    K = ellipk(m)
    E = ellipe(m)
    return K, E
