# Port target: SourceCode/elliptic12.m
"""Incomplete elliptic integrals of the first and second kind, and Jacobi's Zeta function.

ELLIPTIC12 evaluates the value of the Incomplete Elliptic Integrals
of the First, Second Kind and Jacobi's Zeta Function.

Uses the method of the Arithmetic-Geometric Mean and Descending Landen 
Transformation described in Abramowitz & Stegun Ch. 17.6.

References:
    [1] M. Abramowitz and I.A. Stegun, "Handbook of Mathematical Functions",
        Dover Publications, 1965, Ch. 17.1 - 17.6.
    [2] D. F. Lawden, "Elliptic Functions and Applications"
        Springer-Verlag, vol. 80, 1989.

GNU GENERAL PUBLIC LICENSE Version 2, June 1991
Copyright (C) 2007 by Moiseev Igor. All rights reserved.
"""

import numpy as np


def elliptic12(u, m, tol=None):
    """Compute incomplete elliptic integrals and Jacobi's Zeta function.

    Parameters
    ----------
    u : float or array_like
        Phase in radians.
    m : float or array_like
        Module parameter (0 <= m <= 1).
    tol : float, optional
        Tolerance for convergence. Default is machine epsilon (np.finfo(float).eps).

    Returns
    -------
    F : ndarray
        Incomplete elliptic integral of the first kind:
        F(phi,m) = integral(1/sqrt(1-m*sin(t)^2), t=0..phi)
    E : ndarray
        Incomplete elliptic integral of the second kind:
        E(phi,m) = integral(sqrt(1-m*sin(t)^2), t=0..phi)
    Z : ndarray
        Jacobi's Zeta function:
        Z(phi,m) = E(u,m) - E(m)/K(m)*F(phi,m)

    Notes
    -----
    For real inputs only. For complex arguments, a separate implementation
    would be needed (elliptic12i in the original MATLAB).
    
    Special cases:
        - m == 0: F(u,0) = u, E(u,0) = u, Z(u,0) = 0
        - m == 1: F(u,1) = log(tan(pi/4 + u/2)) for |u| < pi/2
                  F(u,1) = ±Inf for |u| >= pi/2
                  E(u,1) = sin(u) (with period adjustments)
                  Z(u,1) = sin(u) (with period adjustments)
    """
    if tol is None:
        tol = np.finfo(float).eps
    
    # Convert to numpy arrays
    u = np.asarray(u, dtype=float)
    m = np.asarray(m, dtype=float)
    
    # Ensure u and m are same size
    if u.size == 1:
        u = np.full_like(m, u.item())
    if m.size == 1:
        m = np.full_like(u, m.item())
    
    if u.shape != m.shape:
        raise ValueError('U and M must be the same size.')
    
    if not np.isreal(u).all() or not np.isreal(m).all():
        raise ValueError('Input arguments must be real.')
    
    if np.any(m < 0) or np.any(m > 1):
        raise ValueError('M must be in the range 0 <= M <= 1.')
    
    # Initialize output arrays
    original_shape = u.shape
    m = m.ravel()
    u = u.ravel()
    
    F = np.zeros_like(u)
    E = np.zeros_like(u)
    Z = np.zeros_like(u)
    
    # Find indices where m is not 0 or 1
    I = np.where((m != 1) & (m != 0))[0]
    
    if len(I) > 0:
        # Extract unique values of m for efficiency
        mu, J, K = np.unique(m[I], return_index=True, return_inverse=True)
        mumax = len(mu)
        signU = np.sign(u[I])
        
        # Pre-allocate space for AGM iteration
        chunk = 7
        a = np.zeros((chunk, mumax))
        c = np.zeros((chunk, mumax))
        b = np.zeros((chunk, mumax))
        
        a[0, :] = 1.0
        c[0, :] = np.sqrt(mu)
        b[0, :] = np.sqrt(1 - mu)
        n = np.zeros(mumax, dtype=int)
        
        # Arithmetic-Geometric Mean iteration
        i = 0
        while np.any(np.abs(c[i, :]) > tol):
            i += 1
            if i >= a.shape[0]:
                # Augment arrays if needed
                a = np.vstack([a, np.zeros((2, mumax))])
                b = np.vstack([b, np.zeros((2, mumax))])
                c = np.vstack([c, np.zeros((2, mumax))])
            
            a[i, :] = 0.5 * (a[i-1, :] + b[i-1, :])
            b[i, :] = np.sqrt(a[i-1, :] * b[i-1, :])
            c[i, :] = 0.5 * (a[i-1, :] - b[i-1, :])
            
            # Track which indices have converged
            converged = np.where((np.abs(c[i, :]) <= tol) & (np.abs(c[i-1, :]) > tol))[0]
            if len(converged) > 0:
                n[converged] = i - 1
        
        mmax = len(I)
        mn = int(np.max(n))
        
        # Initialize for Descending Landen Transformation
        phin = np.zeros(mmax)
        C = np.zeros(mmax)
        Cp = np.zeros(mmax)
        e = np.zeros(mmax, dtype=int)
        phin[:] = signU * u[I]
        
        c2 = c ** 2
        
        # Descending Landen Transformation
        for i in range(mn):
            idx = np.where(n[K] > i)[0]
            if len(idx) > 0:
                Ki = K[idx]
                phin[idx] = (np.arctan(b[i, Ki] / a[i, Ki] * np.tan(phin[idx])) +
                            np.pi * np.ceil(phin[idx] / np.pi - 0.5) + phin[idx])
                e[idx] = 2 ** i
                C[idx] = C[idx] + e[idx] * c2[i, Ki]
                Cp[idx] = Cp[idx] + c[i+1, Ki] * np.sin(phin[idx])
        
        # Compute final values
        Ff = phin / (a[mn, K] * e * 2)
        F[I] = Ff * signU
        Z[I] = Cp * signU
        E[I] = (Cp + (1 - 0.5 * C) * Ff) * signU
    
    # Special case: m == 0
    m0 = np.where(m == 0)[0]
    if len(m0) > 0:
        F[m0] = u[m0]
        E[m0] = u[m0]
        Z[m0] = 0
    
    # Special case: m == 1
    m1 = np.where(m == 1)[0]
    if len(m1) > 0:
        um1 = np.abs(u[m1])
        N = np.floor((um1 + np.pi/2) / np.pi)
        M = np.where(um1 < np.pi/2)[0]
        
        # F values
        F_m1 = np.full_like(um1, np.inf)
        if len(M) > 0:
            F_m1[M] = np.log(np.tan(np.pi/4 + u[m1[M]]/2))
        F_m1[um1 >= np.pi/2] = np.inf * np.sign(u[m1[um1 >= np.pi/2]])
        F[m1] = F_m1
        
        # E values
        E[m1] = ((-1)**N * np.sin(um1) + 2*N) * np.sign(u[m1])
        
        # Z values
        Z[m1] = (-1)**N * np.sin(u[m1])
    
    # Reshape to original shape
    F = F.reshape(original_shape)
    E = E.reshape(original_shape)
    Z = Z.reshape(original_shape)
    
    return F, E, Z
