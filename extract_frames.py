#!/usr/bin/env python3

import cv2
import os
import sys
import shutil
import getopt


def print_helptext():
    """
    Prints the usage explanation for this script.
    """
    print("""
Usage:
  ./extract_frames.py -i <input_file_path>

Flags and Options:
  -h, --help       Displays this help text.
  -i, --in=PATH    Video file to extract frames from. (tab-to-autocomplete available)
""")


def main(argv):
    """
    Makes a clean directory based on the video filename
    and sequentially extracts video frames to it
    """
    vid_path = ''

    # Check the input args
    if len(argv) == 0:
        print_helptext()
        sys.exit()

    opts, _ = getopt.getopt(argv, 'hi:', ['help', 'in='])
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_helptext()
            sys.exit()
        elif opt in ('-i', '--in'):
            vid_path = arg
            if not os.path.isfile(vid_path):
                print('Invalid filepath: ' + vid_path)
                sys.exit()

    print('Preparing project directory...')

    # Check filepath validity
    if not os.path.isfile(vid_path):
        print('  Invalid filepath! ' + vid_path)

    # Initialize project directory
    proj_dir = os.path.join('./data', os.path.basename(vid_path).split('.')[0])
    if os.path.exists(proj_dir):
        while True:
            pick = input('  > Overwrite ' + proj_dir + '? [y/n]  ').lower()
            if pick == 'y':
                # Clear project directory
                shutil.rmtree(proj_dir)
                break
            elif pick == 'n':
                # Avoid overwriting files if user rejects prompt
                print('  Exiting: user refused overwrite!')
                sys.exit()

    os.makedirs(proj_dir)

    print('Extracting frames...')

    # Read video
    cam = cv2.VideoCapture(vid_path)

    frame_count = 0
    while True:
        # Attempt to read next frame
        ret, frame = cam.read()
        if not ret:
            # No frames remaining
            break

        # Save frame to project directory
        frame_path = os.path.join(proj_dir, str(frame_count) + '.jpg')
        cv2.imwrite(frame_path, frame)

        # Increment counter
        frame_count += 1

    # Cleanup
    cam.release()
    cv2.destroyAllWindows()

    print('Processed %s frames!' % frame_count)


if __name__ == '__main__':
    main(sys.argv[1:])
