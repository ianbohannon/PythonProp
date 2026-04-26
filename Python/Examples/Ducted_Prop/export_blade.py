"""Export blade geometry to various CAD formats (STEP, STL, CSV).

This module provides functions to export propeller blade geometry generated
by Geometry() to common CAD file formats for import into SolidWorks, Fusion 360,
Rhino, CATIA, and other 3D modeling software.

Supported formats:
- STEP (.step, .stp) - Industry standard, parametric
- STL (.stl) - Universal mesh format
- CSV (.csv) - Point cloud format

Created: 2024
"""

import numpy as np
import os


def export_blade_geometry(pt, output_dir=".", formats=None):
    """Export blade geometry to multiple CAD formats.
    
    Parameters
    ----------
    pt : dict
        Propeller/turbine data structure with 'geometry' dict containing
        X3D, Y3D, Z3D arrays (shape: Mp+1 x 2*Np)
    output_dir : str, optional
        Output directory for exported files. Default is current directory.
    formats : list of str, optional
        List of formats to export: ['step', 'stl', 'csv']
        If None, exports all available formats.
    
    Returns
    -------
    exported_files : list of str
        List of successfully exported file paths
    
    Examples
    --------
    >>> pt = run_design()  # Run propeller design
    >>> files = export_blade_geometry(pt, output_dir="output", formats=['step', 'stl'])
    >>> print(f"Exported: {files}")
    """
    if formats is None:
        formats = ['step', 'stl', 'csv']
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract geometry data
    geom = pt.get('geometry', {})
    if 'X3D' not in geom or 'Y3D' not in geom or 'Z3D' not in geom:
        raise ValueError("Geometry data (X3D, Y3D, Z3D) not found in pt['geometry']. "
                        "Run Geometry(pt) first.")
    
    X3D = geom['X3D']
    Y3D = geom['Y3D']
    Z3D = geom['Z3D']
    Z = pt['input']['Z']  # Number of blades
    
    filename_base = pt.get('filename', 'propeller')
    exported_files = []
    
    # Export STEP file
    if 'step' in formats or 'stp' in formats:
        try:
            step_file = os.path.join(output_dir, f"{filename_base}.step")
            export_to_step(X3D, Y3D, Z3D, step_file, num_blades=Z)
            exported_files.append(step_file)
            print(f"✓ Exported STEP: {step_file}")
        except Exception as e:
            print(f"✗ STEP export failed: {e}")
    
    # Export STL file
    if 'stl' in formats:
        try:
            stl_file = os.path.join(output_dir, f"{filename_base}.stl")
            export_to_stl(X3D, Y3D, Z3D, stl_file, num_blades=Z)
            exported_files.append(stl_file)
            print(f"✓ Exported STL: {stl_file}")
        except Exception as e:
            print(f"✗ STL export failed: {e}")
    
    # Export CSV point cloud
    if 'csv' in formats:
        try:
            csv_file = os.path.join(output_dir, f"{filename_base}_points.csv")
            export_to_csv(X3D, Y3D, Z3D, csv_file, num_blades=Z)
            exported_files.append(csv_file)
            print(f"✓ Exported CSV: {csv_file}")
        except Exception as e:
            print(f"✗ CSV export failed: {e}")
    
    return exported_files


