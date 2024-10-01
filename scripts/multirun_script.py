#!/usr/bin/env python3

###############################################################################
# @file   multirun_script.py
# @brief  Run a given Python script multiple times with fixed or iterative variables.
#
# @author brice.c.aa
# @date   2024/10/1
###############################################################################

import betterprint  # local module
import subprocess
import sys
from pathlib import Path

class Shortcut:
    def __init__(self, s, fa, ia, iv):
        self.script_name = s
        self.fixed_args = fa
        self.iter_args = ia
        self.iter_vals = iv

shortcuts = {
    "2024-10-1 Videos": Shortcut(
        "combine_frames.py",
        {},
        ["-i"],
        [
            ["/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/baseline/color/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/baseline/depth/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/darkness/color/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/darkness/depth/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-90/color/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-90/depth/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-45/color/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-45/depth/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-0/color/extracted",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-0/depth/extracted"
            ]
        ]),
    "2024-10-1 SfM": Shortcut(
        "hloc_sfm.py",
        {"--use-defaults": ""},
        ["-i"],
        [
            ["/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/baseline/color/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/baseline/depth/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/darkness/color/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/darkness/depth/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-90/color/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-90/depth/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-45/color/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-45/depth/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-0/color/images",
            "/mnt/c/Users/brice/Desktop/Projects/LIBRA/Archive/2024-10-01_RealSense_Indirect_Lighting_Experiment/light-0/depth/images"
            ]
        ])
}

def multirun_script(script_name, fixed_args, iter_args, iter_vals):
    """
    Args:
        script_name: The full name of the Python script to be run.
        fixed_args: Dictionary of args (keys) and their respective values (values, optional) that will stay constant every run.
        iter_args: List of args whose values will change every run.
        iter_vals: List of lists of values (corresponding to iter_args) that will change every run.
    """
    # Validate script
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        betterprint.err(f"Script '{script_name}' not found in current directory!")
        return
    
    # Validate iterative arguments (ensure lists have same length)
    if len(iter_args) is not len(iter_vals):
        betterprint.err("Inconsistent number of iterative args and values!")
        return
    
    if len(set(map(len,iter_vals))) != 1:
        betterprint.err("Inconsistent length of iterative value lists!")
        return
    
    # NOTE: On the use of zip():
    #       For ease of use, an element of `iterative_arguments` corresponds to
    #       a "row" of `iterative_values`. Because of this relationship, we have
    #       to transpose `iter_vals` in the for loop so that the `iter_arg`
    #       matches up with its corresponding `iter_val`.

    betterprint.info(f"Multirunning {script_name} {len(iter_vals[0])} times")

    # Loop over args in order
    for iter_val in zip(*iter_vals):
        cmd = [sys.executable, str(script_path)]
        
        # Add fixed arguments
        for arg, value in fixed_args.items():
            cmd.extend([arg, str(value)])
        
        # Add iterative arguments
        for arg, value in zip(iter_args, iter_val):
            cmd.extend([arg, str(value)])

        # Run script
        with betterprint.status(f"Running: {' '.join(cmd)}"):
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                if result.stdout:
                    betterprint.info(f"Process finished: {result.stdout}")
                else:
                    betterprint.info(f"Process finished")
            except subprocess.CalledProcessError as e:
                betterprint.err(f"Process returned error: {e}\n{e.stderr}")

    betterprint.info("Finished!")

if __name__ == '__main__':
    sel = shortcuts["2024-10-1 Videos"]
    multirun_script(sel.script_name, sel.fixed_args, sel.iter_args, sel.iter_vals)
