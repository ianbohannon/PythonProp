"""
Export blade geometry to STL file format for CAD import.

This module provides functionality to convert the generated blade geometry
into STL (STereoLithography) format, which can be imported into most CAD packages.
"""

import numpy as np
import struct


def export_blade_to_stl(geometry, filename, units='mm', ascii_format=False, include_hub=True, single_blade=True):
    """
    Export blade geometry to STL file format.
    
    Parameters
    ----------
    geometry : dict
        Geometry dictionary containing:
        - X3D: 3D X coordinates (Mp+1, 2*Np, Z) [normalized or m]
        - Y3D: 3D Y coordinates (Mp+1, 2*Np, Z) [normalized or m]
        - Z3D: 3D Z coordinates (Mp+1, 2*Np, Z) [normalized or m]
        - Z: number of blades
        - D: propeller diameter [m]
        - Dhub: hub diameter [m]
    filename : str
        Output filename (without .stl extension)
    units : str, optional
        Output units ('mm' or 'm'). Default is 'mm' (millimeters).
        The geometry will be scaled so the propeller diameter matches
        the value specified in geometry['D'].
    ascii_format : bool, optional
        If True, write ASCII STL format. If False (default), write binary STL.
        Binary format is more compact and widely supported.
    include_hub : bool, optional
        If True (default), include cylindrical hub in the export
    single_blade : bool, optional
        If True, export only a single blade. If False (default), export all blades.
    
    Returns
    -------
    str
        Full path to the written STL file
    """
    if 'X3D' not in geometry or 'Y3D' not in geometry or 'Z3D' not in geometry:
        raise ValueError("Geometry dictionary must contain X3D, Y3D, and Z3D coordinates")
    
    X3D = geometry['X3D'].copy()
    Y3D = geometry['Y3D'].copy()
    Z3D = geometry['Z3D'].copy()
    Z_blades = geometry['Z']
    D = geometry['D']  # Diameter in meters
    Dhub = geometry.get('Dhub', 0.0)  # Hub diameter in meters
    
    # Calculate the current diameter in the geometry to determine if it's normalized
    max_radius = 0.0
    Mp = X3D.shape[0] - 1
    Np2 = X3D.shape[1]
    for i in range(Mp + 1):
        for j in range(Np2):
            for k in range(Z_blades):
                radius = np.sqrt(Y3D[i, j, k]**2 + Z3D[i, j, k]**2)
                max_radius = max(max_radius, radius)
    
    current_diameter = 2 * max_radius
    
    # Scale coordinates to match the input diameter D
    # This handles both normalized geometry and geometry in different units
    diameter_scale = D / current_diameter if current_diameter > 0 else 1.0
    
    X3D = X3D * diameter_scale
    Y3D = Y3D * diameter_scale
    Z3D = Z3D * diameter_scale
    
    # Now convert to target units
    if units.lower() == 'mm':
        unit_scale = 1000.0  # Convert meters to millimeters
        unit_label = 'millimeters'
    elif units.lower() == 'm':
        unit_scale = 1.0  # Keep in meters
        unit_label = 'meters'
    else:
        raise ValueError(f"Unsupported units: {units}. Use 'mm' or 'm'.")
    
    X3D = X3D * unit_scale
    Y3D = Y3D * unit_scale
    Z3D = Z3D * unit_scale
    
    # Get dimensions
    Mp = X3D.shape[0] - 1  # Number of radial panels
    Np2 = X3D.shape[1]     # Total points around section (2*Np)
    
    # Add .stl extension if not present
    if not filename.lower().endswith('.stl'):
        filename = filename + '.stl'
    
    # Generate triangular mesh for each blade
    triangles = []
    
    # Determine how many blades to export
    num_blades_to_export = 1 if single_blade else Z_blades
    
    for blade_idx in range(num_blades_to_export):
        # Extract coordinates for this blade
        X = X3D[:, :, blade_idx]
        Y = Y3D[:, :, blade_idx]
        Z = Z3D[:, :, blade_idx]
        
        # Create triangular mesh by connecting adjacent radial sections
        for i in range(Mp):
            for j in range(Np2):
                j_next = (j + 1) % Np2  # Wrap around to close the section
                
                # Get four corners of the quadrilateral panel
                p1 = np.array([X[i, j], Y[i, j], Z[i, j]], dtype=np.float32)
                p2 = np.array([X[i, j_next], Y[i, j_next], Z[i, j_next]], dtype=np.float32)
                p3 = np.array([X[i+1, j_next], Y[i+1, j_next], Z[i+1, j_next]], dtype=np.float32)
                p4 = np.array([X[i+1, j], Y[i+1, j], Z[i+1, j]], dtype=np.float32)
                
                # Split quadrilateral into two triangles
                # Triangle 1: p1, p2, p3
                if _is_valid_triangle(p1, p2, p3):
                    triangles.append((p1, p2, p3))
                
                # Triangle 2: p1, p3, p4
                if _is_valid_triangle(p1, p3, p4):
                    triangles.append((p1, p3, p4))
        
        # Add caps at hub and tip to create closed solid
        # Hub cap (inner radius) - fan triangulation from center
        hub_center = np.array([
            np.mean(X[0, :]),
            np.mean(Y[0, :]),
            np.mean(Z[0, :])
        ], dtype=np.float32)
        
        for j in range(Np2):
            j_next = (j + 1) % Np2
            p1 = hub_center
            p2 = np.array([X[0, j], Y[0, j], Z[0, j]], dtype=np.float32)
            p3 = np.array([X[0, j_next], Y[0, j_next], Z[0, j_next]], dtype=np.float32)
            if _is_valid_triangle(p1, p2, p3):
                triangles.append((p1, p2, p3))
        
        # Tip cap (outer radius) - fan triangulation from center (reverse winding)
        tip_center = np.array([
            np.mean(X[Mp, :]),
            np.mean(Y[Mp, :]),
            np.mean(Z[Mp, :])
        ], dtype=np.float32)
        
        for j in range(Np2):
            j_next = (j + 1) % Np2
            p1 = tip_center
            p2 = np.array([X[Mp, j_next], Y[Mp, j_next], Z[Mp, j_next]], dtype=np.float32)
            p3 = np.array([X[Mp, j], Y[Mp, j], Z[Mp, j]], dtype=np.float32)
            if _is_valid_triangle(p1, p2, p3):
                triangles.append((p1, p2, p3))
    
    # Add cylindrical hub if requested and hub diameter > 0
    if include_hub and Dhub > 0:
        hub_triangles = _generate_hub_mesh(X3D, Y3D, Z3D, Dhub * diameter_scale * unit_scale, n_segments=64)
        triangles.extend(hub_triangles)
        print(f"  Hub diameter: {Dhub:.4f} m ({Dhub*unit_scale:.2f} {units})")
    
    # Write STL file
    if ascii_format:
        _write_stl_ascii(filename, triangles)
    else:
        _write_stl_binary(filename, triangles)
    
    print(f"STL file written: {filename}")
    print(f"  Propeller diameter: {D:.4f} m ({D*unit_scale:.2f} {units})")
    print(f"  Number of blades exported: {num_blades_to_export} (of {Z_blades} total)")
    print(f"  Number of triangles: {len(triangles)}")
    print(f"  Output units: {unit_label}")
    
    return filename


