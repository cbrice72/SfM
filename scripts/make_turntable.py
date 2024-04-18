#!/usr/bin/env python3

###############################################################################
# @file   make_turntable.py
# @brief  Creates a turntable-like GIF of a 3D model (.ply).
#
# @author brice.c.aa
# @date   2024/4/15
###############################################################################

'''
Usage:
  ./make_turntable.py -i <input_file>

Flags and Options:
  -h, --help                      Displays this help text.
  -i, --in=PATH        [REQUIRED] 3D model (in .ply format) to make a turntable GIF of.
  -s, --silent                    Disable INFO-level logging.
'''

import betterprint  # local module
import getopt
import open3d as o3d
import os
import shutil
import sys
from PIL import Image
from time import sleep


# Keep track of visualization angle across callback instances
angle = 0


def usage():
    """
    Prints the usage information for this script and exits.
    """
    # Print usage
    print(sys.exit(__doc__))


def parse_args(argv):
    """
    Parses and validates input arguments for this script.
    """
    # Default args
    input_file = ''
    silent = False

    # Parse input args according to the options' short and long forms
    opts, _ = getopt.getopt(argv, 'hi:s', ['help', 'in=', 'silent'])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Input - Images Dir
        elif opt in ('-i', '--in'):
            input_file = os.path.abspath(arg)
            if not os.path.exists(input_file):
                betterprint.err(f'Invalid input filepath: {input_file}')
                sys.exit()
            elif not input_file.endswith('.ply'):
                betterprint.err(f'''Invalid input file type: {
                                os.path.splitext(input_file)[1]} (expected .ply)''')
                sys.exit()

        # Preserve turntable frames
        elif opt in ('-s', '--silent'):
            silent = True

    # Check for required args (getopt has no concept of "mandatory" options)
    if not input_file:
        usage()

    return input_file, silent


def main(input_file, silent=True):
    # Read input point cloud (.ply) using Open3D
    if not silent:
        betterprint.info('Reading input file...')

    pcd = o3d.io.read_point_cloud(input_file)

    # Remove as much empty space around the geometry as possible
    if not silent:
        betterprint.info('Focusing model...')

    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False)
    vis.add_geometry(pcd)
    vis.get_view_control().set_zoom(0.4)

    # Generate a frame for every rotation
    if not silent:
        betterprint.info('Generating frames...')

    frames_dir = f'{os.path.dirname(input_file)}/turntable-frames'
    if os.path.exists(frames_dir):
        # Start fresh so the resulting GIF isn't contaminated
        shutil.rmtree(frames_dir)

    os.makedirs(frames_dir)

    ctr = vis.get_view_control()
    # see https://stackoverflow.com/questions/62065410/what-is-the-argument-type-for-get-view-control-rotate-in-open3d
    o3d_pix_per_deg = 5.8178
    o3d_rotation_val = 1.0 * o3d_pix_per_deg  # rotate 1 deg per frame

    for angle in range(0, 360, 1):
        # Rotate and update the visualization
        ctr.rotate(o3d_rotation_val, 0.0)
        vis.update_geometry(pcd)
        vis.poll_events()
        vis.update_renderer()
        # Save a capture
        vis.capture_screen_image(f'{frames_dir}/{angle:03d}.png', True)

    vis.destroy_window()

    # Generate the animation (.gif) itself
    if not silent:
        betterprint.info('Compiling animation...')

    images = [Image.open(os.path.join(frames_dir, f))
              for f in os.listdir(frames_dir) if f.endswith('.png')]
    images[0].save(f'{os.path.dirname(input_file)}/visualization_3D-turntable.gif',
                   format='GIF', append_images=images[1:], save_all=True, duration=25, loop=0)

    # Cleanup
    if not silent:
        betterprint.info('Cleaning up...')

    shutil.rmtree(frames_dir)

    if not silent:
        betterprint.info('Done!')


if __name__ == '__main__':
    i, s = parse_args(sys.argv[1:])
    main(i, s)
