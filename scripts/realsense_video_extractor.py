#!/usr/bin/env python3

###############################################################################
# @file   realsense_video_extractor.py
# @brief  Extracts RGB and depth videos from rosbags created using Intel RealSense D4xx cameras.
#
# @author g2-bernotas
#         (see https://github.com/IntelRealSense/librealsense/issues/2731#issuecomment-529938267)
# @author gycka
#         (see https://github.com/IntelRealSense/librealsense/issues/2731#issuecomment-1130541167)
# @author brice.c.aa
# @date   2024/9/30
###############################################################################

'''
Usage:
  ./realsense_video_extractor.py -i <rosbag>

Flags and Options:
  -h, --help                      Displays this help text.
  -i, --in=PATH        [REQUIRED] Filepath to input rosbag.
'''

import betterprint  # local module
import getopt
import os
from pathlib import Path
import sys

import pyrealsense2 as rs
import numpy as np
import cv2


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
    bag_path = ''

    # Parse input args according to the options' short and long forms
    opts, _ = getopt.getopt(argv, 'hi:', ['help', 'in='])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Rosbag Filepath
        elif opt in ('-i', '--in'):
            bag_path = Path(arg)
            if not bag_path.exists():
                betterprint.err(f'Invalid input filepath: {bag_path}')
                sys.exit()

    # Check for required args (getopt has no concept of "mandatory" options)
    if not bag_path:
        usage()

    return bag_path.absolute().as_posix()


def main(bag_path: str):
    # Configure depth and color streams
    pipeline = rs.pipeline()
    config = rs.config()
    rs.config.enable_device_from_file(config, bag_path)
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

    # Initialize video writers
    bag_name = os.path.basename(bag_path)
    prefix = os.path.splitext(bag_name)[0]
    depth_path = f'outputs/{prefix}_depth.avi'
    color_path = f'outputs/{prefix}_rgb.avi'

    # NOTE: although depth framerate can reach 90 fps, it's limited to 30 fps
    #       since that's what the RGB framerate maxes out at
    depthwriter = cv2.VideoWriter(
        depth_path, cv2.VideoWriter_fourcc(*'XVID'), 30, (1280, 720), 1)
    # depthwriter = cv2.VideoWriter(
    #    depth_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (1280, 720), 1)
    colorwriter = cv2.VideoWriter(
        color_path, cv2.VideoWriter_fourcc(*'XVID'), 30, (1280, 720), 1)
    # colorwriter = cv2.VideoWriter(
    #    color_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (1280, 720), 1)

    # Begin streaming
    profile = pipeline.start(config)
    playback = profile.get_device().as_playback()
    playback.set_real_time(False)

    try:
        # From gycka:
        # "I found it a good idea to skip the first frames of a recording as they aren't always perfect.
        #  I used to skip about 30 frames, but typically in the range 5-45 were unusable."
        count = 0
        for _ in range(30):
            profile.get_device().as_playback().resume()
            frames = pipeline.wait_for_frames()
            profile.get_device().as_playback().pause()
            count = count + 1
        while True:
            # Retrieve frames
            profile.get_device().as_playback().resume()
            frames = pipeline.wait_for_frames()
            profile.get_device().as_playback().pause()
            frames.keep()

            # Only continue if both depth and color frames are valid
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                # We want to keep the resulting videos at the same framerate,
                # so don't save anything if one stream dropped a frame
                continue

            # Convert images to numpy arrays for saving
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(
                depth_image, alpha=0.03), cv2.COLORMAP_JET)

            depthwriter.write(depth_colormap)
            colorwriter.write(color_image)

            # Display stream to user
            cv2.imshow('Stream', depth_colormap)

            # Exit loop only if user presses "q"
            if cv2.waitKey(1) == ord("q"):
                break
    finally:
        # Clean up
        colorwriter.release()
        depthwriter.release()
        pipeline.stop()


if __name__ == '__main__':
    i = parse_args(sys.argv[1:])
    main(i)