def _generate_hub_mesh(X3D, Y3D, Z3D, Dhub_scaled, n_segments=64):
    """
    Generate triangular mesh for cylindrical hub.
    
    Parameters
    ----------
    X3D, Y3D, Z3D : ndarray
        Scaled blade coordinates
    Dhub_scaled : float
        Hub diameter in the same units as coordinates
    n_segments : int
        Number of circumferential segments
    
    Returns
    -------
    list of tuples
        List of triangle tuples (p1, p2, p3)
    """
    triangles = []
    
    Rhub = Dhub_scaled / 2.0
    
    # Determine axial extent from blade geometry
    x_min = np.min(X3D)
    x_max = np.max(X3D)
    
    # Extend hub slightly beyond blade extent
    x_buffer = (x_max - x_min) * 0.05
    x_min -= x_buffer
    x_max += x_buffer
    
    # Generate circumferential points
    theta = np.linspace(0, 2*np.pi, n_segments + 1)
    
    # Generate cylinder surface
    for i in range(n_segments):
        y1 = Rhub * np.cos(theta[i])
        z1 = Rhub * np.sin(theta[i])
        y2 = Rhub * np.cos(theta[i + 1])
        z2 = Rhub * np.sin(theta[i + 1])
        
        # Four corners of the rectangular panel
        p1 = np.array([x_min, y1, z1], dtype=np.float32)
        p2 = np.array([x_min, y2, z2], dtype=np.float32)
        p3 = np.array([x_max, y2, z2], dtype=np.float32)
        p4 = np.array([x_max, y1, z1], dtype=np.float32)
        
        # Two triangles for cylinder wall
        triangles.append((p1, p2, p3))
        triangles.append((p1, p3, p4))
        
        # End caps
        center_front = np.array([x_min, 0.0, 0.0], dtype=np.float32)
        center_back = np.array([x_max, 0.0, 0.0], dtype=np.float32)
        
        # Front cap (pointing in -X direction)
        triangles.append((center_front, p1, p2))
        
        # Rear cap (pointing in +X direction)
        triangles.append((center_back, p3, p4))
    
    return triangles


def _is_valid_triangle(p1, p2, p3, min_area=1e-6):
    """Check if triangle is valid (non-degenerate and has finite coordinates)."""
    # Check for NaN or Inf
    if not (np.all(np.isfinite(p1)) and np.all(np.isfinite(p2)) and np.all(np.isfinite(p3))):
        return False
    
    # Check triangle area (cross product magnitude)
    v1 = p2 - p1
    v2 = p3 - p1
    cross = np.cross(v1, v2)
    area = np.linalg.norm(cross)
    
    return area > min_area


