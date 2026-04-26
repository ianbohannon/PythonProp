"""
Surgical patch for EppsOptimizer.py to fix numerical stability issues.

Run this script to fix division-by-zero errors in duct calculations.
"""

def patch_optimizer():
    """Patch EppsOptimizer.py with numerical stability fixes."""
    
    with open('EppsOptimizer.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Track if we've made changes
    changes_made = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Fix 1: Initial DAHIF/DRHIF division (around line 383)
        if 'for m in range(Mp):' in line and i < len(lines) - 2:
            next1 = lines[i+1] if i+1 < len(lines) else ''
            next2 = lines[i+2] if i+2 < len(lines) else ''
            
            if 'DAHIF[:, m] = DAHIF_times_TANBIC[:, m] / TANBIC[m]' in next1:
                # Found the pattern - replace these 3 lines
                indent = ' ' * (len(line) - len(line.lstrip()))
                new_lines = [
                    line,  # keep the for loop line
                    f'{indent}    # Safeguard against division by very small TANBIC\n',
                    f'{indent}    if abs(TANBIC[m]) < 1e-10:\n',
                    f'{indent}        DAHIF[:, m] = 0.0\n',
                    f'{indent}        DRHIF[:, m] = 0.0\n',
                    f'{indent}    else:\n',
                    f'{indent}        DAHIF[:, m] = DAHIF_times_TANBIC[:, m] / TANBIC[m]\n',
                    f'{indent}        DRHIF[:, m] = DRHIF_times_TANBIC[:, m] / TANBIC[m]\n',
                ]
                lines[i:i+3] = new_lines
                changes_made += 1
                i += len(new_lines)
                continue
            
            # Fix 2: Iteration loop DAHIF/DRHIF division (around line 610)
            if 'DAHIF[:, m] = DAHIF_times_TANBIC[:, m] / TANBICsmooth[m]' in next1:
                # Found the pattern - replace these 3 lines
                indent = ' ' * (len(line) - len(line.lstrip()))
                new_lines = [
                    line,  # keep the for loop line
                    f'{indent}    # Safeguard against division by very small TANBICsmooth\n',
                    f'{indent}    if abs(TANBICsmooth[m]) < 1e-10:\n',
                    f'{indent}        DAHIF[:, m] = 0.0\n',
                    f'{indent}        DRHIF[:, m] = 0.0\n',
                    f'{indent}    else:\n',
                    f'{indent}        DAHIF[:, m] = DAHIF_times_TANBIC[:, m] / TANBICsmooth[m]\n',
                    f'{indent}        DRHIF[:, m] = DRHIF_times_TANBIC[:, m] / TANBICsmooth[m]\n',
                ]
                lines[i:i+3] = new_lines
                changes_made += 1
                i += len(new_lines)
                continue
        
        i += 1
    
    if changes_made > 0:
        # Write back the patched file
        with open('EppsOptimizer.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✓ EppsOptimizer.py patched successfully! ({changes_made} fixes applied)")
        return True
    else:
        print("✗ No patterns found to patch. File may already be patched or structure has changed.")
        return False


if __name__ == '__main__':
    patch_optimizer()