def export_to_step(X3D, Y3D, Z3D, filename, num_blades=1):
    """Export blade surface to STEP file format using OCC/CadQuery.
    
    Parameters
    ----------
    X3D, Y3D, Z3D : ndarray, shape (Mp+1, 2*Np)
        3D blade surface coordinates (single blade)
    filename : str
        Output STEP filename (.step or .stp)
    num_blades : int, optional
        Number of blades to export (rotated around X-axis). Default is 1.
    
    Notes
    -----
    Requires either:
    - cadquery: `pip install cadquery`
    - OCP (OpenCascade): `pip install OCP`
    
    The blade surface is fitted as a B-spline surface and replicated
    for multiple blades by rotation around the X-axis.
    """
    try:
        from OCP.gp import gp_Pnt
        from OCP.TColgp import TColgp_Array2OfPnt
        from OCP.GeomAPI import GeomAPI_PointsToBSplineSurface
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
        from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.gp import gp_Trsf, gp_Ax1, gp_Dir
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        use_ocp = True
    except ImportError:
        try:
            import cadquery as cq
            use_ocp = False
        except ImportError:
            raise ImportError(
                "STEP export requires either 'OCP' or 'cadquery' package.\n"
                "Install with: pip install OCP   OR   pip install cadquery"
            )
    
    Mp, Np2 = X3D.shape
    Np = Np2 // 2  # Half the points (pressure and suction sides)
    
    if use_ocp:
        # === OCP (OpenCascade) Implementation ===
        writer = STEPControl_Writer()
        
        for blade_idx in range(num_blades):
            angle = blade_idx * 2 * np.pi / num_blades
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            
            # Create point array for B-spline surface
            # Use only one side (e.g., pressure side) for surface
            points_array = TColgp_Array2OfPnt(1, Mp, 1, Np)
            
            for i in range(Mp):
                for j in range(Np):
                    x = X3D[i, j]
                    y = Y3D[i, j] * cos_a - Z3D[i, j] * sin_a
                    z = Y3D[i, j] * sin_a + Z3D[i, j] * cos_a
                    points_array.SetValue(i + 1, j + 1, gp_Pnt(x, y, z))
            
            # Fit B-spline surface to points
            surface_builder = GeomAPI_PointsToBSplineSurface(points_array)
            if not surface_builder.IsDone():
                raise RuntimeError(f"Failed to create B-spline surface for blade {blade_idx + 1}")
            
            surface = surface_builder.Surface()
            
            # Create face from surface
            face_builder = BRepBuilderAPI_MakeFace(surface, 1e-6)
            if not face_builder.IsDone():
                raise RuntimeError(f"Failed to create face for blade {blade_idx + 1}")
            
            face = face_builder.Face()
            
            # Add to STEP file
            writer.Transfer(face, STEPControl_AsIs)
        
        # Write STEP file
        status = writer.Write(filename)
        if status != IFSelect_RetDone:
            raise RuntimeError(f"STEP file write failed with status {status}")
    
    else:
        # === CadQuery Implementation ===
        blades = []
        
        for blade_idx in range(num_blades):
            angle = blade_idx * 2 * np.pi / num_blades
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            
            # Create spline curves along chord at each radial station
            splines = []
            for i in range(Mp):
                points = []
                for j in range(Np2):
                    x = X3D[i, j]
                    y = Y3D[i, j] * cos_a - Z3D[i, j] * sin_a
                    z = Y3D[i, j] * sin_a + Z3D[i, j] * cos_a
                    points.append((x, y, z))
                
                # Create spline through points
                spline = cq.Edge.makeSpline([cq.Vector(*pt) for pt in points])
                splines.append(spline)
            
            # Loft surface through splines
            blade_surface = cq.Workplane("XY").add(
                cq.Solid.makeLoft([cq.Wire.assembleEdges([s]) for s in splines])
            )
            blades.append(blade_surface)
        
        # Combine all blades
        assembly = blades[0]
        for blade in blades[1:]:
            assembly = assembly.union(blade)
        
        # Export to STEP
        cq.exporters.export(assembly, filename)


def export_to_stl(X3D, Y3D, Z3D, filename, num_blades=1):
    """Export blade surface to STL mesh format.
    
    Parameters
    ----------
    X3D, Y3D, Z3D : ndarray, shape (Mp+1, 2*Np)
        3D blade surface coordinates (single blade)
    filename : str
        Output STL filename
    num_blades : int, optional
        Number of blades to export (rotated around X-axis). Default is 1.
    
    Notes
    -----
    Requires numpy-stl: `pip install numpy-stl`
    
    Creates a triangulated mesh from the blade surface points.
    Suitable for import into SolidWorks, Fusion 360, Rhino, etc.
    """
    try:
        from stl import mesh
    except ImportError:
        raise ImportError(
            "STL export requires 'numpy-stl' package.\n"
            "Install with: pip install numpy-stl"
        )
    
    Mp, Np2 = X3D.shape
    
    vertices = []
    faces = []
    
    for blade_idx in range(num_blades):
        angle = blade_idx * 2 * np.pi / num_blades
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        
        # Create vertices for this blade (rotated)
        v_offset = len(vertices)
        for i in range(Mp):
            for j in range(Np2):
                x = X3D[i, j]
                y = Y3D[i, j] * cos_a - Z3D[i, j] * sin_a
                z = Y3D[i, j] * sin_a + Z3D[i, j] * cos_a
                vertices.append([x, y, z])
        
        # Create triangular faces between grid points
        for i in range(Mp - 1):
            for j in range(Np2 - 1):
                # Vertex indices for quad
                v1 = v_offset + i * Np2 + j
                v2 = v_offset + i * Np2 + (j + 1)
                v3 = v_offset + (i + 1) * Np2 + j
                v4 = v_offset + (i + 1) * Np2 + (j + 1)
                
                # Split quad into two triangles
                faces.append([v1, v2, v3])
                faces.append([v2, v4, v3])
    
    vertices = np.array(vertices)
    faces = np.array(faces)
    
    # Create mesh
    blade_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            blade_mesh.vectors[i][j] = vertices[f[j], :]
    
    # Save STL file
    blade_mesh.save(filename)