def _calculate_normal(p1, p2, p3):
    """Calculate unit normal vector for a triangle."""
    v1 = p2 - p1
    v2 = p3 - p1
    normal = np.cross(v1, v2)
    norm_length = np.linalg.norm(normal)
    
    if norm_length > 1e-10:
        normal = normal / norm_length
    else:
        # Degenerate triangle, use default normal
        normal = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    
    return normal.astype(np.float32)


def _write_stl_ascii(filename, triangles):
    """Write STL file in ASCII format."""
    with open(filename, 'w') as f:
        f.write("solid blade_geometry\n")
        
        for tri in triangles:
            p1, p2, p3 = tri
            
            # Calculate normal vector
            normal = _calculate_normal(p1, p2, p3)
            
            f.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
            f.write(f"    outer loop\n")
            f.write(f"      vertex {p1[0]:.6e} {p1[1]:.6e} {p1[2]:.6e}\n")
            f.write(f"      vertex {p2[0]:.6e} {p2[1]:.6e} {p2[2]:.6e}\n")
            f.write(f"      vertex {p3[0]:.6e} {p3[1]:.6e} {p3[2]:.6e}\n")
            f.write(f"    endloop\n")
            f.write(f"  endfacet\n")
        
        f.write("endsolid blade_geometry\n")


def _write_stl_binary(filename, triangles):
    """Write STL file in binary format (more compact and efficient)."""
    with open(filename, 'wb') as f:
        # Write 80-byte header
        header = b'Binary STL - Blade Geometry' + b'\0' * (80 - 27)
        f.write(header)
        
        # Write number of triangles (uint32, little-endian)
        num_triangles = len(triangles)
        f.write(struct.pack('<I', num_triangles))
        
        # Write each triangle
        for tri in triangles:
            p1, p2, p3 = tri
            
            # Ensure float32 type
            p1 = np.array(p1, dtype=np.float32)
            p2 = np.array(p2, dtype=np.float32)
            p3 = np.array(p3, dtype=np.float32)
            
            # Calculate normal vector
            normal = _calculate_normal(p1, p2, p3)
            
            # Write normal (3 float32, little-endian)
            f.write(struct.pack('<fff', float(normal[0]), float(normal[1]), float(normal[2])))
            
            # Write vertices (9 float32, little-endian)
            f.write(struct.pack('<fff', float(p1[0]), float(p1[1]), float(p1[2])))
            f.write(struct.pack('<fff', float(p2[0]), float(p2[1]), float(p2[2])))
            f.write(struct.pack('<fff', float(p3[0]), float(p3[1]), float(p3[2])))
            
            # Write attribute byte count (uint16) - always 0
            f.write(struct.pack('<H', 0))


def export_hub_to_stl(geometry, filename, n_segments=32, ascii_format=False):
    """
    Export hub geometry to STL file format (cylindrical hub).
    
    Parameters
    ----------
    geometry : dict
        Geometry dictionary containing:
        - Dhub: hub diameter [m]
        - D: propeller diameter [m]
        - X3D: 3D coordinates for determining axial extent
    filename : str
        Output filename (without .stl extension)
    n_segments : int, optional
        Number of circumferential segments for hub cylinder (default: 32)
    ascii_format : bool, optional
        If True, write ASCII STL format. If False (default), write binary STL.
    
    Returns
    -------
    str
        Full path to the written STL file
    """
    if 'Dhub' not in geometry:
        raise ValueError("Geometry dictionary must contain Dhub (hub diameter)")
    
    Dhub = geometry['Dhub']
    D = geometry['D']
    
    if Dhub <= 0:
        raise ValueError("Hub diameter must be greater than 0")
    
    # Scale to millimeters
    scale_factor = 1000
    
    # Use the helper function to generate hub mesh
    X3D = geometry['X3D'] * scale_factor
    Y3D = geometry['Y3D'] * scale_factor
    Z3D = geometry['Z3D'] * scale_factor
    
    triangles = _generate_hub_mesh(X3D, Y3D, Z3D, Dhub * scale_factor, n_segments)
    
    # Add .stl extension if not present
    if not filename.lower().endswith('.stl'):
        filename = filename + '.stl'
    
    # Write STL file
    if ascii_format:
        _write_stl_ascii(filename, triangles)
    else:
        _write_stl_binary(filename, triangles)
    
    print(f"Hub STL file written: {filename}")
    print(f"  Hub diameter: {Dhub:.4f} m ({Dhub*scale_factor:.2f} mm)")
    print(f"  Number of triangles: {len(triangles)}")
    print(f"  Output units: millimeters")
    
    return filename