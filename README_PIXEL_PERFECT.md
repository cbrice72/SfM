# Using Pixel Perfect SfM

This file contains setup and usage information for `pixsfm`, a Python package that can be used with [COLMAP](https://colmap.github.io/) and [HLOC](https://github.com/cvg/Hierarchical-Localization/).

Source code and documentation for the Pixel Perfect SfM project can be found [here](https://github.com/cvg/pixel-perfect-sfm).

## Table of Contents

1. [Setup](#setup)
2. [Usage](#usage)
    - [Command-line Application](#command-line-application)
    - [C++ Programming API](#c-programming-api)
3. [Tips](#tips)
4. [Troubleshooting](#troubleshooting)

## Setup

Before building `pixsfm`, you must first [build COLMAP **3.8** from source](https://colmap.github.io/install.html#build-from-source) (get COLMAP 3.8 [here](https://github.com/colmap/colmap/releases/tag/3.8)). Note that if you are on Ubuntu 22.04, you will need to [implement some workarounds](README_COLMAP.md#building-colmap-from-source).

Follow the instructions in the `pixsfm` `README.md`. At the `pip install -r requirements.txt` step, you may have to do the following.

- The `Eigen` package does not set up a default symbolic link. You must create one in order for libraries that use Eigen to reference its header files.
```bash
sudo ln -s /usr/include/eigen3/Eigen/ /usr/include/Eigen
```

## Usage

### *Command-line Application*

...

### *C++ Programming API*

...

## Tips

...

## Troubleshooting

...
