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
  ./hloc_sfm.py -i <images_dir|shortcut>

Flags and Options:
  -h, --help                      Displays this help text.
  -i, --in=PATH        [REQUIRED] Directory containing input images for SfM (alternatively, a valid shortcut).
  -o, --out=PATH                  Directory for saving SfM data to.
  --use-defaults                  Uses default pipeline configuration (skips any user input).
  -r, --retriever=STR             Image retriever (for finding global descriptors).
  -f, --features=STR              Feature extractor.
  -m, --matcher=STR               Feature matcher.
  -q, --query=PATH                Query image to be matched against resulting 3D map.
'''

import betterprint  # local module
import getopt
import numpy as np
import pprint
import pycolmap
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
from hloc.localize_sfm import QueryLocalizer, pose_from_cluster
from hloc.utils import viz, viz_3d


# For ease of use
input_shortcuts = {'mikan': '/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2023-12-13_SfM-Example/n60/images/',
                   'ambient-y': '/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2024-1-24_Captures-for-SfM/no-flashlight/a_Y-only/images/',
                   'ambient-x': '/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2024-1-24_Captures-for-SfM/no-flashlight/b_X-only/images/',
                   'ambient-xy': '/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2024-1-24_Captures-for-SfM/no-flashlight/c_X-and-Y/images/',
                   'flash-y': '/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2024-1-24_Captures-for-SfM/with-flashlight/a_Y-only/images/',
                   'takahashi-1': '/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2024-3-12_Takahashi-Collab_(ultrasonic-sensor)/vid_camera_2/n8/images',
                   'takahashi-2': '/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2024-3-12_Takahashi-Collab_(ultrasonic-sensor)/vid_camera_3/n10/images/'}


def usage():
    """
    Prints the usage information for this script and exits.
    """
    # Show hloc configs
    betterprint.info(f'''Configs for feature extractors:\n{
                     pprint.pformat(extract_features.confs)}\n''')
    betterprint.info(f'''Configs for feature matchers:\n{
                     pprint.pformat(match_features.confs)}\n''')

    # Show input shortcuts
    betterprint.info(f'Available shortcuts: {list(input_shortcuts.keys())}')

    # Print usage
    print(sys.exit(__doc__))


def parse_args(argv):
    """
    Parses and validates input arguments for this script.
    """
    # Default args
    image_dir = ''
    output_dir = ''
    use_defaults = False
    retrieval_type = 'netvlad'
    feature_type = 'disk'
    matching_type = 'disk+lightglue'
    query = ''

    # Parsing helpers
    retrieval_type_provided = False
    feature_type_provided = False
    matching_type_provided = False

    # Parse input args according to the options' short and long forms
    opts, _ = getopt.getopt(
        argv, 'hi:o:r:f:m:q:', ['help', 'in=', 'out=', 'use-defaults', 'retriever=', 'features=', 'matcher=', 'query='])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Input - Images Dir
        elif opt in ('-i', '--in'):
            # Check if a "secret nickname" was provided instead of an actual path
            if arg in input_shortcuts:
                output_dir = Path(f'outputs/{arg}/').resolve()
                arg = input_shortcuts[arg]

            image_dir = Path(arg)
            if not image_dir.exists():
                betterprint.err(f'Invalid input filepath: {image_dir}')
                sys.exit()

        # Output - Models & Databases Dir
        elif opt in ('-o', '--out'):
            output_dir = Path(f'outputs/{arg}/').resolve()

        # "Use Defaults" Flag
        elif opt in ('--use-defaults'):
            use_defaults = True

        # Image Retrieval Config
        elif opt in ('-r', '--retriever'):
            retrieval_type = arg
            retrieval_type_provided = True
            if retrieval_type not in extract_features.confs:
                betterprint.err('Unsupported image retriever: '
                                + retrieval_type)
                sys.exit()

        # Feature Extraction Config
        elif opt in ('-f', '--features'):
            feature_type = arg
            feature_type_provided = True
            if feature_type not in extract_features.confs:
                betterprint.err('Unsupported feature extractor: '
                                + feature_type)
                sys.exit()

        # Feature Matching Config
        elif opt in ('-m', '--matcher'):
            matching_type = arg
            matching_type_provided = True
            if matching_type not in match_features.confs:
                betterprint.err('Unsupported feature matcher: '
                                + matching_type)
                sys.exit()

        # Localization Query Path
        elif opt in ('-q', '--query'):
            query = Path(arg)
            if not query.exists():
                betterprint.err(f'Invalid query filepath: {query}')
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

    if not use_defaults:
        # User input for selecting a retriever
        while not retrieval_type_provided:
            sel = betterprint.ask(
                'Please select a retriever (default: netvlad).').lower()
            if not sel:
                # Empty input
                betterprint.err(
                    'You must select a retriever! To just use defaults, pass the --use-defaults flag.')
            elif sel not in extract_features.confs:
                # Invalid retriever
                betterprint.err('Unsupported image retriever: ' + sel)
            else:
                # Valid retriever
                retrieval_type = sel
                retrieval_type_provided = True

        # User input for selecting a feature extractor
        while not feature_type_provided:
            sel = betterprint.ask(
                'Please select an extractor (default: disk).').lower()
            if not sel:
                # Empty input
                betterprint.err(
                    'You must select an extractor! To just use defaults, pass the --use-defaults flag.')
            elif sel not in extract_features.confs:
                # Invalid retriever
                betterprint.err('Unsupported feature extractor: ' + sel)
            else:
                # Valid extractor
                feature_type = sel
                feature_type_provided = True

        # User input for selecting a feature matcher
        while not matching_type_provided:
            sel = betterprint.ask(
                'Please select a matcher (default: disk+lightglue).').lower()
            if not sel:
                # Empty input
                betterprint.err(
                    'You must select a matcher! To just use defaults, pass the --use-defaults flag.')
            elif sel not in match_features.confs:
                # Invalid retriever
                betterprint.err('Unsupported feature matcher: ' + sel)
            else:
                # Valid matcher
                matching_type = sel
                matching_type_provided = True

    return image_dir, output_dir, retrieval_type, feature_type, matching_type, query


class HlocSfm:
    def __init__(self, i, o, r, f, m):
        # Initialize input arg-based member variables
        self.image_dir = i
        self.output_dir = o
        self.retrieval_conf = extract_features.confs[r]
        self.feature_conf = extract_features.confs[f]
        self.matching_conf = match_features.confs[m]

        self.references = [p.relative_to(self.image_dir).as_posix()
                           for p in (self.image_dir).iterdir()]

        # Set output paths
        # - Top `k` pairs retrieved from global descriptors (default: k=10)
        self.sfm_pairs = self.output_dir / (f'pairs-{r}-sfm.txt')
        # - All query pairs retrieved from exhaustive matching
        self.loc_pairs = self.output_dir / (f'pairs-{r}-loc.txt')
        # - HDF database for all extracted features
        self.features = self.output_dir / (f'features-{f}.h5')
        # - HDF database for all matched features
        self.matches = self.output_dir / (f'matches-{m}.h5')
        # - Resulting SfM model
        self.sfm_dir = self.output_dir / (f'sfm_{f}-with-{m}')

        # Declare member variables that will be initialized later
        self.model = None

    def localize(self, query):
        """
        Localize a single "query" image in an existing 3D map
        """
        # Extract features and match exhaustively (since it's only a single image)
        betterprint.info('Starting query feature extraction and matching...')
        sleep(1)

        pairs_from_exhaustive.main(self.loc_pairs, image_list=[
                                   query], ref_list=self.references)
        extract_features.main(self.feature_conf, self.image_dir, image_list=[
                              query], feature_path=self.features, overwrite=True)
        match_features.main(self.matching_conf, self.loc_pairs,
                            self.features, matches=self.matches, overwrite=True)

        # Estimate absolute camera pose using PnP+RANSAC
        betterprint.info('Estimating query camera parameters and pose...')
        sleep(1)

        conf = {
            "estimation": {"ransac": {"max_error": 12}},
            "refinement": {"refine_focal_length": True, "refine_extra_params": True},
        }
        localizer = QueryLocalizer(self.model, conf)

        # Estimate camera parameters from image EXIF data
        camera = pycolmap.infer_camera_from_image(self.image_dir / query)
        ref_ids = [self.model.find_image_with_name(
            r).image_id for r in self.references]

        # Refine camera parameters
        ret, log = pose_from_cluster(
            localizer, query, camera, ref_ids, self.features, self.matches)

        betterprint.info(
            f'Found {ret["num_inliers"]}/{len(ret["inliers"])} inlier correspondences')

        # Visualize localization of query relative to original dataset
        betterprint.info('Generating 2D visualization...')
        sleep(1)

        visualization.visualize_loc_from_log(  # doesn't show in WSL2
            self.image_dir, query, log, self.model)
        viz.save_plot(self.output_dir / 'visualization_query-2D.pdf')

        betterprint.info('Generating 3D visualization...')
        sleep(1)

        fig = viz_3d.init_figure()
        pose = pycolmap.Image(cam_from_world=ret["cam_from_world"])
        viz_3d.plot_camera_colmap(
            fig, pose, camera, color="rgba(0,255,0,0.5)", name=query, fill=True)

        inl_3d = np.array([self.model.points3D[pid].xyz for pid in np.array(
            log["points3D_ids"])[ret["inliers"]]])  # visualize 2D-3D corresp.
        viz_3d.plot_points(fig, inl_3d, color="lime", ps=1, name=query)
        fig.write_html(self.output_dir / 'visualization_query-3D.html')
        fig.show()  # doesn't show in WSL2

    def main(self):
        """
        Makes a clean directory based on the video filename
        and sequentially extracts video frames to it
        """
        # Find image pairs via image retrieval
        # Note: divided into "large dataset" and "small dataset" actions
        betterprint.info('Starting image retrieval...')
        sleep(1)

        if len(self.references) > 50:  # large dataset (see below for small): match based on descriptors
            global_descriptors = extract_features.main(
                self.retrieval_conf, self.image_dir, self.output_dir)
            # Larger `k` (num_matched) improves robustness of localization for
            # difficult queries but makes matching more expensive.
            # Using `k` between 10-20 is generally a good tradeoff.
            pairs_from_retrieval.main(
                global_descriptors, self.sfm_pairs, num_matched=10)

        # Extract and match local features
        betterprint.info('Starting feature extraction and matching...')
        sleep(1)

        extract_features.main(self.feature_conf, self.image_dir, export_dir=self.output_dir,
                              image_list=self.references, feature_path=self.features)

        if len(self.references) <= 50:  # small dataset (see above for large): match exhaustively
            pairs_from_exhaustive.main(
                self.sfm_pairs, image_list=self.references)

        match_features.main(self.matching_conf, self.sfm_pairs, self.features,
                            export_dir=self.output_dir, matches=self.matches)

        # 3D reconstruction (via COLMAP) -- longest step!
        betterprint.info('Starting reconstruction...')
        sleep(1)

        self.model = reconstruction.main(self.sfm_dir, self.image_dir, self.sfm_pairs,
                                         self.features, self.matches, image_list=self.references)

        # Visualize results
        betterprint.info('Generating 2D visualization...')
        sleep(1)

        # TODO: for some reason, save_plot() below only saves the last selected picture

        # Note: explanation of keypoint visualization types (using color_by)
        # - 'visibility': blue if successfully triangulated, red if never matched
        # - 'track_length': red if observed many times, blue if few
        # - 'depth': red if relatively far away, blue if closer
        visualization.visualize_sfm_2d(  # doesn't show in WSL2
            self.model, self.image_dir, color_by='visibility', selected=[2, 12, 20], n=3)
        viz.save_plot(self.output_dir / 'visualization_2D-vis.pdf')

        visualization.visualize_sfm_2d(  # doesn't show in WSL2
            self.model, self.image_dir, color_by='track_length', selected=[2, 12, 20], n=3)
        viz.save_plot(self.output_dir / 'visualization_2D-tracklen.pdf')

        visualization.visualize_sfm_2d(  # doesn't show in WSL2
            self.model, self.image_dir, color_by='depth', selected=[2, 12, 20], n=3)
        viz.save_plot(self.output_dir / 'visualization_2D-depth.pdf')

        betterprint.info('Generating 3D visualization...')
        sleep(1)

        fig = viz_3d.init_figure()
        viz_3d.plot_reconstruction(
            fig, self.model, color='rgba(255,0,0,0.5)', name='mapping')
        fig.write_html(self.output_dir / 'visualization_3D.html')
        fig.show()  # doesn't show in WSL2

        betterprint.info('Done!')


if __name__ == '__main__':
    i, o, r, f, m, q = parse_args(sys.argv[1:])
    hloc_sfm = HlocSfm(i, o, r, f, m)
    hloc_sfm.main()
    if q:
        hloc_sfm.localize(q)
