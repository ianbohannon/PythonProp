"""
Simplified GUI for Ducted Propeller Design Tool
All flags controlled by checkboxes and all graphs displayed in the GUI
Includes blade section plots and 3D visualization
"""

import sys
import os
import numpy as np
import threading
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

# Add SourceCode to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "..", "SourceCode")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from EppsOptimizer import EppsOptimizer
from Geometry import Geometry
from Analyze import Analyze
from InterpolateChord import InterpolateChord

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BladeDataEditor(ctk.CTkToplevel):
    """Window for editing blade 2D section properties matrix data"""
    
    def __init__(self, parent, data_dict):
        super().__init__(parent)
        
        self.title("Blade 2-D Section Properties Editor")
        self.geometry("1400x600")  # CHANGED: Wider to accommodate more columns
        
        # Store reference to parent and data
        self.parent = parent
        self.data = data_dict.copy()
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.populate_table()
        
    def create_ui(self):
        """Create the editor UI"""
        # Instructions
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # CHANGED: Updated description to include new columns
        info_label = ctk.CTkLabel(
            info_frame, 
            text="Edit blade radial distributions. Each row represents a radial station.\n"
                 "XR: r/R, XCoD: c/D, t0oc: t/c, XCD: Drag Coeff, XVA: Va/Vs, XVT: Vt/Vs, skew0: Skew [deg], rake0: Rake/D",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        info_label.pack(pady=5, padx=10)
        
        # Button frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        add_row_btn = ctk.CTkButton(button_frame, text="➕ Add Row", 
                                    command=self.add_row, width=100)
        add_row_btn.pack(side="left", padx=5)
        
        remove_row_btn = ctk.CTkButton(button_frame, text="➖ Remove Row", 
                                       command=self.remove_row, width=100,
                                       fg_color="#dc2626", hover_color="#991b1b")
        remove_row_btn.pack(side="left", padx=5)
        
        reset_btn = ctk.CTkButton(button_frame, text="🔄 Reset to Defaults", 
                                 command=self.reset_defaults, width=150,
                                 fg_color="#ea580c", hover_color="#c2410c")
        reset_btn.pack(side="left", padx=5)
        
        # Table frame with scrollbar
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        tree_scroll_y.pack(side="right", fill="y")
        
        tree_scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")
        
        # CHANGED: Added new columns for XVA, XVT, skew0, rake0
        columns = ("Index", "XR (r/R)", "XCoD (c/D)", "t0oc (t/c)", "XCD",
                   "XVA (Va/Vs)", "XVT (Vt/Vs)", "skew0 [deg]", "rake0 (rake/D)")
        
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode="browse"
        )
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("Index", text="Index")
        self.tree.heading("XR (r/R)", text="XR (r/R)")
        self.tree.heading("XCoD (c/D)", text="XCoD (c/D)")
        self.tree.heading("t0oc (t/c)", text="t0oc (t/c)")
        self.tree.heading("XCD", text="XCD")
        self.tree.heading("XVA (Va/Vs)", text="XVA (Va/Vs)")      # NEW
        self.tree.heading("XVT (Vt/Vs)", text="XVT (Vt/Vs)")      # NEW
        self.tree.heading("skew0 [deg]", text="skew0 [deg]")      # NEW
        self.tree.heading("rake0 (rake/D)", text="rake0 (rake/D)")  # NEW
        
        self.tree.column("Index", width=50, anchor="center")
        self.tree.column("XR (r/R)", width=100, anchor="center")
        self.tree.column("XCoD (c/D)", width=100, anchor="center")
        self.tree.column("t0oc (t/c)", width=100, anchor="center")
        self.tree.column("XCD", width=100, anchor="center")
        self.tree.column("XVA (Va/Vs)", width=100, anchor="center")      # NEW
        self.tree.column("XVT (Vt/Vs)", width=100, anchor="center")      # NEW
        self.tree.column("skew0 [deg]", width=100, anchor="center")      # NEW
        self.tree.column("rake0 (rake/D)", width=120, anchor="center")    # NEW
        
        self.tree.pack(fill="both", expand=True)
        
        # Bind double-click to edit
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Apply and Cancel buttons
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        cancel_btn = ctk.CTkButton(action_frame, text="Cancel", 
                                   command=self.cancel, width=120,
                                   fg_color="#6b7280", hover_color="#4b5563")
        cancel_btn.pack(side="right", padx=5)
        
        apply_btn = ctk.CTkButton(action_frame, text="Apply", 
                                 command=self.apply_changes, width=120,
                                 fg_color="#10b981", hover_color="#059669")
        apply_btn.pack(side="right", padx=5)
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background="#2b2b2b",
                       foreground="white",
                       fieldbackground="#2b2b2b",
                       borderwidth=0,
                       font=("Consolas", 9))  # CHANGED: Smaller font
        style.configure("Treeview.Heading",
                       background="#1f538d",
                       foreground="white",
                       borderwidth=1,
                       font=("Arial", 9, "bold"))  # CHANGED: Smaller font
        style.map("Treeview",
                 background=[("selected", "#1f538d")])
        
    def populate_table(self):
        """Populate table with current data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # CHANGED: Get all arrays including new ones
        XR = self.data['XR']
        XCoD = self.data['XCoD']
        t0oc = self.data['t0oc']
        XCD = self.data['XCD']
        XVA = self.data['XVA']      # NEW
        XVT = self.data['XVT']      # NEW
        skew0 = self.data['skew0']  # NEW
        rake0 = self.data['rake0']  # NEW
        
        # CHANGED: Add rows with all columns
        for i in range(len(XR)):
            self.tree.insert("", "end", values=(
                i,
                f"{XR[i]:.4f}",
                f"{XCoD[i]:.4f}",
                f"{t0oc[i]:.4f}",
                f"{XCD[i]:.6f}",
                f"{XVA[i]:.4f}",      # NEW
                f"{XVT[i]:.4f}",      # NEW
                f"{skew0[i]:.4f}",    # NEW
                f"{rake0[i]:.6f}"     # NEW
            ))
    
    def on_double_click(self, event):
        """Handle double-click to edit cell"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        
        if not row_id:
            return
        
        # Get column index (0-based, but column is 1-based string like '#1')
        col_idx = int(column.replace('#', '')) - 1
        
        # Don't allow editing the index column
        if col_idx == 0:
            return
        
        # Get current value
        values = self.tree.item(row_id, 'values')
        current_value = values[col_idx]
        
        # Get cell position
        x, y, width, height = self.tree.bbox(row_id, column)
        
        # Create entry widget for editing
        entry = tk.Entry(self.tree, font=("Consolas", 9))  # CHANGED: Smaller font
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.focus()
        
        def save_edit(event=None):
            new_value = entry.get()
            try:
                # Validate numeric input
                float(new_value)
                # Update tree
                new_values = list(values)
                new_values[col_idx] = new_value
                self.tree.item(row_id, values=new_values)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number")
            entry.destroy()
        
        def cancel_edit(event=None):
            entry.destroy()
        
        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    
    def add_row(self):
        """Add a new row to the table"""
        # CHANGED: Get current data including new arrays
        XR = self.data['XR'].tolist()
        XCoD = self.data['XCoD'].tolist()
        t0oc = self.data['t0oc'].tolist()
        XCD = self.data['XCD'].tolist()
        XVA = self.data['XVA'].tolist()      # NEW
        XVT = self.data['XVT'].tolist()      # NEW
        skew0 = self.data['skew0'].tolist()  # NEW
        rake0 = self.data['rake0'].tolist()  # NEW
        
        # Add default values
        if len(XR) > 0:
            new_xr = min(1.0, XR[-1] + 0.05)
        else:
            new_xr = 0.5
        
        XR.append(new_xr)
        XCoD.append(0.15)
        t0oc.append(0.05)
        XCD.append(0.008)
        XVA.append(1.0)       # NEW: Default uniform inflow
        XVT.append(0.0)       # NEW: Default no tangential inflow
        skew0.append(0.0)     # NEW: Default no skew
        rake0.append(0.0)     # NEW: Default no rake
        
        # CHANGED: Update data including new arrays
        self.data['XR'] = np.array(XR)
        self.data['XCoD'] = np.array(XCoD)
        self.data['t0oc'] = np.array(t0oc)
        self.data['XCD'] = np.array(XCD)
        self.data['XVA'] = np.array(XVA)      # NEW
        self.data['XVT'] = np.array(XVT)      # NEW
        self.data['skew0'] = np.array(skew0)  # NEW
        self.data['rake0'] = np.array(rake0)  # NEW
        
        # Refresh table
        self.populate_table()
    
    def remove_row(self):
        """Remove selected row from table"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a row to remove")
            return
        
        if len(self.data['XR']) <= 2:
            messagebox.showwarning("Cannot Remove", "Must have at least 2 data points")
            return
        
        # Get selected index
        values = self.tree.item(selected[0], 'values')
        idx = int(values[0])
        
        # CHANGED: Remove from all arrays including new ones
        self.data['XR'] = np.delete(self.data['XR'], idx)
        self.data['XCoD'] = np.delete(self.data['XCoD'], idx)
        self.data['t0oc'] = np.delete(self.data['t0oc'], idx)
        self.data['XCD'] = np.delete(self.data['XCD'], idx)
        self.data['XVA'] = np.delete(self.data['XVA'], idx)      # NEW
        self.data['XVT'] = np.delete(self.data['XVT'], idx)      # NEW
        self.data['skew0'] = np.delete(self.data['skew0'], idx)  # NEW
        self.data['rake0'] = np.delete(self.data['rake0'], idx)  # NEW
        
        # Refresh table
        self.populate_table()
    
    def reset_defaults(self):
        """Reset to default values"""
        if messagebox.askyesno("Reset", "Reset to default values?"):
            self.data['XR'] = np.array([0.15, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0])
            self.data['XCoD'] = np.array([0.1600, 0.1818, 0.2024, 0.2196, 0.2305, 0.2311, 
                                         0.2173, 0.1806, 0.1387, 0.0010])
            self.data['t0oc'] = np.array([0.2056, 0.1551, 0.1181, 0.0902, 0.0694, 0.0541, 
                                         0.0419, 0.0332, 0.0324, 0.0000])
            self.data['XCD'] = np.ones(10) * 0.008
            self.data['XVA'] = np.ones(10)      # NEW: Default uniform inflow
            self.data['XVT'] = np.zeros(10)     # NEW: Default no tangential inflow
            self.data['skew0'] = np.zeros(10)   # NEW: Default no skew
            self.data['rake0'] = np.zeros(10)   # NEW: Default no rake
            self.populate_table()
    
    def apply_changes(self):
        """Apply changes and close window"""
        try:
            # CHANGED: Extract data from tree including new columns
            XR_list = []
            XCoD_list = []
            t0oc_list = []
            XCD_list = []
            XVA_list = []      # NEW
            XVT_list = []      # NEW
            skew0_list = []    # NEW
            rake0_list = []    # NEW
            
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                XR_list.append(float(values[1]))
                XCoD_list.append(float(values[2]))
                t0oc_list.append(float(values[3]))
                XCD_list.append(float(values[4]))
                XVA_list.append(float(values[5]))      # NEW
                XVT_list.append(float(values[6]))      # NEW
                skew0_list.append(float(values[7]))    # NEW
                rake0_list.append(float(values[8]))    # NEW
            
            # Validate data
            if len(XR_list) < 2:
                messagebox.showerror("Error", "Must have at least 2 data points")
                return
            
            # Check XR is monotonically increasing
            for i in range(1, len(XR_list)):
                if XR_list[i] <= XR_list[i-1]:
                    messagebox.showerror("Error", "XR values must be monotonically increasing")
                    return
            
            # CHANGED: Update data including new arrays
            self.data['XR'] = np.array(XR_list)
            self.data['XCoD'] = np.array(XCoD_list)
            self.data['t0oc'] = np.array(t0oc_list)
            self.data['XCD'] = np.array(XCD_list)
            self.data['XVA'] = np.array(XVA_list)      # NEW
            self.data['XVT'] = np.array(XVT_list)      # NEW
            self.data['skew0'] = np.array(skew0_list)  # NEW
            self.data['rake0'] = np.array(rake0_list)  # NEW
            
            # Update parent's blade data
            self.parent.blade_data = self.data.copy()
            
            messagebox.showinfo("Success", f"Blade data updated with {len(XR_list)} stations")
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid data: {e}")
    
    def cancel(self):
        """Cancel and close window"""
        self.destroy()


class CollapsibleSection(ctk.CTkFrame):
    """A collapsible section widget"""
    
    def __init__(self, parent, title, start_collapsed=False):
        super().__init__(parent, fg_color="transparent")
        
        self.is_collapsed = start_collapsed
        
        # Header button
        self.header = ctk.CTkButton(
            self,
            text=f"{'▶' if start_collapsed else '▼'} {title}",
            command=self.toggle,
            fg_color="#1f538d",
            hover_color="#14375e",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.header.pack(fill="x", padx=5, pady=(10, 0))
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        if not start_collapsed:
            self.content_frame.pack(fill="x", padx=0, pady=0)
        
        self.title = title
    
    def toggle(self):
        """Toggle the collapsed state"""
        if self.is_collapsed:
            self.content_frame.pack(fill="x", padx=0, pady=0)
            self.header.configure(text=f"▼ {self.title}")
            self.is_collapsed = False
        else:
            self.content_frame.pack_forget()
            self.header.configure(text=f"▶ {self.title}")
            self.is_collapsed = True
    
    def get_content_frame(self):
        """Get the frame where content should be added"""
        return self.content_frame


class DuctedPropGUI(ctk.CTk):
    """Simplified GUI with checkboxes for flags and all graphs displayed"""
    
    def __init__(self):
        super().__init__()
        
        self.title("PythonProp - Ducted Propeller Design")
        self.geometry("1800x950")
        
        # Initialize data
        self.pt = None
        self.current_filename = None
        
        # Create menu bar
        self.create_menu_bar()
        
        # CHANGED: Initialize blade data with defaults including new parameters
        self.blade_data = {
            'XR': np.array([0.15, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]),
            'XCoD': np.array([0.1600, 0.1818, 0.2024, 0.2196, 0.2305, 0.2311, 
                            0.2173, 0.1806, 0.1387, 0.0010]),
            't0oc': np.array([0.2056, 0.1551, 0.1181, 0.0902, 0.0694, 0.0541, 
                            0.0419, 0.0332, 0.0324, 0.0000]),
            'XCD': np.ones(10) * 0.008,
            'XVA': np.ones(10),      # NEW: Va/Vs = 1.0 (uniform axial inflow)
            'XVT': np.zeros(10),     # NEW: Vt/Vs = 0.0 (no tangential inflow)
            'skew0': np.zeros(10),   # NEW: skew = 0 degrees (no sweep)
            'rake0': np.zeros(10)    # NEW: rake = 0 (no axial offset)
        }
        
        # Store references to canvases and figures for proper cleanup
        self.design_canvas = None
        self.blade_canvas = None
        self.view3d_canvas = None
        self.performance_canvas = None
        self.design_figure = None
        self.blade_figure = None
        self.view3d_figure = None
        self.performance_figure = None
        
        # Bind close event for cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create UI
        self.create_input_panel()
        self.create_display_panel()
        self.create_menu_bar()
    
    def on_closing(self):
        """Clean up matplotlib figures and canvases before closing"""
        try:
            # Stop and clean up all canvases
            for canvas in [self.design_canvas, self.blade_canvas, 
                          self.view3d_canvas, self.performance_canvas]:
                if canvas is not None:
                    try:
                        # Cancel any pending draw events
                        if hasattr(canvas, '_idle_draw_id') and canvas._idle_draw_id:
                            try:
                                canvas.get_tk_widget().after_cancel(canvas._idle_draw_id)
                            except:
                                pass
                        canvas.flush_events()
                    except:
                        pass
            
            # Close all matplotlib figures
            for fig in [self.design_figure, self.blade_figure,
                       self.view3d_figure, self.performance_figure]:
                if fig is not None:
                    try:
                        plt.close(fig)
                    except:
                        pass
            # Close any remaining figures
            plt.close('all')
            
        except Exception as e:
            print(f"Cleanup error: {e}")
        finally:
            # Destroy the window
            self.destroy()
    
    def open_blade_data_editor(self):
        """Open the blade data editor window"""
        editor = BladeDataEditor(self, self.blade_data)
    
    def create_input_panel(self):
        """Create left input panel"""
        input_frame = ctk.CTkScrollableFrame(self, width=350)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(input_frame, text="🚢 Design Parameters", 
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # Basic Parameters - Collapsible
        basic_section = CollapsibleSection(input_frame, "Basic Parameters", start_collapsed=False)
        basic_section.pack(fill="x", padx=0, pady=5)
        basic_content = basic_section.get_content_frame()
        
        self.Z = self.add_input(basic_content, "Number of Blades", "4")
        self.N = self.add_input(basic_content, "Speed (RPM)", "9000")
        self.D = self.add_input(basic_content, "Diameter (m)", "0.100")
        self.THRUST = self.add_input(basic_content, "Thrust (N)", "900")
        self.Vs = self.add_input(basic_content, "Flow Speed (m/s)", "4.5")
        
        # Hub Parameters - Collapsible
        hub_section = CollapsibleSection(input_frame, "Hub Parameters", start_collapsed=False)
        hub_section.pack(fill="x", padx=0, pady=5)
        hub_content = hub_section.get_content_frame()
        
        self.Hub_flag = self.add_checkbox(hub_content, "Include Hub", True)
        self.Dhub = self.add_input(hub_content, "Hub Diameter (m)", "0.015")
        self.HUF = self.add_input(hub_content, "Hub Unloading", "0")
        self.Rhv = self.add_input(hub_content, "Hub Vortex Radius", "0.5")
        
        # Duct Parameters - Collapsible
        duct_section = CollapsibleSection(input_frame, "Duct Parameters", start_collapsed=False)
        duct_section.pack(fill="x", padx=0, pady=5)
        duct_content = duct_section.get_content_frame()
        
        self.Duct_flag = self.add_checkbox(duct_content, "Include Duct", True)
        self.TAU = self.add_input(duct_content, "Thrust Ratio (τ)", "0.9")
        self.Rduct_offset = self.add_input(duct_content, "Blade to Duct Gap (m)", "0.002")
        self.Cduct_mult = self.add_input(duct_content, "Chord Multiplier", "1.0")
        self.CDd = self.add_input(duct_content, "Drag Coefficient", "0.008")
        
        # Section Properties - Collapsible
        section_section = CollapsibleSection(input_frame, "Section Properties", start_collapsed=False)
        section_section.pack(fill="x", padx=0, pady=5)
        section_content = section_section.get_content_frame()
        
        self.Meanline = self.add_dropdown(section_content, "Meanline", 
                                         ["NACA a=0.8", "Parabolic"],
                                         "NACA a=0.8")
        self.Thickness = self.add_dropdown(section_content, "Thickness Form", 
                                          ["NACA 65A010", "Elliptical", "Parabolic"],
                                          "Elliptical")
        
        # Blade 2-D Data button
        blade_data_btn = ctk.CTkButton(
            section_content, 
            text="📊 Edit Blade 2-D Section Data",
            command=self.open_blade_data_editor,
            fg_color="#059669",
            hover_color="#047857"
        )
        blade_data_btn.pack(pady=5, padx=15, fill="x")
        
        # Computational Parameters - Collapsible
        computational_section = CollapsibleSection(input_frame, "Computational", start_collapsed=False)
        computational_section.pack(fill="x", padx=0, pady=5)
        computational_content = computational_section.get_content_frame()
        
        self.Mp = self.add_input(computational_content, "Vortex Panels", "20")
        self.Np = self.add_input(computational_content, "Chord Points", "20")
        self.rho = self.add_input(computational_content, "Density (kg/m³)", "1025")
        self.TUF = self.add_input(computational_content, "Tip Unloading", "0")
        
        # Design Flags - Collapsible
        flags_section = CollapsibleSection(input_frame, "Design Flags", start_collapsed=False)
        flags_section.pack(fill="x", padx=0, pady=5)
        flags_content = flags_section.get_content_frame()
        
        self.Propeller_flag = self.add_checkbox(flags_content, "Propeller Mode", True)
        self.Viscous_flag = self.add_checkbox(flags_content, "Viscous Forces", True)
        self.Chord_flag = self.add_checkbox(flags_content, "Optimize Chord", False)
        
        # Run Button
        self.run_btn = ctk.CTkButton(input_frame, text="▶ Run Design", 
                                     command=self.run_design,
                                     height=50, font=ctk.CTkFont(size=16, weight="bold"))
        self.run_btn.pack(pady=20, padx=10, fill="x")
        
        # Progress
        self.progress = ctk.CTkProgressBar(input_frame)
        self.progress.pack(pady=5, padx=10, fill="x")
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(input_frame, text="Ready")
        self.status_label.pack(pady=5)
    
    def create_display_panel(self):
        """Create right display panel with all graphs"""
        display_frame = ctk.CTkFrame(self)
        display_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)
        
        # Tab view for different graph sets
        self.tabs = ctk.CTkTabview(display_frame)
        self.tabs.grid(row=0, column=0, sticky="nsew")
        
        # Create tabs
        self.tabs.add("Design Graphs")
        self.tabs.add("Blade Sections")
        self.tabs.add("3D View")
        self.tabs.add("Performance")
        self.tabs.add("Console")
        
        # Console
        console_frame = self.tabs.tab("Console")
        self.console = ctk.CTkTextbox(console_frame, font=ctk.CTkFont(family="Consolas"))
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log("Ready to run design optimization...")
    
    def create_section(self, parent, title):
        """Create a section header"""
        label = ctk.CTkLabel(parent, text=title, 
                            font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(pady=(15, 5), padx=5, anchor="w")
    
    def add_input(self, parent, label, default):
        """Add input field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        
        lbl = ctk.CTkLabel(frame, text=label, width=140, anchor="w")
        lbl.pack(side="left")
        
        entry = ctk.CTkEntry(frame, width=100)
        entry.insert(0, default)
        entry.pack(side="right")
        
        return entry
    
    def add_dropdown(self, parent, label, options, default):
        """Add dropdown (combobox) field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        
        lbl = ctk.CTkLabel(frame, text=label, width=140, anchor="w")
        lbl.pack(side="left")
        
        dropdown = ctk.CTkComboBox(frame, values=options, width=100, state="readonly")
        dropdown.set(default)
        dropdown.pack(side="right")
        
        return dropdown
    
    def add_checkbox(self, parent, label, default):
        """Add checkbox"""
        checkbox = ctk.CTkCheckBox(parent, text=label)
        checkbox.pack(pady=3, padx=15, anchor="w")
        if default:
            checkbox.select()
        return checkbox
    
    def log(self, message):
        """Log to console"""
        self.console.insert("end", message + "\n")
        self.console.see("end")
        self.update_idletasks()
    
    def get_inputs(self):
        """Get all input values"""
        try:
            Z = int(self.Z.get())
            N = float(self.N.get())
            D = float(self.D.get())
            THRUST = float(self.THRUST.get())
            Vs = float(self.Vs.get())
            Dhub = float(self.Dhub.get())
            
            n = N / 60
            R = D / 2
            Rhub = Dhub / 2
            Js = Vs / (n * D)
            L = np.pi / Js
            CTDES = THRUST / (0.5 * float(self.rho.get()) * Vs**2 * np.pi * R**2)
            
            # CHANGED: Use blade data from editor INCLUDING new parameters
            XR = self.blade_data['XR']
            XCoD = self.blade_data['XCoD']
            t0oc = self.blade_data['t0oc']
            XCD = self.blade_data['XCD']
            XVA = self.blade_data['XVA']      # NEW
            XVT = self.blade_data['XVT']      # NEW
            skew0 = self.blade_data['skew0']  # NEW
            rake0 = self.blade_data['rake0']  # NEW
            
            # Map meanline dropdown to string name
            meanline_map = {
                "NACA a=0.8": "NACA a=0.8",
                "Parabolic": "parabolic"
            }
            meanline_value = meanline_map.get(self.Meanline.get(), "NACA a=0.8")
            
            # Map thickness dropdown to string name
            thickness_map = {
                "NACA 65A010": "NACA 65A010",
                "Elliptical": "elliptic",
                "Parabolic": "parabolic"
            }
            thickness_value = thickness_map.get(self.Thickness.get(), "elliptic")
            
            Rduct = D / 2 + float(self.Rduct_offset.get())
            Cduct = D * float(self.Cduct_mult.get())
            
            # CHANGED: Include new parameters in input dictionary
            inp = {
                "Z": Z, "N": N, "D": D, "Vs": Vs, "Js": Js, "L": L, "CTDES": CTDES,
                "Mp": int(self.Mp.get()), "Np": int(self.Np.get()),
                "R": R, "Rhub": Rhub, "Rhub_oR": Rhub/R,
                "XR": XR, "XVA": XVA, "XVT": XVT, "XCD": XCD, "XCoD": XCoD,
                "t0oc0": t0oc,
                "skew0": skew0, "rake0": rake0,  # NEW: Now passed to optimizer/geometry
                "Meanline": meanline_value,
                "Thickness": thickness_value,
                "dCLdALPHA": 2*np.pi,
                "Propeller_flag": self.Propeller_flag.get(),
                "Viscous_flag": self.Viscous_flag.get(),
                "Hub_flag": self.Hub_flag.get(),
                "Duct_flag": self.Duct_flag.get(),
                "Plot_flag": 0,
                "Chord_flag": self.Chord_flag.get(),
                "TAU": float(self.TAU.get()),
                "Rduct": Rduct,
                "Cduct": Cduct,
                "CDd": float(self.CDd.get()),
                "rho": float(self.rho.get()),
                "HUF": float(self.HUF.get()),
                "TUF": float(self.TUF.get()),
                "Rhv": float(self.Rhv.get()),
            }
            return inp
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            return None
    
    def clear_all_graphs(self):
        """Clear all existing graphs before running new calculation"""
        try:
            # Clear design graphs
            if self.design_canvas is not None:
                try:
                    widget = self.design_canvas.get_tk_widget()
                    widget.pack_forget()
                    widget.destroy()
                except:
                    pass
                self.design_canvas = None
            if self.design_figure is not None:
                try:
                    plt.close(self.design_figure)
                except:
                    pass
                self.design_figure = None
            
            # Clear blade sections
            if self.blade_canvas is not None:
                try:
                    widget = self.blade_canvas.get_tk_widget()
                    widget.pack_forget()
                    widget.destroy()
                except:
                    pass
                self.blade_canvas = None
            if self.blade_figure is not None:
                try:
                    plt.close(self.blade_figure)
                except:
                    pass
                self.blade_figure = None
            
            # Clear 3D view
            if self.view3d_canvas is not None:
                try:
                    widget = self.view3d_canvas.get_tk_widget()
                    widget.pack_forget()
                    widget.destroy()
                except:
                    pass
                self.view3d_canvas = None
            if self.view3d_figure is not None:
                try:
                    plt.close(self.view3d_figure)
                except:
                    pass
                self.view3d_figure = None
            
            # Clear performance graphs
            if self.performance_canvas is not None:
                try:
                    widget = self.performance_canvas.get_tk_widget()
                    widget.pack_forget()
                    widget.destroy()
                except:
                    pass
                self.performance_canvas = None
            if self.performance_figure is not None:
                try:
                    plt.close(self.performance_figure)
                except:
                    pass
                self.performance_figure = None
            
            # Force update
            self.update_idletasks()
                
        except Exception as e:
            print(f"Error clearing graphs: {e}")
    
    def run_design(self):
        """Run design in background thread"""
        self.run_btn.configure(state="disabled")
        self.progress.set(0)
        self.status_label.configure(text="Running...")
        self.console.delete("1.0", "end")
        
        # Clear previous results and graphs
        self.pt = None
        self.clear_all_graphs()
        
        inp = self.get_inputs()
        if inp is None:
            self.run_btn.configure(state="normal")
            return
        
        thread = threading.Thread(target=self._run_design_thread, args=(inp,))
        thread.daemon = True
        thread.start()
    
    def _run_design_thread(self, inp):
        """Background design execution"""
        try:
            self.log("=" * 60)
            self.log("Starting Design Optimization")
            self.log("=" * 60)
            self.log(f"Js = {inp['Js']:.4f}, L = {inp['L']:.4f}, CTDES = {inp['CTDES']:.4f}")
            
            self.pt = {"input": inp}
            
            # Run optimizer
            self.after(0, lambda: self.progress.set(0.2))
            self.log("\nRunning EppsOptimizer...")
            self.pt["design"] = EppsOptimizer(inp)
            self.log("✓ Optimization complete")
            
            # Generate geometry - switch to non-interactive backend to avoid threading issues
            self.after(0, lambda: self.progress.set(0.5))
            self.log("\nGenerating geometry...")
            
            # Enable text file output
            self.pt['input']['Make_GeoText_flag'] = 1
            if 'filename' not in self.pt['input']:
                self.pt['input']['filename'] = 'PythonProp'
            
            # Save current backend and switch to Agg (non-interactive)
            current_backend = matplotlib.get_backend()
            matplotlib.use('Agg', force=True)
            
            try:
                self.pt["geometry"] = Geometry(self.pt)
                self.log("✓ Geometry complete")
                self.log(f"✓ Geometry file written: {self.pt['input']['filename']}_Geometry.txt")
            finally:
                # Restore original backend
                matplotlib.use(current_backend, force=True)
            
            # Run analysis
            self.after(0, lambda: self.progress.set(0.7))
            self.log("\nRunning off-design analysis...")
            
            # Calculate design point Js (this corresponds to the input RPM - maximum RPM)
            Js_design = inp['Js']
            
            # Create Js range starting from design point (max RPM) up to higher Js (lower RPM)
            # Since RPM = Vs/(Js*D)*60, lower Js = higher RPM
            # We want design point to be the MINIMUM Js (MAXIMUM RPM)
            Js_min = Js_design  # Design point is the minimum Js (maximum RPM)
            Js_max = min(1.00, Js_design + 0.5)  # Go to higher Js values (lower RPMs)
            
            # Create range starting from design point
            Js_range = np.arange(Js_min, Js_max + 0.05, 0.05)
            
            LAMBDAall = np.pi / Js_range
            self.pt["states"] = Analyze(self.pt, LAMBDAall)
            self.log("✓ Analysis complete")
            
            self.after(0, lambda: self.progress.set(1.0))
            self.log("\n" + "=" * 60)
            self.log("Design Complete!")
            self.log("=" * 60)
            
            # Display results
            self.after(0, self.display_all_graphs)
            
        except Exception as e:
            import traceback
            self.log(f"\nERROR: {str(e)}")
            self.log(traceback.format_exc())
        
        finally:
            self.after(0, lambda: self.run_btn.configure(state="normal"))
            self.after(0, lambda: self.status_label.configure(text="Complete"))
    
    def display_all_graphs(self):
        """Display all graphs in the GUI"""
        if self.pt is None:
            return
        
        try:
            # Clear and recreate all graph tabs
            self.log("\n📊 Generating visualizations...")
            
            # Design graphs
            self.log("  - Design graphs...")
            self.create_design_graphs()
            
            # Blade section plots
            self.log("  - Blade sections...")
            self.create_blade_sections()
            
            # 3D view
            self.log("  - 3D view...")
            self.create_3d_view()
            
            # Performance graphs
            self.log("  - Performance curves...")
            self.create_performance_graphs()
            
            self.log("✓ All visualizations complete\n")
            
            # Switch to design graphs tab
            self.tabs.set("Design Graphs")
            
        except Exception as e:
            import traceback
            self.log(f"\n❌ Error creating graphs: {str(e)}")
            self.log(traceback.format_exc())
    
    def create_design_graphs(self):
        """Create all design graphs"""
        if self.pt is None or 'design' not in self.pt:
            return
        
        design = self.pt["design"]
        inp = self.pt["input"]
        
        # Get the frame
        design_frame = self.tabs.tab("Design Graphs")
        
        # Destroy old canvas and figure if they exist
        if self.design_canvas is not None:
            try:
                widget = self.design_canvas.get_tk_widget()
                widget.pack_forget()
                widget.destroy()
            except:
                pass
            self.design_canvas = None
        if self.design_figure is not None:
            try:
                plt.close(self.design_figure)
            except:
                pass
            self.design_figure = None
        
        # Force update
        design_frame.update_idletasks()
        
        # Create NEW figure with 6 subplots (3x2 grid)
        self.design_figure = Figure(figsize=(14, 10), facecolor='#2b2b2b')
        fig = self.design_figure
        
        # 1. Circulation Distribution
        ax1 = fig.add_subplot(3, 2, 1)
        ax1.plot(design['RC'], design['G'], 'cyan', linewidth=2)
        ax1.set_xlabel('r/R', color='white')
        ax1.set_ylabel('Γ / (2πRVs)', color='white')
        ax1.set_title('Circulation Distribution', color='white', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        self.style_axis(ax1)
        
        # 2. Velocity Distributions
        ax2 = fig.add_subplot(3, 2, 2)
        ax2.plot(design['RC'], design['VAC'], '-', color='#3b82f6', linewidth=2, label='Va/Vs')
        ax2.plot(design['RC'], design['VTC'], '--', color='#3b82f6', linewidth=2, label='Vt/Vs')
        ax2.plot(design['RC'], design['UASTAR'], '-.', color='#ef4444', linewidth=2, label='Ua*/Vs')
        ax2.plot(design['RC'], design['UTSTAR'], ':', color='#ef4444', linewidth=2, label='Ut*/Vs')
        ax2.set_xlabel('r/R', color='white')
        ax2.set_ylabel('Velocity', color='white')
        ax2.set_title('Velocity Distributions', color='white', fontweight='bold')
        ax2.legend(facecolor='#1e1e1e', edgecolor='white', labelcolor='white')
        ax2.grid(True, alpha=0.3)
        self.style_axis(ax2)
        
        # 3. Flow Angles
        ax3 = fig.add_subplot(3, 2, 3)
        Beta_c = np.degrees(np.arctan(design['TANBC']))
        BetaI_c = np.degrees(np.arctan(design['TANBIC']))
        ax3.plot(design['RC'], Beta_c, '--', color='#3b82f6', linewidth=2, label='β')
        ax3.plot(design['RC'], BetaI_c, '-', color='#ef4444', linewidth=2, label='βI')
        ax3.set_xlabel('r/R', color='white')
        ax3.set_ylabel('Angle (deg)', color='white')
        ax3.set_title('Flow Angles', color='white', fontweight='bold')
        ax3.legend(facecolor='#1e1e1e', edgecolor='white', labelcolor='white')
        ax3.grid(True, alpha=0.3)
        self.style_axis(ax3)
        
        # 4. Chord Distribution
        ax4 = fig.add_subplot(3, 2, 4)
        Rhub_oR = inp['Rhub_oR']
        XXRC = Rhub_oR + (1 - Rhub_oR) * np.sin(np.arange(61) * np.pi / (2 * 60))
        XXCoD = InterpolateChord(design['RC'], design['CoD'], XXRC)
        ax4.plot(XXRC, XXCoD, color='#10b981', linewidth=2)
        ax4.plot(XXRC, -XXCoD, color='#10b981', linewidth=2)
        ax4.plot(design['RC'], design['CoD'], 'o', color='yellow', markersize=6)
        ax4.plot(design['RC'], -design['CoD'], 'o', color='yellow', markersize=6)
        ax4.set_xlabel('r/R', color='white')
        ax4.set_ylabel('c/D', color='white')
        ax4.set_title('Chord Distribution', color='white', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        self.style_axis(ax4)
        
        # 5. Design Parameters Table (Bottom Left)
        ax5 = fig.add_subplot(3, 2, 5)
        ax5.axis('tight')
        ax5.axis('off')
        ax5.set_title('Design Parameters', color='white', fontweight='bold', pad=10)

        # Calculate Torque and Power using formulas from Forces.m
        n = inp['N'] / 60  # Convert RPM to rev/s
        rho = inp['rho']
        D = inp['D']
        R = inp['R']
        Vs = inp['Vs']
        if 'CQ' in design and 'CP' in design:
            # From Forces.m: Q = CQ * 0.5 * rho * Vs^2 * pi * R^3
            Q = design['CQ'] * 0.5 * rho * (Vs**2) * np.pi * (R**3)  # Torque in Nm
            # From Forces.m: P = CP * 0.5 * rho * Vs^3 * pi * R^2
            P = design['CP'] * 0.5 * rho * (Vs**3) * np.pi * (R**2)  # Power in W
        else:
            Q = 0
            P = 0

        # Create table data with only requested parameters
        table_data = [
            ['Parameter', 'Value', 'Unit'],
            ['Advance Coeff (Js)', f"{inp['Js']:.4f}", ''],
            ['Torque', f"{Q:.3f}", 'Nm'],
            ['Power', f"{P:.2f}", 'W'],
            ['Thrust Ratio (τ)', f"{inp['TAU']:.3f}", ''],
        ]

        # Create the table
        table = ax5.table(cellText=table_data, cellLoc='left', loc='center',
                         colWidths=[0.5, 0.3, 0.2])
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.8)
        
        # Color header row
        for i in range(3):
            cell = table[(0, i)]
            cell.set_facecolor('#1f538d')
            cell.set_text_props(weight='bold', color='white')
        
        # Color data rows
        for i in range(1, len(table_data)):
            for j in range(3):
                cell = table[(i, j)]
                cell.set_facecolor('#1e1e1e')
                cell.set_text_props(color='white')
                cell.set_edgecolor('gray')
        
        # 6. Performance Summary (Bottom Right)
        ax6 = fig.add_subplot(3, 2, 6)
        ax6.axis('tight')
        ax6.axis('off')
        ax6.set_title('Performance Summary', color='white', fontweight='bold', pad=10)

        if 'EFFY' in design:
            # Create table data with parameter names and values
            table_data = [
                ['Parameter', 'Value'],
                ['Js - Advance Coefficient', f"{inp['Js']:.4f}"],
                ['KT - Thrust Coefficient', f"{design.get('KT', 0):.4f}"],
                ['KQ - Torque Coefficient', f"{design.get('KQ', 0):.4f}"],
                ['CT - Thrust Coefficient', f"{design['CT']:.4f}"],
                ['EFFY - Overall Efficiency', f"{design['EFFY']:.4f}"],
                ['ADEFFY - Actuator Disk Efficiency', f"{design.get('ADEFFY', 0):.4f}"],
                ['QF - Quality Factor', f"{design.get('QF', 0):.4f}"],
            ]
            
            # Create the table
            table = ax6.table(cellText=table_data, cellLoc='left', loc='center',
                             colWidths=[0.7, 0.3])
            
            # Style the table
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.8)
            
            # Color header row
            for i in range(2):
                cell = table[(0, i)]
                cell.set_facecolor('#1f538d')
                cell.set_text_props(weight='bold', color='white')
            
            # Color data rows
            for i in range(1, len(table_data)):
                for j in range(2):
                    cell = table[(i, j)]
                    cell.set_facecolor('#1e1e1e')
                    cell.set_text_props(color='white')
                    cell.set_edgecolor('gray')
        
        fig.tight_layout()
        
        # Create NEW canvas and add to GUI
        self.design_canvas = FigureCanvasTkAgg(fig, design_frame)
        self.design_canvas.draw()
        self.design_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_blade_sections(self):
        """Create 2D blade cross-section image at selected radial stations"""
        if self.pt is None or 'geometry' not in self.pt:
            return

        geometry = self.pt['geometry']
        blade_frame = self.tabs.tab("Blade Sections")
        
        # Destroy old canvas and figure
        if self.blade_canvas is not None:
            try:
                widget = self.blade_canvas.get_tk_widget()
                widget.pack_forget()
                widget.destroy()
            except:
                pass
            self.blade_canvas = None
        if self.blade_figure is not None:
            try:
                plt.close(self.blade_figure)
            except:
                pass
            self.blade_figure = None
        
        blade_frame.update_idletasks()

        # Check if required geometry data exists
        if 'x2Dr' not in geometry or 'y2Dr' not in geometry or 'RG' not in geometry:
            # Create placeholder message
            self.blade_figure = Figure(figsize=(14, 10), facecolor='#2b2b2b')
            fig = self.blade_figure
            ax = fig.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, 'Blade section data not available\n(x2Dr, y2Dr not in geometry)', 
                   transform=ax.transAxes, fontsize=14, color='white',
                   verticalalignment='center', horizontalalignment='center',
                   bbox=dict(boxstyle='round', facecolor='#1e1e1e', alpha=0.8))
            ax.axis('off')
            self.blade_canvas = FigureCanvasTkAgg(fig, blade_frame)
            self.blade_canvas.draw()
            self.blade_canvas.get_tk_widget().pack(fill="both", expand=True)
            return

        # Get geometry data
        RG = geometry['RG']
        x2Dr = geometry['x2Dr']
        y2Dr = geometry['y2Dr']
        
        Mp = x2Dr.shape[0] - 1
        Np = x2Dr.shape[1] // 2

        # Create figure
        self.blade_figure = Figure(figsize=(14, 10), facecolor='#2b2b2b')
        fig = self.blade_figure
        ax = fig.add_subplot(1, 1, 1)
        
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, color='gray')
        ax.set_title('2D Blade Image', fontsize=14, color='white', fontweight='bold')
        ax.set_xlabel('X (2D) [m]', fontsize=12, color='white')
        ax.set_ylabel('Y (2D) [m]', fontsize=12, color='white')
        
        # Color cycle for blade sections
        colors = ['r', 'g', 'b', 'm', 'k']
        
        # Plot crosshairs through origin
        x_min, x_max = np.min(x2Dr), np.max(x2Dr)
        y_min, y_max = np.min(y2Dr), np.max(y2Dr)
        ax.plot([x_min, x_max], [0, 0], 'white', linewidth=0.5, alpha=0.5)
        ax.plot([0, 0], [y_min, y_max], 'white', linewidth=0.5, alpha=0.5)
        
        flag = 0
        handle_legend = []
        str_legend = []
        
        # Select sections to plot
        step = max(1, int(np.ceil(Mp / 5)))
        indices = list(range(0, Mp, step))
        
        for i in indices:
            color = colors[flag % len(colors)]
            
            # Plot the blade section outline
            handle = ax.plot(x2Dr[i, :], y2Dr[i, :], color, linewidth=2)[0]
            handle_legend.append(handle)
            
            # Plot thickness line
            x_te = 0.5 * (x2Dr[i, 0] + x2Dr[i, 2*Np - 1])
            y_te = 0.5 * (y2Dr[i, 0] + y2Dr[i, 2*Np - 1])
            x_le = 0.5 * (x2Dr[i, Np - 1] + x2Dr[i, Np])
            y_le = 0.5 * (y2Dr[i, Np - 1] + y2Dr[i, Np])
            
            ax.plot([x_te, x_le], [y_te, y_le], color, linewidth=1)
            
            str_legend.append(f'r/R = {RG[i]:.5g}')
            
            flag += 1
        
        ax.legend(handle_legend, str_legend, loc='upper left', fontsize=10,
                 facecolor='#1e1e1e', edgecolor='white', labelcolor='white')
        
        self.style_axis(ax)
        fig.tight_layout()
        
        # Add to GUI
        self.blade_canvas = FigureCanvasTkAgg(fig, blade_frame)
        self.blade_canvas.draw()
        self.blade_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_3d_view(self):
        """Create 3D propeller view"""
        if self.pt is None or 'geometry' not in self.pt:
            return
        
        geometry = self.pt['geometry']
        inp = self.pt['input']
        view3d_frame = self.tabs.tab("3D View")
        
        # Destroy old canvas and figure
        if self.view3d_canvas is not None:
            try:
                widget = self.view3d_canvas.get_tk_widget()
                widget.pack_forget()
                widget.destroy()
            except:
                pass
            self.view3d_canvas = None
        if self.view3d_figure is not None:
            try:
                plt.close(self.view3d_figure)
            except:
                pass
            self.view3d_figure = None
            
        view3d_frame.update_idletasks()
        
        # Create figure
        self.view3d_figure = Figure(figsize=(14, 10), facecolor='#2b2b2b')
        fig = self.view3d_figure
        ax = fig.add_subplot(111, projection='3d')
        
        # Get 3D geometry data
        if 'X3D' in geometry and 'Y3D' in geometry and 'Z3D' in geometry:
            X3D = geometry['X3D']
            Y3D = geometry['Y3D']
            Z3D = geometry['Z3D']
            Z_blades = geometry['Z'];
            
            for k in range(Z_blades):
                ax.plot_surface(X3D[:, :, k], Y3D[:, :, k], Z3D[:, :, k],
                               color='coral', edgecolor='darkred', 
                               linewidth=0.5, alpha=0.85, shade=True)
            
            # Plot hub
            R = inp['R']
            Rhub = inp['Rhub']
            hub_length = 2.5 * Rhub;
            
            # Cylindrical hub
            theta = np.linspace(0, 2*np.pi, 30)
            x_hub = np.linspace(-hub_length/2, hub_length/2, 20)
            X_hub, Theta_hub = np.meshgrid(x_hub, theta)
            Y_hub = Rhub * np.cos(Theta_hub)
            Z_hub = Rhub * np.sin(Theta_hub)
            
            ax.plot_surface(X_hub, Y_hub, Z_hub, color='gray', alpha=0.7,
                          edgecolor='darkgray', linewidth=0.3)
            
            # Hub caps
            phi = np.linspace(0, np.pi/2, 10)
            Theta_cap, Phi_cap = np.meshgrid(theta, phi)
            
            # Front cap
            X_front = hub_length/2 + Rhub * np.cos(Phi_cap)
            Y_front = Rhub * np.sin(Phi_cap) * np.cos(Theta_cap)
            Z_front = Rhub * np.sin(Phi_cap) * np.sin(Theta_cap)
            ax.plot_surface(X_front, Y_front, Z_front, color='gray', alpha=0.7)
            
            # Back cap
            phi_back = np.linspace(np.pi/2, np.pi, 10)
            Theta_back, Phi_back = np.meshgrid(theta, phi_back)
            X_back = -hub_length/2 + Rhub * np.cos(Phi_back)
            Y_back = Rhub * np.sin(Phi_back) * np.cos(Theta_back)
            Z_back = Rhub * np.sin(Phi_back) * np.sin(Theta_back)
            ax.plot_surface(X_back, Y_back, Z_back, color='gray', alpha=0.7)
            
            # Plot duct if present
            if inp['Duct_flag'] == 1:
                Rduct = inp['Rduct']
                Cduct = inp['Cduct']
                
                # Simplified duct as cylinder
                x_duct = np.linspace(-Cduct/2, Cduct/2, 20)
                X_duct, Theta_duct = np.meshgrid(x_duct, theta)
                Y_duct = Rduct * np.cos(Theta_duct)
                Z_duct = Rduct * np.sin(Theta_duct)
                
                ax.plot_surface(X_duct, Y_duct, Z_duct, color='lightblue', 
                              alpha=0.3, edgecolor='blue', linewidth=0.5)
            
            # Set labels and title
            ax.set_xlabel('X (m)', color='white', fontsize=11)
            ax.set_ylabel('Y (m)', color='white', fontsize=11)
            ax.set_zlabel('Z (m)', color='white', fontsize=11)
            ax.set_title('3D Propeller View', color='white', fontsize=14, fontweight='bold')
            
            # Set equal aspect ratio
            max_range = R * 1.2
            ax.set_xlim([-max_range, max_range])
            ax.set_ylim([-max_range, max_range])
            ax.set_zlim([-max_range, max_range])
            
            # Style 3D axis
            ax.xaxis.pane.fill = False
            ax.yaxis.pane.fill = False
            ax.zaxis.pane.fill = False
            ax.xaxis.pane.set_edgecolor('white')
            ax.yaxis.pane.set_edgecolor('white')
            ax.zaxis.pane.set_edgecolor('white')
            ax.tick_params(colors='white', labelsize=9)
            ax.set_facecolor('#1e1e1e')
            fig.patch.set_facecolor('#2b2b2b')
        
        fig.tight_layout()
        
        # Add to GUI
        self.view3d_canvas = FigureCanvasTkAgg(fig, view3d_frame)
        self.view3d_canvas.draw()
        self.view3d_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_performance_graphs(self):
        """Create performance curve graphs"""
        if self.pt is None or self.pt.get("states") is None:
            return
        
        states = self.pt["states"]
        inp = self.pt["input"]
        perf_tab = self.tabs.tab("Performance")
        
        # Destroy old canvas and figure
        if self.performance_canvas is not None:
            try:
                widget = self.performance_canvas.get_tk_widget()
                widget.pack_forget()
                widget.destroy()
            except:
                pass
            self.performance_canvas = None
        if self.performance_figure is not None:
            try:
                plt.close(self.performance_figure)
            except:
                pass
            self.performance_figure = None
        
        # Destroy old scrollable frame if it exists
        for widget in perf_tab.winfo_children():
            widget.destroy()
        
        # Create scrollable frame for performance tab
        perf_frame = ctk.CTkScrollableFrame(perf_tab)
        perf_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create figure with 4 subplots
        self.performance_figure = Figure(figsize=(14, 16), facecolor='#2b2b2b')
        fig = self.performance_figure
        
        # Calculate RPM and Torque arrays (used in multiple plots)
        rho = inp['rho']
        R = inp['R']
        Vs = inp['Vs']
        D = inp['D']
        
        # Calculate RPM from Js: Js = Vs / (n * D), so n = Vs / (Js * D)
        # RPM = n * 60
        n_array = Vs / (states['Js'] * D)  # revolution per second
        RPM_array = n_array * 60  # RPM
        
        # Calculate torque for each state using KQ
        # KQ = Q / (rho * n^2 * D^5), so Q = KQ * rho * n^2 * D^5
        Torque_array = states['KQ'] * rho * (n_array**2) * (D**5)
        
        # 1. KT, KQ, Efficiency vs Js
        ax1 = fig.add_subplot(4, 1, 1)
        ax1.plot(states['Js'], states['KT'], '.-', color='#3b82f6', 
                linewidth=2.5, markersize=10, label='KT')
        ax1.plot(states['Js'], 10 * states['KQ'], '.-', color='#ef4444', 
                linewidth=2.5, markersize=10, label='10×KQ')
        ax1.plot(states['Js'], states['EFFY'], '.-', color='#10b981', 
                linewidth=2.5, markersize=10, label='Efficiency (η)')
        ax1.set_xlabel('Advance Coefficient (Js)', color='white', fontsize=12)
        ax1.set_ylabel('Coefficients', color='white', fontsize=12)
        ax1.set_title('Off-Design Performance', color='white', fontsize=14, fontweight='bold')
        ax1.legend(facecolor='#1e1e1e', edgecolor='white', labelcolor='white', fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(right=.85)  # Max X-axis
        self.style_axis(ax1)
        
        # 2. CT, CP vs Js
        ax2 = fig.add_subplot(4, 1, 2)
        ax2.plot(states['Js'], states['CT'], '.-', color='cyan', 
                linewidth=2.5, markersize=10, label='CT')
        ax2.plot(states['Js'], states['CP'], '.-', color='magenta', 
                linewidth=2.5, markersize=10, label='CP')
        ax2.set_xlabel('Advance Coefficient (Js)', color='white', fontsize=12)
        ax2.set_ylabel('Coefficients', color='white', fontsize=12)
        ax2.set_title('Thrust and Power Coefficients', color='white', fontsize=14, fontweight='bold')
        ax2.legend(facecolor='#1e1e1e', edgecolor='white', labelcolor='white', fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(right=0.85)  # ADD THIS LINE - Extend X-axis to 0.80
        self.style_axis(ax2)
        
        # 3. Torque vs RPM
        ax3 = fig.add_subplot(4, 1, 3)
        ax3.plot(RPM_array, Torque_array, '.-', color='#f59e0b', 
                linewidth=2.5, markersize=10, label='Torque')
        ax3.set_xlabel('RPM', color='white', fontsize=12)
        ax3.set_ylabel('Torque (Nm)', color='white', fontsize=12)
        ax3.set_title('Torque vs RPM', color='white', fontsize=14, fontweight='bold')
        ax3.legend(facecolor='#1e1e1e', edgecolor='white', labelcolor='white', fontsize=11)
        ax3.grid(True, alpha=0.3)
        self.style_axis(ax3)
        
        # 4. Efficiency vs RPM
        ax4 = fig.add_subplot(4, 1, 4)
        ax4.plot(RPM_array, states['EFFY'], '.-', color='#10b981', 
                linewidth=2.5, markersize=10, label='Efficiency (η)')
        ax4.set_xlabel('RPM', color='white', fontsize=12)
        ax4.set_ylabel('Efficiency', color='white', fontsize=12)
        ax4.set_title('Efficiency vs RPM', color='white', fontsize=14, fontweight='bold')
        ax4.legend(facecolor='#1e1e1e', edgecolor='white', labelcolor='white', fontsize=11)
        ax4.grid(True, alpha=0.3)
        self.style_axis(ax4)
        
        fig.tight_layout()
        
        # Add to GUI
        self.performance_canvas = FigureCanvasTkAgg(fig, perf_frame)
        self.performance_canvas.draw()
        self.performance_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def style_axis(self, ax):
        """Apply dark theme styling to axis"""
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white', labelsize=10)
        for spine in ax.spines.values():
            spine.set_color('white')
    
    def create_menu_bar(self):
        """Create menu bar at the top"""
        menubar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open...", command=self.file_open)
        file_menu.add_command(label="Save", command=self.file_save)
        file_menu.add_command(label="Save As...", command=self.file_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu (empty)
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Help menu (empty)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)

    def get_input_values(self):
        """Get all current input values from the GUI"""
        # CHANGED: Include new blade data parameters in save file
        values = {
            "Z": self.Z.get(),
            "N": self.N.get(),
            "D": self.D.get(),
            "THRUST": self.THRUST.get(),
            "Vs": self.Vs.get(),
            "Hub_flag": self.Hub_flag.get(),
            "Dhub": self.Dhub.get(),
            "HUF": self.HUF.get(),
            "Rhv": self.Rhv.get(),
            "Duct_flag": self.Duct_flag.get(),
            "TAU": self.TAU.get(),
            "Rduct_offset": self.Rduct_offset.get(),
            "Cduct_mult": self.Cduct_mult.get(),
            "CDd": self.CDd.get(),
            "Meanline": self.Meanline.get(),
            "Thickness": self.Thickness.get(),
            "blade_data": {
                "XR": self.blade_data['XR'].tolist(),
                "XCoD": self.blade_data['XCoD'].tolist(),
                "t0oc": self.blade_data['t0oc'].tolist(),
                "XCD": self.blade_data['XCD'].tolist(),
                "XVA": self.blade_data['XVA'].tolist(),      # NEW
                "XVT": self.blade_data['XVT'].tolist(),      # NEW
                "skew0": self.blade_data['skew0'].tolist(),  # NEW
                "rake0": self.blade_data['rake0'].tolist()   # NEW
            },
            "Mp": self.Mp.get(),
            "Np": self.Np.get(),
            "rho": self.rho.get(),
            "TUF": self.TUF.get(),
            "Propeller_flag": self.Propeller_flag.get(),
            "Viscous_flag": self.Viscous_flag.get(),
            "Chord_flag": self.Chord_flag.get()
        }
        return values

    def set_input_values(self, values):
        """Set all input values in the GUI"""
        # Basic parameters
        self.Z.delete(0, 'end')
        self.Z.insert(0, values["Z"])
        self.N.delete(0, 'end')
        self.N.insert(0, values["N"])
        self.D.delete(0, 'end')
        self.D.insert(0, values["D"])
        self.THRUST.delete(0, 'end')
        self.THRUST.insert(0, values["THRUST"])
        self.Vs.delete(0, 'end')
        self.Vs.insert(0, values["Vs"])
        
        # Hub parameters
        if values["Hub_flag"]:
            self.Hub_flag.select()
        else:
            self.Hub_flag.deselect()
        self.Dhub.delete(0, 'end')
        self.Dhub.insert(0, values["Dhub"])
        self.HUF.delete(0, 'end')
        self.HUF.insert(0, values["HUF"])
        self.Rhv.delete(0, 'end')
        self.Rhv.insert(0, values["Rhv"])
        
        # Duct parameters
        if values["Duct_flag"]:
            self.Duct_flag.select()
        else:
            self.Duct_flag.deselect()
        self.TAU.delete(0, 'end')
        self.TAU.insert(0, values["TAU"])
        self.Rduct_offset.delete(0, 'end')
        self.Rduct_offset.insert(0, values["Rduct_offset"])
        self.Cduct_mult.delete(0, 'end')
        self.Cduct_mult.insert(0, values["Cduct_mult"])
        self.CDd.delete(0, 'end')
        self.CDd.insert(0, values["CDd"])
        
        # Section properties
        self.Meanline.set(values["Meanline"])
        self.Thickness.set(values["Thickness"])
        
        # CHANGED: Load blade data including new parameters
        self.blade_data = {
            "XR": np.array(values["blade_data"]["XR"]),
            "XCoD": np.array(values["blade_data"]["XCoD"]),
            "t0oc": np.array(values["blade_data"]["t0oc"]),
            "XCD": np.array(values["blade_data"]["XCD"]),
            "XVA": np.array(values["blade_data"].get("XVA", np.ones(len(values["blade_data"]["XR"])))),    # NEW with fallback
            "XVT": np.array(values["blade_data"].get("XVT", np.zeros(len(values["blade_data"]["XR"])))),   # NEW with fallback
            "skew0": np.array(values["blade_data"].get("skew0", np.zeros(len(values["blade_data"]["XR"])))), # NEW with fallback
            "rake0": np.array(values["blade_data"].get("rake0", np.zeros(len(values["blade_data"]["XR"])))) # NEW with fallback
        }
        
        # Computational parameters
        self.Mp.delete(0, 'end')
        self.Mp.insert(0, values["Mp"])
        self.Np.delete(0, 'end')
        self.Np.insert(0, values["Np"])
        self.rho.delete(0, 'end')
        self.rho.insert(0, values["rho"])
        self.TUF.delete(0, 'end')
        self.TUF.insert(0, values["TUF"])
        
        # Design flags
        if values["Propeller_flag"]:
            self.Propeller_flag.select()
        else:
            self.Propeller_flag.deselect()
        if values["Viscous_flag"]:
            self.Viscous_flag.select()
        else:
            self.Viscous_flag.deselect()
        if values["Chord_flag"]:
            self.Chord_flag.select()
        else:
            self.Chord_flag.deselect()

    def file_open(self):
        """Open an existing design"""
        from tkinter import filedialog
        import json
        
        filename = filedialog.askopenfilename(
            title="Open Design File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json"
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    values = json.load(f)
                self.set_input_values(values)
                self.current_filename = filename
                self.log(f"✓ Loaded design from: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def file_save(self):
        """Save current design"""
        import json
        
        if hasattr(self, 'current_filename') and self.current_filename:
            try:
                values = self.get_input_values()
                with open(self.current_filename, 'w') as f:
                    json.dump(values, f, indent=4)
                self.log(f"✓ Saved design to: {self.current_filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
        else:
            self.file_save_as()

    def file_save_as(self):
        """Save design as new file"""
        from tkinter import filedialog
        import json
        
        filename = filedialog.asksaveasfilename(
            title="Save Design As",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json"
        )
        if filename:
            try:
                values = self.get_input_values()
                with open(filename, 'w') as f:
                    json.dump(values, f, indent=4)
                self.current_filename = filename
                self.log(f"✓ Saved design to: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")


if __name__ == "__main__":
    app = DuctedPropGUI()
    app.mainloop()
