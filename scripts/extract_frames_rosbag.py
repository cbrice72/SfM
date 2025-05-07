#!/usr/bin/env python3

###############################################################################
# @file   extract_frames_rosbag.py
# @brief  Extract all recorded frames from a ROS2-bag.
#
# @author brice.c.aa
# @date   2025/5/7
#
# @note Adapted from Baza's answer in the following Stack Overflow thread:
#       https://stackoverflow.com/questions/76537425/how-to-export-image-and-video-data-from-a-bag-file-in-ros2
###############################################################################

'''
Usage:
  ./extract_frames_rosbag.py -i <input_rosbag> -t <topic_name>

Flags and Options:
  -h, --help                   Displays this help text.
  -i, --in=PATH     [REQUIRED] ROS2-bag to extract frames from.
  -t, --topic=NAME  [REQUIRED] ROS2 topic name to read frames from.
  -o, --out=PATH               Output directory in which to place folder with extracted frames.
                                 (default: "frames_[NAME_OF_ROSBAG]")
  -n, --interval=INT           Number of frames to skip before saving another one.
                                 (default: 30)
  -j, --jobs=INT               Number of parallel processes to use for frame writing.
                                 (default: 1)
'''

import betterprint         # custom stdout/stderr text formatting
import concurrent.futures  # paralell processing
import cv2                 # image frame handling
import getopt              # command-line option parsing
from pathlib import Path   # path management, directory creation
from rosbags.highlevel import AnyReader       # reading rosbags
from rosbags.image import message_to_cvimage  # converting ROS2 topic data to cv2 images
import shutil              # clearing output folder
import sys                 # retrieving input args, exiting script
import time                # measuring runtime


def usage():
    """
    Prints the usage information for this script and exits.
    """
    print(sys.exit(__doc__))


def parse_args(argv):
    """
    Parses and validates the input arguments.
    """
    bag_path = None
    topic_name = ''
    out_dir = None
    interval = 30
    num_jobs = 1

    # Parse input args according to the options' short and long forms
    opts, _ = getopt.getopt(
        argv, 'hi:t:o:n:j:', ['help', 'in=', 'topic=', 'out=', 'interval=', 'jobs='])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Input ROS2-bag
        elif opt in ('-i', '--in'):
            bag_path = Path(arg).resolve()
            if not bag_path.is_dir():
                betterprint.err(f'Invalid input directory: {bag_path}')
                sys.exit()

        # Topic Name
        elif opt in ('-t', '--topic'):
            topic_name = arg
            if not topic_name.isascii():
                betterprint.err(f'Invalid topic name: {topic_name}')
                sys.exit()

        # Project Directory (for output)
        elif opt in ('-o', '--out'):
            out_dir = Path(arg).resolve()

        # Frame Interval
        elif opt in ('-n', '--interval'):
            if arg.isnumeric():
                if int(arg) < 1:
                    betterprint.warn(
                        f'Invalid interval (must be positive): {arg}; using default (30)...')
                else:
                    interval = int(arg)
            else:
                betterprint.err(
                    f'Invalid interval (must be an integer): {arg}')
                sys.exit()
                
        # Number of Multithreading Jobs
        elif opt in ('-j', '--jobs'):
            if arg.isnumeric():
                if int(arg) < 1:
                    betterprint.warn(
                        f'Invalid jobs number (must be positive): {arg}; using default (1)...')
                else:
                    num_jobs = int(arg)
            else:
                betterprint.err(
                    f'Invalid jobs number (must be an integer): {arg}')
                sys.exit()

    # Check for required args (getopt has no concept of "mandatory" options)
    if not bag_path:
        usage()

    if not topic_name:
        betterprint.err(f'Please specify one of the following topics using \'-t\':')
        with AnyReader([bag_path]) as reader:
            # Get topic and msgtype information from .connections list
            for connection in reader.connections:
                print('  ' + connection.topic + ' (Type: ' + connection.msgtype + ')')
        sys.exit()

    # Set optional args, if necessary
    if not out_dir:
        # By default, output directory should be appended with rosbag name
        out_dir = bag_path.parent

    return bag_path, topic_name, out_dir, interval, num_jobs


