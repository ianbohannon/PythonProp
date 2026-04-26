# Port target: SourceCode/CLCD_vs_ALPHA.m
"""Return CL and CD as a function of angle of attack for a given section type."""

import numpy as np


def CLCD_vs_ALPHA(ALPHA, ALPHAstall, CL0, CD0, dCLdALPHA, Propeller_flag):
    """Compute section lift and drag coefficients at angle of attack ALPHA.

    This function implements a smooth stall model using arctangent transitions
    with sharpness parameter B=20. The drag model differs for propellers vs turbines:
    - Propellers: CD ~= CD0 near ALPHA == 0 (constant drag treatment)
    - Turbines: CD ~= abs(CL0)*(CDoCL + dCLdALPHA*ALPHA) near ALPHA == 0

    Parameters
    ----------
    ALPHA : float or array_like
        Net angle of attack [radians] (current angle minus reference angle).
    ALPHAstall : float
        Net angle of attack at stall [radians].
    CL0 : float
        Lift coefficient at reference angle of attack.
    CD0 : float
        Drag coefficient at reference angle of attack.
    dCLdALPHA : float
        Lift curve slope [1/rad].
    Propeller_flag : int
        Mode selector: 1 for propeller (constant drag), 0 for turbine (variable drag).

    Returns
    -------
    CL : ndarray
        Lift coefficient at the given angle(s) of attack.
    CD : ndarray
        Drag coefficient at the given angle(s) of attack.

    Notes
    -----
    This is a direct port of CLCD_vs_ALPHA.m from OpenProp v3.3.4 by Brenden Epps.
    The stall model uses smooth arctangent transitions with B=20 sharpness parameter.
    """
    # Convert to numpy array
    ALPHA = np.asarray(ALPHA, dtype=float)
    
    # Compute drag/lift ratio
    if CL0 == 0:
        CDoCL = CD0 / (2.0 * np.pi * ALPHAstall)
    else:
        CDoCL = CD0 / abs(CL0)
    
    # If section is not a lifting surface
    if dCLdALPHA == 0:
        CL = np.full_like(ALPHA, CL0)
        CD = np.full_like(ALPHA, CD0)
        return CL, CD
    
    # Stall sharpness parameter
    B = 20.0
    
    # Compute lift coefficient with smooth stall transitions
    CL = (CL0
          + dCLdALPHA * ALPHA
          - dCLdALPHA * (ALPHA - ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (ALPHA - ALPHAstall)) + 0.5)
          + dCLdALPHA * (-ALPHA - ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHA - ALPHAstall)) + 0.5))
    
    # Compute drag coefficient based on mode
    if Propeller_flag == 1:
        # Propeller: constant drag treatment (CD ~= CD0 near ALPHA == 0)
        A = (2.0 - CD0) / (np.pi / 2.0 - ALPHAstall)  # post-stall slope
        
        CD = (CD0
              + A * (ALPHA - ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (ALPHA - ALPHAstall)) + 0.5)
              - A * (-ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHAstall)) + 0.5)
              + A * (-ALPHA - ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHA - ALPHAstall)) + 0.5)
              - A * (-ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHAstall)) + 0.5))
    else:
        # Turbine: variable drag treatment (CD ~= abs(CL0)*(CDoCL + dCLdALPHA*ALPHA) near ALPHA == 0)
        A = (2.0 - CDoCL * (CL0 + dCLdALPHA * ALPHAstall)) / (np.pi / 2.0 - ALPHAstall)  # post-stall slope
        
        CD = (CDoCL * abs(CL0)
              + CDoCL * dCLdALPHA * ALPHA * ((1.0 / np.pi) * np.arctan(B * ALPHA) + 0.5)
              - CDoCL * dCLdALPHA * (ALPHA - ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (ALPHA - ALPHAstall)) + 0.5)
              + CDoCL * dCLdALPHA * (-ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHAstall)) + 0.5)
              + A * (ALPHA - ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (ALPHA - ALPHAstall)) + 0.5)
              - A * (-ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHAstall)) + 0.5)
              + CDoCL * dCLdALPHA * (-ALPHA) * ((1.0 / np.pi) * np.arctan(B * (-ALPHA)) + 0.5)
              - CDoCL * dCLdALPHA * (-ALPHA - ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHA - ALPHAstall)) + 0.5)
              + CDoCL * dCLdALPHA * (-ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHAstall)) + 0.5)
              + A * (-ALPHA - ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHA - ALPHAstall)) + 0.5)
              - A * (-ALPHAstall) * ((1.0 / np.pi) * np.arctan(B * (-ALPHAstall)) + 0.5))
    
    return CL, CD
