#!/usr/bin/env python3

###############################################################################
# @file   sample_frames.py
# @brief  Sample images in a directory at a set interval.
#         This is essentially the same logic as `extract_frames.py`, except
#         it works with images that have already been extracted from a rosbag.
#
# @author brice.c.aa
# @date   2024/10/1
###############################################################################

'''
Usage:
  ./sample_frames.py -i <images_dir> -n <interval>

Flags and Options:
  -h, --help                      Displays this help text.
  -i, --images=PATH    [REQUIRED] Directory containing input images.
  -n, --interval=INT   [REQUIRED] Number of images to skip before saving another one.
  -s, --simplify                  Simplify the directory structure by skipping "n{interval}/".
'''

import betterprint  # local module
import getopt
import os
from pathlib import Path
import shutil
import sys
import time

def usage():
    """
    Prints the usage information for this script and exits.
    """
    print(sys.exit(__doc__))


def parse_args(argv):
    """
    Parses and validates input arguments for this script.
    """
    # Default args
    image_dir = ''
    interval = 0
    simplify = False

    # Parse input args according to the options' short and long forms
    opts, _ = getopt.getopt(argv, 'hi:n:s', ['help', 'images=', 'interval=', 'simplify'])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Images Directory
        elif opt in ('-i', '--images'):
            image_dir = Path(arg)
            if not image_dir.exists():
                betterprint.err(f'Invalid input filepath: {image_dir}')
                sys.exit()
        
        # Interval
        elif opt in ('-n', '--interval'):
            try:
                interval = int(arg)
                if interval <= 0:
                    betterprint.err(f'Interval must be greater than 0: {interval}')
                    sys.exit()
            except ValueError:
                betterprint.err(f'Invalid interval: {interval}')
                sys.exit()

        # Simplify Directory Structure
        elif opt in ('-s', '--simplify'):
            simplify = True

    # Check for required args (getopt has no concept of "mandatory" options)
    if not image_dir or not interval:
        usage()

    return image_dir, interval, simplify


def sample_frames(img_dir, interval, simplify):
    # Get all image files (PNG, JPG) from input dir
    images = [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if len(images) == 0:
        betterprint.err(f"No images found in {img_dir}")
        return

    images.sort()  # just in case

    # Initialize project directory
    betterprint.info('Preparing output directory...')

    if simplify:
        out_path = os.path.join(os.path.dirname(img_dir), 'images')
    else:
        out_path = os.path.join(os.path.dirname(img_dir), 'n' + str(interval), 'images')

    if os.path.exists(out_path):
        while True:
            pick = betterprint.ask(
                'This directory\'s images seem to have already been sampled; overwrite? [y/n]').lower()
            if pick == 'y':
                # Clear project directory
                shutil.rmtree(out_path)
                break
            elif pick == 'n':
                # Avoid overwriting files if user rejects prompt
                betterprint.info('Exiting: user refused overwrite!')
                return

    os.makedirs(out_path)
    betterprint.info('Output dir: ' + out_path)

    # Loop over images, only saving every n-th one
    count = 0
    reduced = round(len(images) / interval)

    t_start = time.time()  # log start time

    with betterprint.status(f'Sampling {reduced} frames...'):
        for i, image in enumerate(images):
            # Sample every n-th image
            if i % n == 0:
                src_path = os.path.join(img_dir, image)
                _, ext = os.path.splitext(image)
                # NOTE: this output directory structure mirrors that of `extract_frames.py` 
                dest_path = os.path.join(out_path, f'{count}{ext}')

                # Copy and rename image to output dir
                shutil.copy(src_path, dest_path)

            # Make sure the count is relative to the original order
            count += 1

    betterprint.info(f'Processed {count} frames (saved {reduced} @ n={interval}) in {time.time() - t_start:.2f} s!')

if __name__ == "__main__":
    i, n, s = parse_args(sys.argv[1:])
    sample_frames(i, n, s)
