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
  --force-reprocess               Force reprocessing of all steps, ignoring existing files.
  -r, --retriever=STR             Image retriever (for finding global descriptors).
  -f, --features=STR              Feature extractor.
  -m, --matcher=STR               Feature matcher.
  -q, --query=PATH                Query image to be matched against resulting 3D map.
'''

import betterprint  # local module
from make_turntable import make_turntable  # local module

from datetime import timedelta
from enum import Enum, auto
import getopt
from math import floor
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pprint
import re
import sys
from time import sleep, time

import pycolmap
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
input_shortcuts = {'mikan': '/mnt/e/LIBRA Archive/2023-12-13_SfM-Example/n60/images/',
                   'ambient-z': '/mnt/e/LIBRA Archive/2024-01-24_Captures-for-SfM/no-flashlight/a_Z-only/images/',
                   'ambient-y': '/mnt/e/LIBRA Archive/2024-01-24_Captures-for-SfM/no-flashlight/b_Y-only/images/',
                   'ambient-yz': '/mnt/e/LIBRA Archive/2024-01-24_Captures-for-SfM/no-flashlight/c_Y-and-Z/images/',
                   'flash-z': '/mnt/e/LIBRA Archive/2024-01-24_Captures-for-SfM/with-flashlight/a_Z-only/images/',
                   'takahashi-1': '/mnt/e/LIBRA Archive/2024-03-12_Takahashi-Collab_(ultrasonic-sensor)/vid_camera_2/n1/images/',
                   'takahashi-2': '/mnt/e/LIBRA Archive/2024-03-12_Takahashi-Collab_(ultrasonic-sensor)/vid_camera_3/n1/images/',
                   'takahashi-combined': '/mnt/e/LIBRA Archive/2024-03-12_Takahashi-Collab_(ultrasonic-sensor)/combined/n1/images/',
                   'rtab-control': '/mnt/e/LIBRA Archive/2025-04-25 LIBRA-I RTAB-Map (RealSense only)/maps/ground-truth/images/',
                   'rtab-rgbd': '/mnt/e/LIBRA Archive/2025-04-25 LIBRA-I RTAB-Map (RealSense only)/bags/n30/images/'}

# Switch between hloc's pyplot-based export into .html and COLMAP's export into .ply
use_colmap_3d_export = True


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
    image_dir = None
    output_dir = ''
    use_defaults = False
    force_reprocess = False
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
        argv, 'hi:o:r:f:m:q:', ['help', 'in=', 'out=', 'use-defaults', 'retriever=', 'features=', 'matcher=', 'force', 'query='])

    # Validate options
    for opt, arg in opts:
        # Help
        if opt in ('-h', '--help'):
            usage()

        # Input - Images Directory
        elif opt in ('-i', '--in'):
            # Check if a shortcut was provided instead of an actual path
            if arg in input_shortcuts:
                output_dir = Path(f'outputs/{arg}/').resolve()
                arg = input_shortcuts[arg]

            image_dir = Path(arg)
            if not image_dir.exists():
                betterprint.err(f'Invalid input filepath: {image_dir}')
                sys.exit()

        # Output - Models & Databases Directory
        elif opt in ('-o', '--out'):
            output_dir = Path(arg).expanduser().resolve()

        # "Use Defaults" Flag
        elif opt in ('--use-defaults'):
            use_defaults = True

        # "Force Reprocessing" Flag
        elif opt in ('--force'):
            force_reprocess = True

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
        # By default, place output directory in same location as input image directory
        output_dir = image_dir.resolve().parent / "output"
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

    return image_dir, output_dir, force_reprocess, retrieval_type, feature_type, matching_type, query


class PipelineStep(Enum):
    RETRIEVE = auto()
    EXTRACT = auto()
    MATCH = auto()
    SPARSE = auto()
    VISUALIZE = auto()
    UNDISTORT = auto()
    STEREO = auto()
    FUSION = auto()
    MESH_POISSON = auto()
    MESH_DELAUNAY = auto()


class HlocSfm:
    def __init__(self, i, o, force, r, f, m):
        # Initialize input arg-based member variables
        self.image_dir = i
        self.output_dir = o
        self.force_reprocess = force
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
        # - Database (HDF5) for all extracted features
        self.features = self.output_dir / (f'features-{f}.h5')
        # - Database (HDF5) for all matched features
        self.matches = self.output_dir / (f'matches-{m}.h5')
        # - Resulting sparse reconstruction (SfM model)
        self.sfm_dir = self.output_dir / (f'sfm_{f}-with-{m}')
        # - Visualizations directory
        self.vis_dir = self.output_dir / 'visualizations'
        # - Resulting dense reconstruction (multi-view stereo)
        self.mvs_dir = self.sfm_dir / "dense"
        # - Script statistics log file
        self.log_file = self.output_dir / f'summary-{r}-{f}-{m}.txt'

        # Declare member variables that will be initialized later
        self.model = None
        self.global_descriptors = None
        self.num_images = len(self.references)
        self.skip_steps = {}

        # For calculating overall script runtime
        self.t_total = 0

        # For holding timestamp strings
        self.t_retrieve = '---'
        self.t_extract = '---'
        self.t_match = '---'
        self.t_sparse = '---'
        self.t_visuals = '---'
        self.t_undistort = '---'
        self.t_stereo = '---'
        self.t_fusion = '---'
        self.t_mesh = '---'

    def _check_existing_outputs(self):
        """
        Checks whether any steps have already been computed and, if so,
        instructs the rest of the script to use the existing data.
        Useful when execution fails partway through large datasets.
        """
        self.skip_steps = {step: False for step in PipelineStep}

        # Exit early if user requested reprocessing
        if self.force_reprocess:
            betterprint.warn('Force reprocessing flag set, all steps will be executed')
            return

        # Check for database files
        if self.sfm_pairs.exists():
            self.skip_steps[PipelineStep.RETRIEVE] = True
        if self.features.exists():
            self.skip_steps[PipelineStep.EXTRACT] = True
        if self.matches.exists():
            self.skip_steps[PipelineStep.MATCH] = True
            
        # Check for sparse reconstruction and try to load it
        if self.sfm_dir.exists() and (self.sfm_dir / 'images.bin').exists() and (self.sfm_dir / 'points3D.bin').exists():
            try:
                self.model = pycolmap.Reconstruction(self.sfm_dir)
                betterprint.info(f'Successfully loaded existing model with {len(self.model.images)} images and {len(self.model.points3D)} points')
                self.skip_steps[PipelineStep.SPARSE] = True
            except Exception as e:
                betterprint.err(f'Failed to load existing model: {e}')
                self.skip_steps[PipelineStep.SPARSE] = False
        
        # Check whether sample visualizations were generated
        if (self.vis_dir / '3D-sparse.ply').exists() or (self.vis_dir / '3D-sparse.html').exists():
            self.skip_steps[PipelineStep.VISUALIZE] = True
            
        # Check all dense reconstruction steps
        if (self.mvs_dir / 'images').exists() and (self.mvs_dir / 'sparse').exists():
            self.skip_steps[PipelineStep.UNDISTORT] = True
        stereo_dir = self.mvs_dir / 'stereo'
        if stereo_dir.exists():
            has_maps = any((stereo_dir / 'depth_maps').glob('*.bin')) and any((stereo_dir / 'normal_maps').glob('*.bin'))
            has_configs = (stereo_dir / 'fusion.cfg').exists() and (stereo_dir / 'patch-match.cfg').exists()
            if has_maps and has_configs:
                self.skip_steps[PipelineStep.STEREO] = True
        if (self.vis_dir / '3D-dense.ply').exists():
            self.skip_steps[PipelineStep.FUSION] = True

        # Check whether each mesh was generated
        if (self.vis_dir / 'mesh-poisson.ply').exists():
            self.skip_steps[PipelineStep.MESH_POISSON] = True
        if (self.vis_dir / 'mesh-delaunay.ply').exists():
            self.skip_steps[PipelineStep.MESH_DELAUNAY] = True
            
        return self.skip_steps

    def _validate_image_filenames(self):
        """
        Validates image filenames in the specified input directory.
        """        
        if not self.image_dir.exists():
            betterprint.err(f"Input directory '{self.image_dir}' does not exist")
            sys.exit()
        
        # Explanation of the following regex:
        # - Must start with alphanumeric ONLY
        # - Rest of name can be any combination of alphanumeric, underscore, hyphen, or period
        # - Must end in common image file extension
        valid_filename_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_\-.]*\.(jpg|jpeg|png|tif|tiff)$', re.IGNORECASE)
        error_msgs = []
        
        for filepath in self.image_dir.iterdir():
            if not filepath.is_file():
                continue  # skip directories
                
            filename = filepath.name
            problems = []
            
            # Check for spaces
            if ' ' in filename:
                problems.append("contains spaces")
            
            # Check for valid format with regex
            if not valid_filename_pattern.match(filename):
                # If regex failed, identify specific issue(s)
                if not any(ext in filename.suffix.lower() for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']):
                    problems.append("invalid extension")
                if filename.startswith('.'):
                    problems.append("starts with period")
                if re.search(r'[^a-zA-Z0-9_\-.]', filename):
                    problems.append("contains special characters")
            
            # Compile human-readable error message
            if problems:
                error_msgs.append(f"'{filename}': {', '.join(problems)}")
        
        if error_msgs:
            betterprint.err("Found problematic filenames that will cause hloc to fail:")
            for issue in error_msgs:
                betterprint.err(f"  - {issue}")
            
            betterprint.err("Please rename these files to remove spaces and special characters (example of valid filename: image_001.jpg).")
            sys.exit()

    def _log_results(self):
        """
        Logs and prints reconstruction statistics.
        """
        betterprint.info('Done!')

        # Print and log statistics
        summary_reconstr = f'{self.model.summary()}\n'
        summary_elapsed = ('Elapsed Time:              H:MM:SS.MS\n'
                          f'	Image Retrieval    {self.t_retrieve}\n'
                          f'	Feat. Extraction   {self.t_extract}\n'
                          f'	Feat. Matching     {self.t_match}\n'
                          f'	Sparse Reconstr.   {self.t_sparse}\n'
                          f'	Visualizations     {self.t_visuals}\n'
                          f'	Undistortion       {self.t_undistort}\n'
                          f'	Stereo (MVS)       {self.t_stereo}\n'
                          f'	Fusion (dense)     {self.t_fusion}\n'
                          f'	Mesh Generation    {self.t_mesh}\n'
                          f'	-----TOTAL-----    {self.t_total}\n')

        betterprint.info(f'''===[ RESULTS ]===\n{
                         summary_reconstr}\n{summary_elapsed}''')

        with open(self.log_file, 'w') as f:
            f.write(summary_reconstr)
            f.write(summary_elapsed)

    def main(self):
        """
        Runs the selected SfM pipeline on a set of images.
        """
        # Validation and Preparation
        self._validate_image_filenames()
        self._check_existing_outputs()

        # Structure-from-Motion
        ts = time()

        self.retrieve_image_pairs()
        self.extract_and_match_features()
        self.perform_sparse_reconstruction()
        self.generate_visualizations()
        self.perform_dense_reconstruction()
        self.generate_meshes()

        self.t_total = str(timedelta(seconds=(time()-ts)))
        
        # Cleanup
        self._log_results()

    def retrieve_image_pairs(self):
        """
        Finds image pairs via image retrieval (if dataset > 50 images).
        """
        if self.skip_steps.get(PipelineStep.RETRIEVE):
            betterprint.info('Using existing image pairs')
            return
        
        betterprint.info('Starting image retrieval...')
        sleep(1)
        ts = time()

        # For large datasets: match based on descriptors
        if self.num_images > 50:
            self.global_descriptors = extract_features.main(
                self.retrieval_conf, self.image_dir, self.output_dir)
            # Larger `k` (num_matched) improves robustness of localization for
            # difficult queries but makes matching more expensive.
            # Using `k` between 10-20 is generally a good tradeoff.
            pairs_from_retrieval.main(
                self.global_descriptors, self.sfm_pairs, num_matched=10)
        else:
            # For small datasets: defer to exhaustive matching in extract_and_match_features()
            pass

        self.t_retrieve = str(timedelta(seconds=(time()-ts)))

    def extract_and_match_features(self):
        """
        Extracts and matches local features.
        """
        if not self.skip_steps[PipelineStep.EXTRACT]:
            betterprint.info('Starting feature extraction...')
            sleep(1)
            ts = time()

            extract_features.main(self.feature_conf, self.image_dir, export_dir=self.output_dir,
                                image_list=self.references, feature_path=self.features)

            self.t_extract = str(timedelta(seconds=(time()-ts)))
        else:
            betterprint.info('Using existing features database')
        
        if not self.skip_steps[PipelineStep.MATCH]:
            betterprint.info('Starting feature matching...')
            sleep(1)
            ts = time()

            # For small datasets: match exhaustively
            if self.num_images <= 50:
                pairs_from_exhaustive.main(
                    self.sfm_pairs, image_list=self.references)

            match_features.main(self.matching_conf, self.sfm_pairs, self.features,
                                export_dir=self.output_dir, matches=self.matches)

            self.t_match = str(timedelta(seconds=(time()-ts)))
        else:
            betterprint.info('Using existing matches database')

    def perform_sparse_reconstruction(self):
        """
        Performs sparse 3D reconstruction.
        """
        if self.skip_steps.get(PipelineStep.SPARSE):
            betterprint.info('Using existing sparse model')
            return
        
        betterprint.info('Starting sparse reconstruction...')
        sleep(1)
        ts = time()

        # TODO: reconstruction with known camera parameters
        # img_opts = dict(camera_model='SIMPLE_PINHOLE', camera_params=','.join(map(str, (f, cx, cy, k))))
        # map_opts = dict(ba_refine_focal_length=False, ba_refine_extra_params=False)
        # self.model = reconstruction.main(..., image_options=img_opts, mapper_options=map_opts)

        # NOTE: hloc uses and returns a COLMAP `Reconstruction` object
        self.model = reconstruction.main(self.sfm_dir, self.image_dir, self.sfm_pairs,
                                         self.features, self.matches, image_list=self.references)

        self.t_sparse = str(timedelta(seconds=(time()-ts)))

    def generate_visualizations(self):
        """
        Generates 2D and 3D visualizations of the reconstruction.
        """
        if self.skip_steps.get(PipelineStep.VISUALIZE):
            betterprint.info('Skipping visualization generation (already generated)')
            return
        
        betterprint.info('Generating 2D visualizations...')
        print('       (a total of 15 visualizations will be generated; this will take a few minutes)')
        sleep(1)
        ts = time()

        Path(self.vis_dir / '2D-visibility').mkdir(parents=True, exist_ok=True)
        Path(self.vis_dir / '2D-tracklength').mkdir(parents=True, exist_ok=True)
        Path(self.vis_dir / '2D-depth').mkdir(parents=True, exist_ok=True)

        for i in range(1, self.num_images, floor(self.num_images * 0.2)):  # save 5 samples
            # NOTE: explanation of keypoint visualization types (using color_by)
            # - 'visibility': BLUE if successfully triangulated, RED if never matched
            # - 'track_length': RED if observed many times, BLUE if few
            # - 'depth': RED if relatively far away, BLUE if closer

            # NOTE: for some reason, save_plot() only saves the last selected picture,
            # so we generate and save them one at a time

            try:
                visualization.visualize_sfm_2d(  # no popup in WSL2
                    self.model, self.image_dir, color_by='visibility', selected=[i])
                viz.save_plot(self.vis_dir / '2D-visibility' /
                              f'visbl-{i}.pdf')
                plt.close()

                visualization.visualize_sfm_2d(  # no popup in WSL2
                    self.model, self.image_dir, color_by='track_length', selected=[i])
                viz.save_plot(self.vis_dir / '2D-tracklength' /
                              f'trlen-{i}.pdf')
                plt.close()

                visualization.visualize_sfm_2d(  # no popup in WSL2
                    self.model, self.image_dir, color_by='depth', selected=[i])
                viz.save_plot(self.vis_dir / '2D-depth' / f'depth-{i}.pdf')
                plt.close()
            except:
                betterprint.warn(
                    f'Selected image index ({i}) out of range, skipping!')

        betterprint.info('Generating 3D (sparse) visualization...')
        sleep(1)

        if not use_colmap_3d_export:
            # 3D point cloud w/ camera poses, viewable in web browser
            fig = viz_3d.init_figure()
            viz_3d.plot_reconstruction(
                fig, self.model, color='rgba(255,0,0,0.5)', name='mapping')
            fig.write_html(self.vis_dir / '3D-sparse.html')
            fig.show()  # no popup in WSL2
        else:
            # Text and PLY format models, PLY viewable in MeshLab
            self.model.write_text(self.sfm_dir)
            ply_file = self.vis_dir / '3D-sparse.ply'
            self.model.export_PLY(ply_file)

            # Generate a GIF of the PLY model for quick visualization
            make_turntable(str(ply_file))
        
        self.t_visuals = str(timedelta(seconds=(time()-ts)))

    def perform_dense_reconstruction(self):
        """
        Performs dense 3D reconstruction (via COLMAP).
        """
        if "patch_match_stereo" not in dir(pycolmap):  # only exists if compiled w/ CUDA
            betterprint.warn('patch_match_stereo not found; skipping dense reconstruction.\n'
                             '       This probably means pycolmap wasn\'t compiled from source,\n'
                             '       or was not compiled with CUDA support.')
            return
        
        # Dense 3D reconstruction (via COLMAP) -- longest step!
        betterprint.info('Starting dense reconstruction...')
        betterprint.warn(
            'This step may take a LONG time!! You should probably find something else to do in the meantime.')
        sleep(3)
        ts = time()

        # Cap the max image size at a standard 1280 pixels (i.e., 720p).
        # This is mainly so stereo matching is more tolerant of small
        # discrepancies, although it's also used by stereo fusion.
        max_image_size = 1280

        if not self.skip_steps[PipelineStep.UNDISTORT]:
            ts = time()
            betterprint.info('Undistorting images...')

            pycolmap.undistort_images(self.mvs_dir, self.sfm_dir, self.image_dir)

            self.t_undistort = str(timedelta(seconds=(time()-ts)))
        else:
            betterprint.info('Using existing undistorted images')

        if not self.skip_steps[PipelineStep.STEREO]:
            ts = time()
            betterprint.info('Running stereo matching...')

            pycolmap.patch_match_stereo(
                self.mvs_dir,
                options={
                    'max_image_size': max_image_size,
                    'geom_consistency': True,
                    'filter': True,
                    'allow_missing_files': True,
                }
            )

            self.t_stereo = str(timedelta(seconds=(time()-ts)))
        else:
            betterprint.info('Using existing stereo results')

        if not self.skip_steps[PipelineStep.FUSION]:
            ts = time()
            betterprint.info('Running stereo fusion...')

            pycolmap.stereo_fusion(
                self.vis_dir / "3D-dense.ply",
                self.mvs_dir,
                options={
                    'max_image_size': max_image_size,
                    'cache_size': 12,  # gigabytes
                }
            )

            self.t_fusion = str(timedelta(seconds=(time()-ts)))
        else:
            betterprint.info('Using existing dense reconstruction')
            
    def generate_meshes(self):
        """
        Generates 3D meshes from the dense point cloud.
        """
        self._generate_poisson_mesh()
        self._generate_delaunay_mesh()

    def _generate_poisson_mesh(self):
        """
        Generates a Poisson mesh from the dense point cloud.
        
        @see https://hhoppe.com/poissonrecon.pdf
        """
        # Early exit cases
        if self.skip_steps.get(PipelineStep.MESH_POISSON):
            betterprint.info('Skipping Poisson meshing (already generated)')
            return

        if "poisson_meshing" not in dir(pycolmap):
            betterprint.warn('poisson_meshing not found; skipping.')
            return

        # Generate mesh
        input_ply = self.vis_dir / "3D-dense.ply"
        output_ply = self.vis_dir / "3D-mesh-poisson.ply"

        if not input_ply.exists():
            betterprint.warn('Dense point cloud not found; skipping Poisson meshing.')
            return

        betterprint.info('Starting Poisson mesh generation...')
        sleep(1)
        ts = time()

        pycolmap.poisson_meshing(input_ply, output_ply, options={'trim': 10.0})

        self.t_mesh = str(timedelta(seconds=(time()-ts)))

    def _generate_delaunay_mesh(self):
        """
        Generates a Delaunay mesh from the multi-view stereo workspace.

        @see https://link.springer.com/chapter/10.1007/978-3-540-33259-6_6
        """
        # Early exit cases
        if self.skip_steps.get(PipelineStep.MESH_DELAUNAY):
            betterprint.info('Skipping Delaunay meshing (already generated)')
            return

        if "delaunay_meshing" not in dir(pycolmap):
            betterprint.warn('delaunay_meshing not found; skipping.')
            return

        # Generate mesh
        input_dir = self.mvs_dir
        output_ply = self.vis_dir / "3D-mesh-delaunay.ply"

        if not (input_dir / 'images').exists():
            betterprint.warn('MVS workspace not found; skipping Delaunay meshing.')
            return

        betterprint.info('Starting Delaunay mesh generation...')
        sleep(1)
        ts = time()

        pycolmap.delaunay_meshing(input_dir, output_ply)

        self.t_delaunay = str(timedelta(seconds=(time()-ts)))

    def localize(self, query):
        """
        Localize a single "query" image in an existing 3D map.

        TODO: make this a standalone function so we can run it on past maps
        """
        # Extract features and match exhaustively (since it's only a single image)
        betterprint.info('Starting query feature extraction and matching...')
        sleep(1)
        ts = time()
        t_qstart = ts

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
        
        t_qmatch = str(timedelta(seconds=(time()-ts)))
        ts = time()

        # Visualize localization of query relative to original dataset
        betterprint.info('Generating 2D visualization...')
        sleep(1)

        visualization.visualize_loc_from_log(  # no popup in WSL2
            self.image_dir, query, log, self.model)
        filepath_2d_viz = self.output_dir / 'visualization_query-2D.pdf'
        viz.save_plot(filepath_2d_viz)

        betterprint.info('Generating 3D visualization...')
        sleep(1)

        fig = viz_3d.init_figure()
        pose = pycolmap.Image(cam_from_world=ret["cam_from_world"])
        viz_3d.plot_camera_colmap(
            fig, pose, camera, color="rgba(0,255,0,0.5)", name=query, fill=True)

        inl_3d = np.array([self.model.points3D[pid].xyz for pid in np.array(
            log["points3D_ids"])[ret["inliers"]]])  # visualize 2D-3D corresp.
        viz_3d.plot_points(fig, inl_3d, color="lime", ps=1, name=query)
        filepath_3d_viz = self.output_dir / 'visualization_query-3D.html'
        fig.write_html(filepath_3d_viz)
        fig.show()  # no popup in WSL2

        end_time = time()
        t_qvisuals = str(timedelta(seconds=(end_time-ts)))

        # Print statistics
        t_qtotal = str(timedelta(seconds=(end_time-t_qstart)))

        betterprint.info('Done!')
        summary_query = ('Query Matching:\n'
                        f'  Inlier corresp.    {ret["num_inliers"]}/{len(ret["inliers"])}\n'
                        f'	Est. 2D location   {filepath_2d_viz}\n'
                        f'	Est. 3D corresp.   {filepath_3d_viz}\n')
        summary_elapsed = ('Elapsed Time:              H:MM:SS.MS\n'
                          f'	Localization       {t_qmatch}\n'
                          f'	Visualizations     {t_qvisuals}\n'
                          f'	-----TOTAL-----    {t_qtotal}\n')

        betterprint.info(f'''===[ RESULTS ]===\n{summary_query}\n{summary_elapsed}''')
        
        f'Found {ret["num_inliers"]}/{len(ret["inliers"])} inlier correspondences'


if __name__ == '__main__':
    i, o, force, r, f, m, q = parse_args(sys.argv[1:])
    hloc_sfm = HlocSfm(i, o, force, r, f, m)
    hloc_sfm.main()
    if q:
        hloc_sfm.localize(q)
