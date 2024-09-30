#!/usr/bin/env python3

###############################################################################
# @file   combine_frames.py
# @brief  Combine sequential frames into a video.
#
# @author brice.c.aa
# @date   2024/9/30
###############################################################################

'''
Usage:
  ./combine_frames.py -i <images_dir>

Flags and Options:
  -h, --help                      Displays this help text.
  -i, --in=PATH        [REQUIRED] Directory containing input images.
'''

import betterprint  # local module
import cv2
import getopt
import os
from pathlib import Path
import sys


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

    # Parse input args according to the options' short and long forms
    opts, _ = getopt.getopt(argv, 'hi:', ['help', 'in='])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Images Directory
        elif opt in ('-i', '--in'):
            image_dir = Path(arg)
            if not image_dir.exists():
                betterprint.err(f'Invalid input filepath: {image_dir}')
                sys.exit()

    # Check for required args (getopt has no concept of "mandatory" options)
    if not image_dir:
        usage()

    # Default to saving the video in the parent directory
    project_dir = os.path.dirname(image_dir)
    output_path = os.path.join(
        project_dir, f"{os.path.basename(image_dir)}_combined.mp4")

    return image_dir, output_path


def main(input_folder, output_video):
    # Retrieve all images from input folder
    images = [img for img in os.listdir(
        input_folder) if img.endswith((".png", ".jpg", ".jpeg"))]
    images.sort()

    # Validation
    if not images:
        betterprint.err(f"No images found in {input_folder}")
        return

    betterprint.info(f'Reading {input_folder}...')

    # Get frame size from first image
    first_frame = cv2.imread(os.path.join(input_folder, images[0]))
    height, width, _ = first_frame.shape

    # Initialize video writer and combine images
    video_writer = cv2.VideoWriter(
        # assume 30 fps
        output_video, cv2.VideoWriter_fourcc(*'mp4v'), 30, (width, height))

    with betterprint.status(f'Combining {len(images)} frames'):
        for image in images:
            frame = cv2.imread(os.path.join(input_folder, image))
            video_writer.write(frame)

    # Clean up
    video_writer.release()

    betterprint.info(f"Finished! Saved video to {output_video}")


if __name__ == "__main__":
    i, o = parse_args(sys.argv[1:])
    main(i, o)
