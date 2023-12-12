#!/usr/bin/env python3

import cv2
import getopt
import os
import shutil
import sys
import time


def print_helptext():
    """
    Prints the usage explanation for this script.
    """
    print("""
Usage:
  ./extract_frames.py -i <input_file> -o [output_dir]

Flags and Options:
  -h, --help                   Displays this help text.
  -i, --in=PATH     [REQUIRED] Video file to extract frames from.
  -o, --out=PATH               Directory in which to place folder with extracted frames.
                                 (default: [video_dir]/frames/[video_name]/)
""")


def main(argv):
    """
    Makes a clean directory based on the video filename
    and sequentially extracts video frames to it
    """
    # Variables set via input args
    vid_path = ''
    proj_dir = ''

    # Parse input args
    if len(argv) == 0:
        print_helptext()
        sys.exit()

    opts, _ = getopt.getopt(argv, 'hi:', ['help', 'in='])
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            print_helptext()
            sys.exit()
        # Input File
        elif opt in ('-i', '--in'):
            vid_path = arg
            if not os.path.isfile(vid_path):
                print('Invalid input filepath: ' + vid_path)
                sys.exit()
        # Project Directory (for output)
        elif opt in ('-o', '--out'):
            proj_dir = arg
            if not os.path.isdir(proj_dir):
                print('Invalid output directory: ' + proj_dir)
                sys.exit()

    print('Preparing output directory...')

    # By default, use video directory as project root directory
    if not proj_dir:
        proj_dir = os.path.dirname(vid_path)

    # Initialize project directory
    out_path = os.path.join(
        proj_dir, 'frames', os.path.basename(vid_path).split('.')[0])
    if os.path.exists(out_path):
        while True:
            pick = input(
                '  > This video\'s frames seem to have already been extracted; overwrite? [y/n]  ').lower()
            if pick == 'y':
                # Clear project directory
                shutil.rmtree(out_path)
                break
            elif pick == 'n':
                # Avoid overwriting files if user rejects prompt
                print('  Exiting: user refused overwrite!')
                sys.exit()

    os.makedirs(out_path)
    print('  Output dir: ' + os.path.abspath(out_path))

    print('Extracting frames...')

    # Read video
    vid = cv2.VideoCapture(vid_path)

    frame_count = 0
    frame_total = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
    t_start = time.time()  # log start time
    while True:
        # Attempt to read next frame
        ret, frame = vid.read()
        if not ret:
            # No frames remaining
            break

        # Save frame to project directory
        frame_path = os.path.join(out_path, str(frame_count) + '.jpg')
        cv2.imwrite(frame_path, frame)

        # Output progress
        print('\r  Progress [%d%%]' %
              round((float(frame_count) / float(frame_total)) * 100), end="")

        # Increment counter
        frame_count += 1

    t_end = time.time()  # log end time

    # Cleanup
    print()  # newline after 'Progress' output
    vid.release()
    cv2.destroyAllWindows()

    print('Processed %d frames in %d s!' % (frame_count, t_end - t_start))


if __name__ == '__main__':
    main(sys.argv[1:])
