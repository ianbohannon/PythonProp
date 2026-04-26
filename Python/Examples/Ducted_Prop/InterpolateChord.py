"""
InterpolateChord - Fits cubic B-spline to chord distribution and interpolates

Created: Brenden Epps, 2/18/2011
Ported to Python: 2024

This function fits a cubic B-spline to a given chord distribution and 
interpolates this chord at the desired radii.

INPUTS
  XR      [1,Mx] r/R given radii
  XCoD    [1,Mx] c/D given chord at XR
  RG      [1,Mp] r/R locations to interpolate chord 

OUTPUTS
  CoD     [1,Mp] c/D at RG
"""

import numpy as np
from scipy.interpolate import interp1d, pchip_interpolate


def InterpolateChord(XR, XCoD, RG):
    """Interpolate chord distribution using B-spline curve fitting.

    Parameters
    ----------
    XR : array_like, shape (Mx,)
        Given radii r/R where chord is defined
    XCoD : array_like, shape (Mx,)
        Chord/diameter at XR
    RG : array_like, shape (Mp,)
        Radii r/R where interpolation is required

    Returns
    -------
    CoD : ndarray, shape (Mp,)
        Chord/diameter at RG
    """
    XR = np.asarray(XR).flatten()
    XCoD = np.asarray(XCoD).flatten()
    RG_input = np.asarray(RG)
    original_shape = RG_input.shape
    RG = RG_input.flatten()

    # Check if finite chord at tip (XR == 1 and XCoD > 0.01 at tip)
    if (abs(XR[-1] - 1) < 1e-4) and (XCoD[-1] > 0.01):
        # Allow for finite chord at tip using PCHIP with extrapolation
        CoD = pchip_interpolate(XR, XCoD, RG)
    else:
        # Assume near-zero chord at tip, interpolate using B-spline curve fit
        Mx = len(XR)

        if XR[-1] == 1:
            # Record tip chord length
            CoDtip = XCoD[-1]
            # Set tip chord length to zero to form spline
            XCoD = XCoD.copy()
            XCoD[-1] = 0
        else:
            # Create another data point at the tip
            XR = np.append(XR, 1.0)
            XCoD = np.append(XCoD, 0.0)
            CoDtip = 0
            Mx = Mx + 1

        # Put all numbers in one list: data to fit spline to
        # Mirror the chord distribution to create symmetric blade outline
        xr2 = np.concatenate([XR, XR[Mx-2::-1]])
        xc2 = np.concatenate([XCoD, -XCoD[Mx-2::-1]])

        # Spline inputs
        Md = len(xr2)  # number of spanwise data sites
        m = Md - 1     # number of spline basis functions / control points
        k = 4          # polynomial order (k == 4 for cubic spline)
        Mk = k + m + 1 # number of spanwise knots

        # Find spline parameters using centripetal method
        dseg = np.sqrt(np.diff(xr2)**2 + np.diff(xc2)**2)**0.5
        dtot = np.sum(dseg)
        ubar = np.zeros(Md)
        ubar[1:] = np.cumsum(dseg) / dtot
        ubar[-1] = 1.0  # Force last value to be exactly 1.0 to avoid floating-point precision issues

        # Find spline knots using averaging method
        uknot = np.zeros(Mk)
        uknot[m+1:Mk] = 1.0

        for j in range(m + 1 - k):
            uknot[k + j] = np.sum(ubar[1 + j : 1 + j + k - 1]) / (k - 1)

        # Evaluate the B-spline basis functions
        BC, _, _, _ = Bspline_basis(ubar, uknot, k)

        # Solve linear system for spline amplitudes
        # xr2(ubar) = BC(ubar, uspline) * Axr2(uspline)
        # xc2(ubar) = BC(ubar, uspline) * Axc2(uspline)
        Axr2 = np.linalg.solve(BC, xr2)
        Axc2 = np.linalg.solve(BC, xc2)

        # Evaluate spline on finer resolution
        Mdd = 401
        ubarFINE = np.linspace(0, 1, Mdd)

        BC_fine, _, _, _ = Bspline_basis(ubarFINE, uknot, k)

        xr3 = BC_fine @ Axr2
        xc3 = BC_fine @ Axc2

        # Fine resolution spline radius and chord length data
        xr = xr3[:(Mdd-1)//2 + 1]
        xc = xc3[:(Mdd-1)//2 + 1]

        # FIXED: Use PCHIP with extrapolation to match MATLAB behavior
        # Interpolate spline values at desired radii
        CoDraw = pchip_interpolate(xr, xc, RG)

        # Offset distribution, used to modify chord at the tip
        CoDoffset = (RG - RG[0]) / (1 - RG[0]) * CoDtip

        # Final chord distribution
        CoD = np.sqrt(CoDraw**2 + CoDoffset**2)

    # Reshape if necessary to match input shape
    if CoD.shape[0] == original_shape[-1] and len(original_shape) > 1:
        CoD = CoD.reshape(original_shape)

    return CoD


def Bspline_basis(t, n_or_knot, k):
    """Evaluate B-spline basis functions at points t.

    Parameters
    ----------
    t : array_like, shape (Mt,)
        Vector of field points
    n_or_knot : int or array_like
        If int: spline parameter n, Ms == n+1 == number of splines
        If array: knot vector
    k : int
        Spline order, k == 4 for cubic splines

    Returns
    -------
    B : ndarray, shape (Mt, Ms)
        B-spline basis functions, B[i,j] = basis function j at t[i]
    D1 : ndarray, shape (Mt, Ms)
        First derivative of basis functions
    D2 : ndarray, shape (Mt, Ms)
        Second derivative of basis functions
    knot : ndarray, shape (Mk,)
        Knot vector
    """
    t = np.asarray(t).flatten()
    Mt = len(t)

    # Handle knot sequence
    if np.isscalar(n_or_knot):
        n = n_or_knot
        Mk = k + n + 1

        # Form a uniform knot sequence on [0,1]
        knot = np.zeros(Mk)
        knot[k-1:n+2] = np.linspace(0, 1, n - k + 3)
        knot[n+2:k+n+1] = 1.0
    else:
        knot = np.asarray(n_or_knot).flatten()
        Mk = len(knot)
        n = Mk - k - 1

    maxknot = np.max(knot)
    Ms = n + 1  # number of basis splines

    N = np.zeros((Mk-1, k, Mt))   # B-spline basis functions of order 1,...,k
    N1 = np.zeros((Mk-1, k, Mt))  # 1st derivative
    N2 = np.zeros((Mk-1, k, Mt))  # 2nd derivative

    B = np.zeros((Mt, Ms))        # B-spline basis functions of order k
    D1 = np.zeros((Mt, Ms))       # 1st derivative
    D2 = np.zeros((Mt, Ms))       # 2nd derivative

    # Evaluate B-spline pointwise in t
    for point in range(Mt):
        # Evaluate order 1 basis functions
        j = 0  # Python uses 0-indexing
        for i in range(Mk-1):
            if ((knot[i] <= t[point] < knot[i+1]) or 
                (knot[i] < t[point] and knot[i+1] == maxknot and t[point] == maxknot)):
                N[i, j, point] = 1

        # Apply recursion relation to evaluate higher order basis functions
        for j in range(1, k):  # j = 1 to k-1 (orders 2 to k)
            for i in range(Mk - j - 1):
                denom1 = knot[i+j] - knot[i]
                denom2 = knot[i+j+1] - knot[i+1]

                # Standard recursion
                if denom1 != 0:
                    N[i, j, point] = ((t[point] - knot[i]) / denom1) * N[i, j-1, point]
                else:
                    N[i, j, point] = 0

                if denom2 != 0:
                    N[i, j, point] += ((knot[i+j+1] - t[point]) / denom2) * N[i+1, j-1, point]

        # Extract order k basis functions
        B[point, :] = N[:Ms, k-1, point]

        # Compute first derivatives
        for i in range(Ms):
            denom1 = knot[i+k-1] - knot[i]
            denom2 = knot[i+k] - knot[i+1]

            if denom1 != 0:
                N1[i, k-1, point] = (k-1) / denom1 * N[i, k-2, point]
            else:
                N1[i, k-1, point] = 0

            if denom2 != 0:
                N1[i, k-1, point] -= (k-1) / denom2 * N[i+1, k-2, point]

        D1[point, :] = N1[:Ms, k-1, point]

        # Compute second derivatives
        for i in range(Ms):
            denom1 = knot[i+k-1] - knot[i]
            denom2 = knot[i+k-2] - knot[i]
            denom3 = knot[i+k] - knot[i+1]
            denom4 = knot[i+k-1] - knot[i+1]

            if denom1 != 0 and denom2 != 0:
                N2[i, k-1, point] = (k-1) * (k-2) / (denom1 * denom2) * N[i, k-3, point]
            else:
                N2[i, k-1, point] = 0

            if denom1 != 0 and denom3 != 0:
                N2[i, k-1, point] -= (k-1) * (k-2) / (denom1 * denom3) * N[i+1, k-3, point]

            if denom3 != 0 and denom4 != 0:
                N2[i, k-1, point] += (k-1) * (k-2) / (denom3 * denom4) * N[i+2, k-3, point]

        D2[point, :] = N2[:Ms, k-1, point]

    return B, D1, D2, knot


def pchip1d(x, y, xi):
    """PCHIP 1-D interpolation (shape-preserving piecewise cubic).
    
    Parameters
    ----------
    x : array_like
        Known x values
    y : array_like
        Known y values
    xi : array_like
        Query points
    
    Returns
    -------
    yi : ndarray
        Interpolated values at xi
    """
    from scipy.interpolate import PchipInterpolator
    return PchipInterpolator(x, y, extrapolate=True)(xi)