def process_bag_chunk(bag_path, topic_name, out_dir, interval, chunk_id, start_time, end_time):
    """
    Saves image frames from a rosbag during a specific time chunk.
    """
    frame_count = 0
    saved_count = 0
    
    with AnyReader([bag_path]) as reader:
        # Filter only messages from target topic
        topic_connections = [conn for conn in reader.connections if conn.topic == topic_name]
        if not topic_connections:
            betterprint.err(f'No messages found for topic: {topic_name}')
            return chunk_id, 0, 0
        
        # Process frames within given time range
        for connection, timestamp, rawdata in reader.messages(
                connections=topic_connections,
                start=start_time,
                stop=end_time):
            
            if frame_count % interval == 0:
                msg = reader.deserialize(rawdata, connection.msgtype)
                img = message_to_cvimage(msg)
                output_path = out_dir / f"{chunk_id}_frame{frame_count:06d}.png"
                cv2.imwrite(str(output_path), img)
                saved_count += 1
            
            frame_count += 1
    
    return chunk_id, frame_count, saved_count


def ns_to_mmss(ns):
    """
    Converts nanoseconds to a string in the format "MM:SS".
    """
    total_sec = ns // 1_000_000_000
    min = total_sec // 60
    sec = total_sec % 60
    return f'{int(min):02d}:{int(sec):02d}'


def extract_frames_rosbag(bag_path, topic_name, out_dir, interval, num_jobs):
    """
    Makes a clean directory based on the rosbag filename
    and extracts recorded frames to it using parallel processing.
    """
    # Initialize project directory
    betterprint.info('Preparing output directory...')
    out_dir = out_dir / ('n' + str(interval)) / 'images'
    if out_dir.exists():
        while True:
            pick = betterprint.ask(
                'This rosbag\'s frames seem to have already been extracted; overwrite? [y/n]').lower()
            if pick == 'y':
                # Clear project directory
                shutil.rmtree(out_dir)
                break
            elif pick == 'n':
                # Avoid overwriting files if user rejects prompt
                betterprint.info('Exiting: user refused overwrite!')
                return

    out_dir.mkdir(parents=True, exist_ok=False)
    betterprint.info('Output dir: ' + str(out_dir))

    # Get rosbag duration and calculate chunk boundaries
    with AnyReader([bag_path]) as reader:
        duration = reader.duration  # duration in nanoseconds
        start_time = reader.start_time
        end_time = reader.end_time
    
    betterprint.info(f'Splitting rosbag ({ns_to_mmss(duration)} MM:SS) into {num_jobs} chunks')
    
    # Create time chunks for parallel processing
    chunk_size = duration // num_jobs
    chunks = []
    
    for i in range(num_jobs):
        chunk_start = start_time + (i * chunk_size)
        chunk_end = chunk_start + chunk_size - 1 if i < num_jobs - 1 else end_time
        chunks.append((i, chunk_start, chunk_end))
        print(f'  Chunk #{i}: {ns_to_mmss(chunk_start-start_time)}-{ns_to_mmss(chunk_end-start_time)}')

    t_start = time.time()  # log start time

    # Process chunks in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_jobs) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                process_bag_chunk,
                bag_path,
                topic_name,
                out_dir,
                interval,
                chunk_id,
                chunk_start,
                chunk_end
            ): chunk_id
            for chunk_id, chunk_start, chunk_end in chunks
        }
        
        # Collect results
        total_frames = 0
        total_saved = 0
        
        with betterprint.status(f'Extracting frames from rosbag...'):
            for future in concurrent.futures.as_completed(futures):
                chunk_id, frames, saved = future.result()
                betterprint.info(f'Chunk {chunk_id} complete: processed {frames} frames (saved {saved})')
                total_frames += frames
                total_saved += saved
    
    t_end = time.time()  # log end time

    # Cleanup
    print()  # newline after 'Progress' output
    betterprint.info(f'Processed {total_frames} frames (saved {total_saved} @ n={interval}) in {t_end - t_start:.2f} s!')


if __name__ == '__main__':
    i, t, o, n, j = parse_args(sys.argv[1:])
    extract_frames_rosbag(i, t, o, n, j)
