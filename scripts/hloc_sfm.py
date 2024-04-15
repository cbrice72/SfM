#!/usr/bin/env python3

###############################################################################
# @file   hloc_sfm.py
# @brief  LIBRA project SfM pipeline using hloc.
#
# @author brice.c.aa
# @date   2024/4/15
###############################################################################

'''
Usage:
  ./hloc_sfm.py

Flags and Options:
  -h, --help                      Displays this help text.
  -i, --in=PATH        [REQUIRED] Directory containing input images for SfM.
  -o, --out=PATH                  Directory for saving SfM data to.
  -r, --retriever=STR             Image retriever (for finding global descriptors).
  -e, --extractor=STR             Feature extractor.
  -m, --matcher=STR               Feature matcher.
'''

import betterprint  # local module
import getopt
import pprint
import sys
from time import sleep
from pathlib import Path
from hloc import (
    extract_features,
    match_features,
    pairs_from_exhaustive,
    pairs_from_retrieval,
    reconstruction,
    visualization
)
from hloc.utils import viz, viz_3d


def usage():
    """
    Prints the usage information for this script and exits.
    """
    print(f'''Configs for feature extractors:\n\n{
          pprint.pformat(extract_features.confs)}''')
    print(f'''Configs for feature matchers:\n\n{
          pprint.pformat(match_features.confs)}''')
    print(sys.exit(__doc__))


def parse_args(argv):
    """
    Parses and validates the input arguments.
    """
    image_dir = ''
    output_dir = ''
    retrieval_type = ''
    extraction_type = ''
    matching_type = ''

    # Parse input args according to the options' short and long forms
    opts, _ = getopt.getopt(
        argv, 'hi:o:r:e:m:', ['help', 'in=', 'out=', 'retriever=', 'extractor=', 'matcher='])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Input - Images Dir
        elif opt in ('-i', '--in'):
            # Check if a "secret nickname" was provided instead of an actual path
            if arg == "mikan":
                output_dir = Path(f'outputs/{arg}/').resolve()
                arg = '/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2023-12-13_SfM-Example/n60/images/'

            image_dir = Path(arg)
            if not image_dir.exists():
                betterprint.err(f'Invalid input filepath: {image_dir}')
                sys.exit()

        # Output - Models & Databases Dir
        elif opt in ('-o', '--out'):
            output_dir = Path(f'outputs/{arg}/').resolve()

        # Image Retrieval Config
        elif opt in ('-r', '--retriever'):
            retrieval_type = arg
            if retrieval_type not in extract_features.confs:
                betterprint.err('Unsupported image retriever: '
                                + retrieval_type)
                sys.exit()

        # Feature Extraction Config
        elif opt in ('-e', '--extractor'):
            extraction_type = arg
            if extraction_type not in extract_features.confs:
                betterprint.err('Unsupported feature extractor: '
                                + extraction_type)
                sys.exit()

        # Feature Matching Config
        elif opt in ('-m', '--matcher'):
            matching_type = arg
            if matching_type not in match_features.confs:
                betterprint.err('Unsupported feature matcher: '
                                + matching_type)
                sys.exit()

    # Check for required args (getopt has no concept of "mandatory" options)
    if not image_dir:
        usage()

    # Set optional args, if necessary
    if not output_dir:
        # By default, use input image directory as output root directory
        output_dir = Path(image_dir + "output")
        betterprint.warn(
            f'Output directory not specified; defaulting to {output_dir}')

    if not retrieval_type:
        sel = betterprint.ask(
            'Please select a retriever (default: netvlad) [str]').lower()
        retrieval_type = 'netvlad' if not sel else sel

    if not extraction_type:
        sel = betterprint.ask(
            'Please select an extractor (default: disk) [str]').lower()
        extraction_type = 'disk' if not sel else sel

    if not matching_type:
        sel = betterprint.ask(
            'Please select a matcher (default: disk+lightglue) [str]').lower()
        matching_type = 'disk+lightglue' if not sel else sel

    return image_dir, output_dir, retrieval_type, extraction_type, matching_type


def main(image_dir, output_dir, retrieval_type, extraction_type, matching_type):
    """
    Makes a clean directory based on the video filename
    and sequentially extracts video frames to it
    """
    # Configure pipeline
    retrieval_conf = extract_features.confs[retrieval_type]
    extraction_conf = extract_features.confs[extraction_type]
    matching_conf = match_features.confs[matching_type]

    # Set output paths
    sfm_pairs = output_dir / (f'pairs-{retrieval_type}-sfm.txt')
    loc_pairs = output_dir / (f'pairs-{retrieval_type}-loc.txt')
    sfm_dir = output_dir / (f'sfm_{extraction_type}+{matching_type}')

    # Find image pairs via image retrieval
    # TODO: is this necessary at this point?
    betterprint.info('Starting image retrieval...')
    sleep(1)

    global_descriptors = extract_features.main(
        retrieval_conf, image_dir, output_dir)
    pairs_from_retrieval.main(global_descriptors, sfm_pairs, num_matched=5)
    # pairs_from_exhaustive.main(sfm_pairs)

    # Extract and match local features
    betterprint.info('Starting feature extraction and matching...')
    sleep(1)

    features = extract_features.main(
        extraction_conf, image_dir, output_dir)
    matches = match_features.main(
        matching_conf, sfm_pairs, extraction_conf['output'], output_dir
    )

    # 3D reconstruction (via COLMAP) -- longest step!
    betterprint.info('Starting reconstruction...')
    sleep(1)

    model = reconstruction.main(
        sfm_dir, image_dir, sfm_pairs, features, matches)

    # Visualize results
    betterprint.info('Generating visualizations...')
    sleep(1)

    # visualization.visualize_sfm_2d(model, image_dir, color_by='visibility', n=3)
    # visualization.visualize_sfm_2d(model, image_dir, color_by='track_length', n=3)
    visualization.visualize_sfm_2d(model, image_dir, color_by='depth', n=3)
    viz.save_plot(output_dir / 'visualization.pdf')

    fig = viz_3d.init_figure()
    viz_3d.plot_reconstruction(
        fig, model, color='rgba(255,0,0,0.5)', name='mapping', points_rgb=True
    )
    fig.show()  # TODO: fix this, maybe save as a file instead

    betterprint.info('Done!')


if __name__ == '__main__':
    i, o, r, e, m = parse_args(sys.argv[1:])
    main(i, o, r, e, m)
