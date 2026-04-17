# Port target: SourceCode/EppsOptimizer.m
"""Epps lifting-line propeller design optimizer."""

import numpy as np


def EppsOptimizer(inp):
    """Run the Epps lifting-line design optimization.

    Parameters
    ----------
    inp : dict
        Input parameter dictionary as assembled by *Ducted_Prop_input.py*.
        Required keys include: ``Z``, ``N``, ``D``, ``Vs``, ``Js``, ``L``,
        ``CTDES``, ``Mp``, ``Np``, ``R``, ``Rhub``, ``XR``, ``XVA``,
        ``XVT``, ``XCD``, ``XCoD``, ``t0oc``, ``skew0``, ``rake0``,
        ``Meanline``, ``Thickness``, ``dCLdALPHA``, ``Propeller_flag``,
        ``Viscous_flag``, ``Hub_flag``, ``Duct_flag``, ``Plot_flag``,
        ``Chord_flag``, ``TAU``, ``Rduct``, ``Cduct``, ``CDd``.

    Returns
    -------
    design : dict
        Design output dictionary with stub keys ``RC``, ``G``, ``KT``,
        ``KQ``, ``EFFY`` (all NaN / empty arrays for this iteration).
    """
    Mp = int(inp.get("Mp", 20))
    design = {
        "RC": np.full(Mp, np.nan),
        "G": np.full(Mp, np.nan),
        "KT": np.nan,
        "KQ": np.nan,
        "EFFY": np.nan,
    }
    return design
