# Using the Hierarchical Localization Toolbox

This file contains setup and usage information for `hloc`, a Python package that leverages [COLMAP](https://colmap.github.io/).

Source code and documentation for the Pixel Perfect SfM project can be found [here](https://github.com/cvg/Hierarchical-Localization/).

## Table of Contents

1. [Setup](#setup)
2. [Usage](#usage)
    - [Command-line Application](#command-line-application)
    - [Python Programming API](#python-programming-api)
3. [Tips](#tips)
4. [Troubleshooting](#troubleshooting)

## Setup

Simply follow the instructions in the `hloc` repo's `README.md`.

## Usage

### *Command-line Application*

...

### *Python Programming API*

#### **Tutorials (Jupyter Notebooks)**

There are some very well-made interactive tutorials in the Jupyter notebooks (file type: `.ipynb`) included in the root `Hierarchical-Localization` directory.
You can run through the code in these notebooks step by step to better understand `hloc`'s SfM workflow and Python API.

- `demo.ipynb`: 3D map creation and subsequent localization of arbitrary image; i.e., figuring out where it was taken in relation to the map.
- `pipeline_Aachen.ipynb`: Pipeline for outdoor (day/night) localization, given an existing [NVM](http://ccwu.me/vsfm/index.html) database.
- `pipeline_InLoc.ipynb`: Pipeline for indoor localization, given an existing [NVM](http://ccwu.me/vsfm/index.html) database.
- `pipeline_SfM.ipynb`: General SfM pipeline (images -> feature extraction & matching -> visualization), from scratch.

```bash
# Ensure Jupyter is installed
pip install jupyterlab
# Start the Jupyter server, then open the web address it prints in the command line to access the notebooks
jupyter lab
```

#### **Minimal Script**

```py
#!/usr/bin/python3

from pathlib import Path
from hloc import (
    extract_features,
    match_features,
    reconstruction,
    visualization,
    pairs_from_retrieval,
)

# Set input path
images = Path("datasets/South-Building/images/")

# Set output paths
outputs = Path("outputs/sfm/")
sfm_pairs = outputs / "pairs-netvlad.txt"
sfm_dir = outputs / "sfm_superpoint+superglue"

# Configure pipeline
retrieval_conf = extract_features.confs["netvlad"]  # for global descriptors
feature_conf = extract_features.confs["superpoint_aachen"]  # for local features
matcher_conf = match_features.confs["superglue"]  # for local features

# Find image pairs via image retrieval
retrieval_path = extract_features.main(retrieval_conf, images, outputs)
pairs_from_retrieval.main(retrieval_path, sfm_pairs, num_matched=5)  # for smaller datasets, consider using `hloc/pairs_from_exhaustive.py`

# Extract and match local features
feature_path = extract_features.main(feature_conf, images, outputs)
match_path = match_features.main(
    matcher_conf, sfm_pairs, feature_conf["output"], outputs
)

# 3D reconstruction (via COLMAP) -- longest step!
model = reconstruction.main(sfm_dir, images, sfm_pairs, feature_path, match_path)

# Visualize results
visualization.visualize_sfm_2d(model, images, color_by="depth", n=5)
```

#### **Specifying Camera Parameters**

The name of the camera models and their parameters are defined by COLMAP. Python API:

opts = dict(camera_model='SIMPLE_RADIAL', camera_params=','.join(map(str, (f, cx, cy, k))))
model = reconstruction.main(..., image_options=opts)
Command-line interface:

python -m hloc.reconstruction [...] --image_options camera_model='"SIMPLE_RADIAL"' camera_params='"256,256,256,0"'
By default, hloc refines the camera parameters during the reconstruction process. To prevent this, add:

reconstruction.main(..., mapper_options=dict(ba_refine_focal_length=False, ba_refine_extra_params=False))
python -m hloc.reconstruction [...] --mapper_options ba_refine_focal_length=False ba_refine_extra_params=False

## Tips

### *Supported Pipeline Configurations* 

|Image Retrieval|Feature Extraction|Feature Matching|
|---|---|---|
|`dir`<br>(extract_features.py)<br>[AP-GeM/DIR](https://github.com/naver/deep-image-retrieval)|`superpoint_aachen`<br>(extract_features.py)<br>[SuperPoint](https://arxiv.org/abs/1712.07629) w/ radius: 3, resize: 1024|`superpoint+lightglue`<br>(match_features.py)<br>[SuperPoint](https://arxiv.org/abs/1712.07629) + [LightGlue](https://github.com/cvg/LightGlue)|
|`netvlad`<br>(extract_features.py)<br>[NetVLAD](https://arxiv.org/abs/1511.07247)|`superpoint_max`<br>(extract_features.py)<br>[SuperPoint](https://arxiv.org/abs/1712.07629) w/ radius: 3, resize: 1600 (forced)|`disk+lightglue`<br>(match_features.py)<br>[DISK](https://arxiv.org/abs/2006.13566) + [LightGlue](https://github.com/cvg/LightGlue)|
|`openibl`<br>(extract_features.py)<br>[OpenIBL](https://github.com/yxgeee/OpenIBL)|`superpoint_inloc`<br>(extract_features.py)<br>[SuperPoint](https://arxiv.org/abs/1712.07629) w/ radius: 4, resize 1600|`superglue`<br>(match_features.py)<br>[SuperGlue](https://arxiv.org/abs/1911.11763) w/ 50 iterations|
|`eigenplaces`<br>(extract_features.py)<br>[EigenPlaces](https://github.com/gmberton/EigenPlaces)|`r2d2`<br>(extract_features.py)<br>[R2D2](https://arxiv.org/abs/1906.06195)|`superglue-fast`<br>(match_features.py)<br>[SuperGlue](https://arxiv.org/abs/1911.11763) w/ 5 iterations|
||`d2net-ss`<br>(extract_features.py)<br>[D2-Net](https://arxiv.org/abs/1905.03561)|`NN-superpoint`<br>(match_features.py)<br>[Nearest Neighbor](https://en.wikipedia.org/wiki/Nearest_neighbor_search) w/ dist. threshold: 0.7 + [SuperPoint](https://arxiv.org/abs/1712.07629)|
||`sift`<br>(extract_features.py)<br>[SIFT](https://www.cs.ubc.ca/~lowe/papers/ijcv04.pdf)|`NN-ratio`<br>(match_features.py)<br>[Nearest Neighbor](https://en.wikipedia.org/wiki/Nearest_neighbor_search) w/ ratio threshold: 0.8|
||`sosnet`<br>(extract_features.py)<br>[SOSNet](https://github.com/scape-research/SOSNet)|`NN-mutual`<br>(match_features.py)<br>[Nearest Neighbor](https://en.wikipedia.org/wiki/Nearest_neighbor_search)|
||`disk`<br>(extract_features.py)<br>[DISK](https://arxiv.org/abs/2006.13566)|`adalam`<br>(match_features.py)<br>[AdaLAM](https://github.com/cavalli1234/AdaLAM)|
|||`loftr`<br>(match_dense.py)<br>[LoFTR](https://github.com/zju3dv/LoFTR) w/ best quality (small scenes only)|
|||`loftr_aachen`<br>(match_dense.py)<br>[LoFTR](https://github.com/zju3dv/LoFTR) w/ limited keypoint detection|
|||`loftr_superpoint`<br>(match_dense.py)<br>[LoFTR](https://github.com/zju3dv/LoFTR) for [SuperPoint](https://arxiv.org/abs/1712.07629) features|

### *Camera Models*

Further reading: https://colmap.github.io/cameras.html

|Model|Parameters|Notes|
|---|---|---|
|`SIMPLE_PINHOLE`|f, cx, cy|No Distortion is assumed. Only focal length and principal point is modeled.|
|`PINHOLE`|fx, fy, cx, cy|No Distortion is assumed. Only focal length and principal point is modeled.|
|`SIMPLE_RADIAL`|f, cx, cy, k|Simple camera model with **one focal length** and **one radial distortion** parameter.|
|`RADIAL`|f, cx, cy, k1, k2|Simple camera model with **one focal length** and **two radial distortion** parameters.|
|`OPENCV`|fx, fy, cx, cy, k1, k2, p1, p2|Based on the pinhole camera model. Additionally models **radial and tangential distortion** (**up to 2nd degree** of coefficients). Not suitable for large radial distortions of fish-eye cameras.|
|`OPENCV_FISHEYE`|fx, fy, cx, cy, k1, k2, k3, k4|Based on the pinhole camera model. Additionally models **radial distortion** (**up to 4th degree** of coefficients). Suitable for large radial distortions of fish-eye cameras.|
|`FULL_OPENCV`|fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, k5, k6|Based on the pinhole camera model. Additionally models **radial and tangential distortion**.|
|`FOV`|fx, fy, cx, cy, omega|Based on the pinhole camera model. Additionally models **radial distortion**. This model is for example used by Project Tango for its **equidistant calibration** type.|
|`SIMPLE_RADIAL_FISHEYE`|f, cx, cy, k|Simple camera model with one focal length and one radial distortion parameter, suitable for fish-eye cameras. This model is **equivalent to the OpenCVFisheyeCameraModel but has only one radial distortion coefficient**.|
|`RADIAL_FISHEYE`|f, cx, cy, k1, k2|Simple camera model with one focal length and two radial distortion parameters, suitable for fish-eye cameras. This model is **equivalent to the OpenCVFisheyeCameraModel but has only two radial distortion coefficients**.|
|`THIN_PRISM_FISHEYE`|fx, fy, cx, cy, k1, k2, p1, p2, k3, k4, sx1, sy1|Camera model with radial and tangential distortion coefficients and **additional coefficients accounting for thin-prism distortion**. Described in "Camera Calibration with Distortion Models and Accuracy Evaluation", J Weng et al., TPAMI, 1992.|

## Troubleshooting

...
