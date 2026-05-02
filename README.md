# PythonProp

A Python-based propeller design tool with an easy-to-use graphical interface.

## What is PythonProp?

PythonProp is a propeller design software that helps you create and analyze marine propellers and ducted thrusters. It features:

- **Easy-to-use GUI** - No coding required
- **Interactive design** - See results in real-time
- **3D visualization** - View your propeller design
- **Performance analysis** - Optimize for efficiency
- **Export geometry** - Generate files for manufacturing

Perfect for marine engineers, students, and ROV/AUV designers.

## Installation

### Step 1: Install Python

Download and install Python 3.7 or newer from [python.org](https://www.python.org/downloads/)

During installation, **check the box** "Add Python to PATH"

### Step 2: Install Required Packages

Open a terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:
  pip install numpy matplotlib customtkinter scipy

### Step 3: Download PythonProp

Download or clone this repository to your computer.

## Running the GUI

1. Open a terminal/command prompt

2. Navigate to the PythonProp folder:
  cd path/to/PythonProp/Python/Examples/Ducted_Prop

3. Run the GUI:
   python Ducted_Prop_GUI.py

   
## Quick Start Guide

### Basic Usage

1. **Launch the GUI** - Run `python Ducted_Prop_GUI.py`

2. **Set Your Parameters**:
   - Number of Blades: 4
   - Speed (RPM): 9000
   - Diameter: 0.100 (meters)
   - Thrust: 900 (Newtons)
   - Ship Velocity: 4.5 (m/s)

3. **Customize Blade Data** (Optional):
   - Click "📊 Edit Blade 2-D Section Data"
   - Adjust chord and thickness distributions
   - Double-click any cell to edit

4. **Run Design**:
   - Click "▶ Run Design"
   - Wait for optimization to complete
   - View results in the tabs

5. **Review Results**:
   - **Design Graphs**: See velocity and circulation distributions
   - **3D View**: Visualize your propeller
   - **Performance**: Check efficiency curves
   - **Console**: Read design summary

### Output Files

After running a design, you'll find:
- `OpenProp_Geometry.txt` - Complete geometry data
- Ready for CAD import or further analysis

## Simple Example

**Small ROV Thruster (100mm diameter):**
- Blades: 4
- RPM: 9000
- Diameter: 0.100 m
- Thrust: 900 N
- Velocity: 4.5 m/s
- Include Duct: ✓ Yes

**Result:** ~70% efficiency, 900N thrust at 4.5 m/s

## Troubleshooting

### "No module named 'customtkinter'"
  pip install customtkinter

  
### "Python is not recognized"
Reinstall Python and check "Add Python to PATH"

### GUI won't open
Make sure you're in the correct folder:
cd Python/Examples/Ducted_Prop


### Optimization fails
- Check that all parameters are positive numbers
- Ensure diameter > hub diameter
- Try reducing "Vortex Panels" to 15

## Support

For issues or questions, open an issue on GitHub.

## License
GNU GPL V3.0

This project is a Python port of OpenProp. See original project at [MIT OpenProp](http://engineering.dartmouth.edu/openprop/)