def export_to_csv(X3D, Y3D, Z3D, filename, num_blades=1):
    """Export blade surface points to CSV point cloud format.
    
    Parameters
    ----------
    X3D, Y3D, Z3D : ndarray, shape (Mp+1, 2*Np)
        3D blade surface coordinates (single blade)
    filename : str
        Output CSV filename
    num_blades : int, optional
        Number of blades to export (rotated around X-axis). Default is 1.
    
    Notes
    -----
    CSV format: X, Y, Z (one point per row)
    Can be imported into CAD software as a point cloud:
    - SolidWorks: Insert > Curve > Curve Through XYZ Points
    - Fusion 360: Create Sketch > Create > Spline through Points
    - Rhino: ImportPointCloud command
    """
    Mp, Np2 = X3D.shape
    
    all_points = []
    
    for blade_idx in range(num_blades):
        angle = blade_idx * 2 * np.pi / num_blades
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        
        for i in range(Mp):
            for j in range(Np2):
                x = X3D[i, j]
                y = Y3D[i, j] * cos_a - Z3D[i, j] * sin_a
                z = Y3D[i, j] * sin_a + Z3D[i, j] * cos_a
                all_points.append([x, y, z])
    
    points_array = np.array(all_points)
    
    # Save to CSV with header
    np.savetxt(filename, points_array, delimiter=',', 
               header='X,Y,Z', comments='', fmt='%.6f')


def export_blade_cross_sections(pt, output_dir=".", num_sections=5):
    """Export 2D cross-section profiles at specified radial locations.
    
    Parameters
    ----------
    pt : dict
        Propeller/turbine data structure with 'geometry' dict
    output_dir : str, optional
        Output directory. Default is current directory.
    num_sections : int, optional
        Number of radial sections to export. Default is 5.
    
    Returns
    -------
    section_files : list of str
        List of exported CSV files (one per section)
    
    Notes
    -----
    Each section is saved as a separate CSV file with X, Y coordinates
    suitable for importing as a sketch profile in CAD software.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    geom = pt.get('geometry', {})
    if 'X3D' not in geom:
        raise ValueError("Geometry data not found. Run Geometry(pt) first.")
    
    X3D = geom['X3D']
    Y3D = geom['Y3D']
    Z3D = geom['Z3D']
    RG = geom['RG']
    
    Mp = X3D.shape[0] - 1
    filename_base = pt.get('filename', 'propeller')
    
    section_files = []
    section_indices = np.linspace(0, Mp, num_sections, dtype=int)
    
    for idx in section_indices:
        r_over_R = RG[idx]
        
        # Extract 2D profile (X, Y in local 2D coordinate system)
        x_profile = X3D[idx, :]
        y_profile = Z3D[idx, :]  # Z is the "up" direction in 2D view
        
        # Save to CSV
        section_file = os.path.join(
            output_dir, 
            f"{filename_base}_section_r{r_over_R:.3f}.csv"
        )
        
        profile = np.column_stack([x_profile, y_profile])
        np.savetxt(section_file, profile, delimiter=',', 
                   header=f'X,Y (r/R = {r_over_R:.4f})', 
                   comments='', fmt='%.6f')
        
        section_files.append(section_file)
        print(f"✓ Exported section r/R={r_over_R:.3f}: {section_file}")
    
    return section_files


# Example usage
if __name__ == "__main__":
    print("Blade Geometry Export Module")
    print("=" * 50)
    print("\nUsage:")
    print("  from export_blade import export_blade_geometry")
    print("  pt = run_design()  # Your design workflow")
    print("  files = export_blade_geometry(pt, output_dir='output')")
    print("\nSupported formats:")
    print("  - STEP (.step) - Requires: pip install OCP")
    print("  - STL  (.stl)  - Requires: pip install numpy-stl")
    print("  - CSV  (.csv)  - Built-in (no dependencies)")