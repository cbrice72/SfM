#!/usr/bin/python3

from pathlib import Path
from hloc import (
    extract_features,
    match_features,
    pairs_from_exhaustive,
    pairs_from_retrieval,
    reconstruction,
    visualization
)
from hloc.utils import viz_3d

# Set input path
images = Path(
    "/mnt/c/Users/brice/Desktop/Projects/LIBRA-II/Archive/2023-12-13_SfM-Example/n60/images/")

# Configure pipeline
sel_retrieval = "netvlad"
sel_extraction = "disk"
sel_matching = "disk+lightglue"

retrieval_conf = extract_features.confs[sel_retrieval]
extraction_conf = extract_features.confs[sel_extraction]
matching_conf = match_features.confs[sel_matching]

# Set output paths
proj_name = "oranges"

outputs = Path("outputs/" + proj_name + "/")
sfm_pairs = outputs / ("pairs-" + sel_retrieval + "-sfm.txt")
loc_pairs = outputs / ("pairs-" + sel_retrieval + "-loc.txt")
sfm_dir = outputs / ("sfm_" + sel_extraction + "+" + sel_matching)

# Find image pairs via image retrieval
retrieval_path = extract_features.main(retrieval_conf, images, outputs)
pairs_from_retrieval.main(retrieval_path, sfm_pairs, num_matched=5)
# pairs_from_exhaustive.main(sfm_pairs)

# Extract and match local features
feature_path = extract_features.main(extraction_conf, images, outputs)
match_path = match_features.main(
    matching_conf, sfm_pairs, extraction_conf["output"], outputs
)

# 3D reconstruction (via COLMAP) -- longest step!
model = reconstruction.main(
    sfm_dir, images, sfm_pairs, feature_path, match_path)

# Visualize results
# visualization.visualize_sfm_2d(model, images, color_by="visibility", n=3)
# visualization.visualize_sfm_2d(model, images, color_by="track_length", n=3)
visualization.visualize_sfm_2d(model, images, color_by="depth", n=3)

fig = viz_3d.init_figure()
viz_3d.plot_reconstruction(
    fig, model, color="rgba(255,0,0,0.5)", name="mapping", points_rgb=True
)
fig.show()
