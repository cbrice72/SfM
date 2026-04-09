# Using DarkFeat

This file contains setup and usage information for `DarkFeat`, a noise-robust feature detector and descriptor for extremely low-light RAW images.

Source code and documentation for the DarkFeat project can be found [here](https://github.com/THU-LYJ-Lab/DarkFeat).

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Setup](#setup)
    - [*Prerequisites*](#prerequisites)
    - [*DarkFeat*](#darkfeat)
- [Usage](#usage)
    - [*Demo*](#demo)
    - [*Custom Dataset*](#custom-dataset)
- [Tips](#tips)
    - [*API Usage*](#api-usage)
- [Troubleshooting](#troubleshooting)

## Setup

### *Prerequisites*

| Requirements | |
| --- | --- |
| [GitHub](https://github.com/THU-LYJ-Lab/DarkFeat) | commit `6a9790b` |
| Python | 3.10.12 |
| PyTorch | 2.2.1 (built for cuda 12.1) |
| Cuda | 12.3 |

| Components | | |
| --- | --- | --- |
| GL3D | gl3d_imgs | 1000x1000 undistorted images of GL3D |

Before building `DarkFeat`, you must first install [the appropriate PyTorch for your system](https://pytorch.org/get-started/locally/). You can check your installed CUDA Compute Platform version by running `nvidia-smi` (the required `nvcc` package can be installed via `sudo apt install nvidia-cuda-toolkit`).

### *DarkFeat*

1. Install the DarkFeat repo.

    ```bash
    git clone https://github.com/THU-LYJ-Lab/DarkFeat.git
    cd DarkFeat
    pip install -r requirements.txt
    ```

2. Download and extract the [sample raw image sequences and pretrained weights](https://drive.google.com/drive/folders/1zkUCsBVEmQcPZPhsEUymA5GIvAzi12hD?usp=sharing) to the DarkFeat directory.
    - Note: you should have four image sequence folders (`seq-0[1-4]`) and one pretrained weights file (`DarkFeat.pth`)

## Usage

### *Demo*

Basic usage is shown in the DarkFeat `README.md`. The following is a copy/paste-able command for sequence 1 of the samples downloaded in step 2 above.

```bash
python ./demo_darkfeat.py \
    --input seq-01/ \
    --output_dir ./output \
    --resize 960 640 \
    --model_path DarkFeat.pth
```

The matched pictures (with # of matches in the top left) in the `output/` directory can be opened with any photo viewing software.

### *Custom Dataset*

#### **Training from Scratch**

The following is a more granular, step-by-step explanation based on the instructions in the DarkFeat `README.md` "Training from scratch" section.

1. Clone the GL3D repository and navigate to it.

    ```bash
    git clone https://github.com/lzx551402/GL3D.git
    cd GL3D
    ```

2. Download the [GL3D dataset](https://1drv.ms/u/s!Anl8gFgW1C7LknxGy1gesj30SQ1I?e=RTT6re) (see GL3D `README.md` "Downloads" section) and extract it into the `data/` directory.

TODO

The GL3D hyperparameters (in the `configs/` directory) can be configured as follows:

- TODO

## Tips

### *API Usage*

| Script | Input | Output |
| --- | --- | --- |
| darkfeat.py | TODO | TODO |
| raw_preprocess.py | `--H`: Image height (default: 640)<br>`--W`: Image width (default: 960)<br>`--histeq`: Enable/disable histogram equalization<br>`--dataset_dir`: Path to dataset directory (default: `/data/hyz/MID/`) | Preprocessed images ready for feature extraction. |
| export_features.py | `--H`: Image height (default: 640)<br>`--W`: Image width (default: 960)<br>`--histeq`: Enable/disable histogram equalization<br>`--model_path`: Path to pretrained weights<br>`--dataset_dir`: Path to dataset directory (default: `/data/hyz/MID/`) | TODO |
| pose_estimation.py | `--histeq`: Enable/disable histogram equalization<br>`--dataset_dir`: Path to dataset directory (default: `/data/hyz/MID/`) | TODO |
| read_error.py | (none; must be run after `pose_estimation.py`) | TODO |
|  |  |  |

## Troubleshooting

...
