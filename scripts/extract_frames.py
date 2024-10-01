#!/usr/bin/env python3

###############################################################################
# @file   extract_frames.py
# @brief  Extract frames from a video at a certain interval.
#
# @author brice.c.aa
# @date   2024/4/15
###############################################################################

'''
Usage:
  ./extract_frames.py -i <input_file>

Flags and Options:
  -h, --help                   Displays this help text.
  -i, --in=PATH     [REQUIRED] Video file to extract frames from.
  -o, --out=PATH               Project directory in which to place folder with extracted frames.
                                 (default: same directory as video file)
  -n, --interval=INT           Number of frames to skip before saving another one.
                                 (default: video framerate)
'''

import betterprint  # custom stdout/stderr text formatting
import cv2          # video handling
import getopt       # command-line option parsing
import os           # path management, directory creation
import shutil       # clearing output folder
import sys          # retrieving input args, exiting script
import time         # measuring runtime


def usage():
    """
    Prints the usage information for this script and exits.
    """
    print(sys.exit(__doc__))


def parse_args(argv):
    """
    Parses and validates the input arguments.
    """
    vid_path = ''
    proj_dir = ''
    interval = 0

    # Parse input args according to the options' short and long forms
    opts, _ = getopt.getopt(
        argv, 'hi:o:n:', ['help', 'in=', 'out=', 'interval='])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Input File
        elif opt in ('-i', '--in'):
            vid_path = arg
            if not os.path.isfile(vid_path):
                betterprint.err(f'Invalid input filepath: {vid_path}')
                sys.exit()

        # Project Directory (for output)
        elif opt in ('-o', '--out'):
            proj_dir = os.path.abspath(arg)

        # Frame Interval
        elif opt in ('-n', '--interval'):
            if arg.isnumeric():
                if int(arg) < 1:
                    betterprint.warn(
                        f'Invalid interval (must be positive): {arg}; setting to 1...')
                    interval = 1
                else:
                    interval = int(arg)
            else:
                betterprint.err(
                    f'Invalid interval (must be an integer): {arg}')
                sys.exit()

    # Check for required args (getopt has no concept of "mandatory" options)
    if not vid_path:
        usage()

    # Set optional args, if necessary
    if not proj_dir:
        # By default, use video directory as project root directory
        proj_dir = os.path.dirname(vid_path)

    return vid_path, proj_dir, interval


def extract_frames(vid_path, proj_dir, interval):
    """
    Makes a clean directory based on the video filename
    and sequentially extracts video frames to it
    """
    # Read video
    vid = cv2.VideoCapture(vid_path)
    interval = round(vid.get(cv2.CAP_PROP_FPS)
                     ) if interval == 0 else interval

    # Initialize project directory
    betterprint.info('Preparing output directory...')
    out_path = os.path.join(proj_dir, 'n' + str(interval), 'images')
    if os.path.exists(out_path):
        while True:
            pick = betterprint.ask(
                'This video\'s frames seem to have already been extracted; overwrite? [y/n]').lower()
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

    # Extract frames
    frame_count = 0
    frame_total = round(vid.get(cv2.CAP_PROP_FRAME_COUNT) / interval)

    t_start = time.time()  # log start time

    with betterprint.status(f'Attempting to extract {frame_total} frames...'):
        while True:
            # Attempt to read next frame
            ret, frame = vid.read()
            if not ret:
                # No frames remaining
                break

            # Save every n-th frame to project directory
            if frame_count % interval == 0:
                frame_path = os.path.join(out_path, str(frame_count) + '.jpg')
                cv2.imwrite(frame_path, frame)

            # Increment counter
            frame_count += 1

    t_end = time.time()  # log end time

    # Cleanup
    print()  # newline after 'Progress' output
    vid.release()
    cv2.destroyAllWindows()

    betterprint.info(
        f'Processed {frame_count} frames (saved {frame_total} @ n={interval}) in {t_end - t_start:.2f} s!')


if __name__ == '__main__':
    v, p, n = parse_args(sys.argv[1:])
    extract_frames(v, p, n)
