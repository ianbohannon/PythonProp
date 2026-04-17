# Dependencies

This example is a Python port of Edited_Ducted_Propeller.

## Python Modules

- [ ] elliptic12
- [ ] LLPanelRadii
- [ ] Wrench
- [ ] Horseshoe110628
- [ ] Horseshoe_intr_110830
- [ ] Duct_Influence
- [ ] Duct_Thrust
- [ ] Forces
- [ ] CLCD_vs_ALPHA
- [ ] Find_dCLCDdALPHA
- [ ] GeometryFoil2D
- [ ] InterpolateChord
- [ ] RepairSpline
- [ ] EppsOptimizer
- [ ] Geometry
- [ ] Analyze
- [ ] Make_Reports

## Notes

- **Wrench**: No direct MATLAB source found; this module provides a convenience
  wrapper that assembles thrust and torque wrench quantities from optimizer
  outputs.
- **RepairSpline**: No MATLAB source found; implemented as a passthrough that
  returns the input spline data unchanged (identity/no-op stub).
