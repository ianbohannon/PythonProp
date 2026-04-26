# Port target: SourceCode/Find_dCLCDdALPHA.m
"""Find d(CL)/d(alpha) and d(CD)/d(alpha) for a given 2-D section."""

import numpy as np
from .CLCD_vs_ALPHA import CLCD_vs_ALPHA


def Find_dCLCDdALPHA(ALPHA, ALPHAstall, CL0, CD0, dCLdALPHA, Propeller_flag):
    """Return lift and drag curve slopes for a 2-D section using numerical differentiation.

    This function computes the derivatives dCL/dALPHA and dCD/dALPHA numerically
    using the central divided difference formula with step size dALPHA = 1e-3 rad.

    Parameters
    ----------
    ALPHA : float
        Net angle of attack [radians] (current angle minus reference angle).
    ALPHAstall : float
        Net angle of attack at stall [radians].
    CL0 : float
        Lift coefficient at reference angle of attack.
    CD0 : float
        Drag coefficient at reference angle of attack.
    dCLdALPHA : float
        Lift curve slope [1/rad] (used in CLCD_vs_ALPHA model).
    Propeller_flag : int
        Mode selector: 1 for propeller (constant drag), 0 for turbine (variable drag).

    Returns
    -------
    dCLda : float
        Derivative of lift coefficient with respect to angle of attack [1/rad].
    dCDda : float
        Derivative of drag coefficient with respect to angle of attack [1/rad].

    Notes
    -----
    This is a direct port of Find_dCLCDdALPHA.m from OpenProp v3.3.4 by Brenden Epps.
    The derivatives are computed using central divided difference:
        dCL/dALPHA = (CL(ALPHA + h) - CL(ALPHA - h)) / (2*h)
        dCD/dALPHA = (CD(ALPHA + h) - CD(ALPHA - h)) / (2*h)
    where h = 1e-3 rad.
    """
    # Step size for numerical differentiation
    dALPHA = 1e-3
    
    # Evaluate CL and CD at ALPHA + dALPHA
    CLp, CDp = CLCD_vs_ALPHA(ALPHA + dALPHA, ALPHAstall, CL0, CD0, dCLdALPHA, Propeller_flag)
    
    # Evaluate CL and CD at ALPHA - dALPHA
    CLm, CDm = CLCD_vs_ALPHA(ALPHA - dALPHA, ALPHAstall, CL0, CD0, dCLdALPHA, Propeller_flag)
    
    # Compute derivatives using central divided difference
    dCLda = (CLp - CLm) / (2.0 * dALPHA)
    dCDda = (CDp - CDm) / (2.0 * dALPHA)
    
    return dCLda, dCDda
