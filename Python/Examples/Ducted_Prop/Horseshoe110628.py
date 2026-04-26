"""
Horseshoe110628 - Compute vortex Horseshoe Influence Functions

Created: 6/28/2011, Brenden Epps
Ported to Python: 2024

This function computes the vortex Horseshoe Influence Functions given
in Kerwin, p.179.

UAHIF = 2*pi*R*(HIF in Kerwin)
UTHIF = 2*pi*R*(HIF in Kerwin)

UAHIF(n,m) = influence of mth horseshoe vortex on nth control point

Locally-constant-pitch wake assumption is made:

            |
            |            
            |
            *---------------       
            |            
            |  <--- RC(n)
            |
            *---------------
            |
            |
            |        
            *--------------- r1 = RV(m+1);  TANBIV1 = TANBIC(m)*RC(m)/RV(m+1) 
            |
            |  <--- RC(m), TANBIC(m), G(m)
            |
            *--------------- r2 = RV(m  );  TANBIV2 = TANBIC(m)*RC(m)/RV(m)
            |
            |
            |

Sign convention:

The circulation is defined positive when it is directed AWAY from 
the lifting line.

UASTAR is defined positive in the downstream direction
UTSTAR is defined positive in the direction of the apparent inflow, omega*r
"""

import numpy as np
from Wrench import Wrench


def Horseshoe110628(Mp, Z, TANBIC, RC, RV, Hub_flag, Rhub_oR, Duct_flag, Rduct_oR):
    """Compute horseshoe vortex influence coefficient matrices.

    Ported from SourceCode/Horseshoe110628.m

    UAHIF(n, m) is the axial velocity induced at control point n by
    a unit horseshoe vortex shed from panel m (scaled by 2*pi*R).

    Parameters
    ----------
    Mp : int
        Number of blade panels
    Z : int
        Number of blades
    TANBIC : array_like, shape (Mp,)
        tan(beta_i) at each control point
    RC : array_like, shape (Mp,)
        Control-point radii (r/R)
    RV : array_like, shape (Mp+1,)
        Vortex-point radii (r/R)
    Hub_flag : int
        1 to include hub image vortices, 0 otherwise
    Rhub_oR : float
        Hub radius / propeller radius
    Duct_flag : int
        1 to include duct image vortices, 0 otherwise
    Rduct_oR : float
        Duct radius / propeller radius

    Returns
    -------
    UAHIF : ndarray, shape (Mp, Mp)
        Axial horseshoe influence functions (2*pi*R * HIF)
    UTHIF : ndarray, shape (Mp, Mp)
        Tangential horseshoe influence functions (2*pi*R * HIF)
    """
    # Ensure inputs are arrays
    TANBIC = np.asarray(TANBIC, dtype=float)
    RC = np.asarray(RC, dtype=float)
    RV = np.asarray(RV, dtype=float)

    # Initialize influence function matrices
    UAHIF = np.zeros((Mp, Mp))
    UTHIF = np.zeros((Mp, Mp))

    # For each control point, n (FOR LOOP MF2)
    for n in range(Mp):
        # For each vortex panel, m (FOR LOOP MF3)
        for m in range(Mp):
            # rc = RC(n)
            # r1 = RV(m+1);  TANBIV1 = TANBIC(m)*RC(m)/RV(m+1)
            # r2 = RV(m  );  TANBIV2 = TANBIC(m)*RC(m)/RV(m)

            # Velocity induced at RC(n) by a unit vortex shed at RV(m+1)
            # Wrench returns 2*pi*R*u_bar
            UAW1, UTW1 = Wrench(Z, TANBIC[m] * RC[m] / RV[m + 1], RC[n], RV[m + 1])

            # Velocity induced at RC(n) by a unit vortex shed at RV(m)
            # Wrench returns 2*pi*R*u_bar
            UAW2, UTW2 = Wrench(Z, TANBIC[m] * RC[m] / RV[m], RC[n], RV[m])

            # Find hub-image effects, Kerwin p.181
            if Hub_flag == 1:
                UAWh1, UTWh1 = Wrench(Z, TANBIC[m] * RC[m] / (Rhub_oR**2 / RV[m + 1]), 
                                     RC[n], Rhub_oR**2 / RV[m + 1])
                UAWh2, UTWh2 = Wrench(Z, TANBIC[m] * RC[m] / (Rhub_oR**2 / RV[m]), 
                                     RC[n], Rhub_oR**2 / RV[m])

                UAW1 = UAW1 - UAWh1
                UAW2 = UAW2 - UAWh2

                UTW1 = UTW1 - UTWh1
                UTW2 = UTW2 - UTWh2

            # Find duct-image effects
            if Duct_flag == 1:
                UAWd1, UTWd1 = Wrench(Z, TANBIC[m] * RC[m] / (Rduct_oR**2 / RV[m + 1]), 
                                     RC[n], Rduct_oR**2 / RV[m + 1])
                UAWd2, UTWd2 = Wrench(Z, TANBIC[m] * RC[m] / (Rduct_oR**2 / RV[m]), 
                                     RC[n], Rduct_oR**2 / RV[m])

                UAW1 = UAW1 - UAWd1
                UAW2 = UAW2 - UAWd2

                UTW1 = UTW1 - UTWd1
                UTW2 = UTW2 - UTWd2

            # Determine the Horseshoe Influence Function
            # The Horseshoe Influence Function for vortex panel m is the
            # effect of the induction by a helical trailing vortex at:
            # vortex point m   with circulation -Gamma(m) and another at
            # vortex point m+1 with circulation +Gamma(m).
            # UAHIF(n,m) = u_barA horseshoe influence function in eqn 254.
            # UAW(m)     = u_barA Wrench velocity given in eqn 202-203.
            # Note that the Wrench velocity assumes that a positive circulation is
            # directed AWAY from the lifting line.
            UAHIF[n, m] = UAW1 - UAW2  # 2*pi*R*(HIF)
            UTHIF[n, m] = UTW1 - UTW2  # 2*pi*R*(HIF)

    return UAHIF, UTHIF


# -------------------------------------------------------------------------
# Any escape might help to smooth the unattractive truth
# But the suburbs have no charms to soothe the restless dreams of youth
# -------------------------------------------------------------------------
