# SfM Scripts used by the LIBRA Project

A collection of scripts and documentation written for Structure-from-Motion (SfM) endeavors related to the LIBRA project.

Project link: [https://github.com/christian-brice/SfM](https://github.com/christian-brice/SfM)

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Requirements](#requirements)
    - [*OS \& Software*](#os--software)
    - [*Setup*](#setup)
- [Usage](#usage)
    - [*combine\_frames.py*](#combine_framespy)
    - [*extract\_frames\_rosbag.py*](#extract_frames_rosbagpy)
    - [*extract\_frames\_video.py*](#extract_frames_videopy)
    - [*hloc\_sfm.py*](#hloc_sfmpy)
    - [*make\_turntable.py*](#make_turntablepy)
    - [*multirun\_script.py*](#multirun_scriptpy)
    - [*realsense\_video\_writer.py*](#realsense_video_writerpy)
    - [*samples\_frames.py*](#samples_framespy)
- [Third-party Apps](#third-party-apps)
    - [*rs-convert*](#rs-convert)
    - [*CloudCompare*](#cloudcompare)
- [Documentation](#documentation)
- [About Us](#about-us)
- [Contributing](#contributing)
    - [*Giving proxy access to Git*](#giving-proxy-access-to-git)
    - [*Accessing the Code*](#accessing-the-code)
- [Troubleshooting](#troubleshooting)

## Requirements

### *OS & Software*

| | Minimum | Recommended |
| --- | --- | --- |
| **Operating System** | Ubuntu 22.04<br>(Jammy package base) | Ubuntu 22.04<br>(Jammy package base) |
| **Python 3** | 3.8.0 | >= 3.10.0 |

### *Setup*

Overall, you should follow the instructions in [HLOC_README.md](../docs/HLOC_README.md). When installing COLMAP and PyCOLMAP from source, refer to the [COLMAP_README.md](../docs/COLMAP_README.md) for installation notes.

For RealSense-related software, you must first install the [Intel RealSense SDK 2.0](https://www.intelrealsense.com/sdk-2/).

## Usage

[hloc_sfm.py](#hloc_sfmpy) is the main script. To run the demo, enter the following in a terminal.

```bash
python3 hloc_sfm.py -i mikan --use-defaults
```

> ***NOTE:*** the input argument `mikan` is a shortcut. You can add your own shortcuts by appending new map entries to the global variable `input_shortcuts`.

<br>

### *combine_frames.py*

Combine sequential frames into a video.

| Input | Output |
| --- | --- |
| Folder containing images | `*_combined.mp4` video file |

```bash
# See help text for detailed explanation of usage and available options
python3 combine_frames.py -h
```

<br>

### *extract_frames_rosbag.py*

Extract frames from a ROS2-bag at a certain interval.

| Input | Output |
| --- | --- |
| Path to rosbag (directory) | `images/` folder wth frames<br>(same directory as input) |
| Image topic<br>(e.g., `/camera/color/image_raw`) | |

```bash
# See help text for detailed explanation of usage and available options
python3 extract_frames_rosbag.py -h
```

<br>

### *extract_frames_video.py*

Extract frames from a video at a certain interval.

| Input | Output |
| --- | --- |
| Video file<br>(`.mp4`, `.avi`, `.mov`, etc.) | `images/` folder wth frames<br>(same directory as input) |
| Desired capture interval<br>(lower = more frames) | |

```bash
# See help text for detailed explanation of usage and available options
python3 extract_frames_video.py -h
```

<br>

### *hloc_sfm.py*

LIBRA project SfM pipeline using hloc.

| Input | Output (in `outputs/`) |
| --- | --- |
| Folder containing images | COLMAP model (`sfm_*/`) |
| | 2D visualizations (`.pdf`)<br>(point depth, tracklength, visibility) |
| | 3D sparse reconstruction (`.ply`) |
| | 3D sparse model turntable (`.gif`) |
| | 3D dense reconstruction (`.ply`) |
| | Feature extraction & matching databases (`.h5`) |
| | Script execution summary (`summary-*.txt`) |

```bash
# See help text for detailed explanation of usage and available options
python3 hloc_sfm.py -h
```

<br>

### *make_turntable.py*

Creates a turntable-like GIF of a 3D model (`.ply`).

| Input | Output |
| --- | --- |
| `.ply` 3D data file | `.gif` animation<br>(same directory as input) |

```bash
# See help text for detailed explanation of usage and available options
python3 make_turntable.py -h
```

<br>

### *multirun_script.py*

Run a given Python script multiple times with fixed or iterative args.
The script and command-line arguments are hard-coded in this file to
improve management of options for larger iterations (see `shortcuts`).

| Input | Output |
| --- | --- |
| None<br>(user is prompted to<br>select a shortcut) | Depends on script |

```bash
# See help text for detailed explanation of usage and available options
python3 multirun_script.py -h
```

<br>

### *realsense_video_writer.py*

Extracts RGB and depth videos from rosbags created using Intel RealSense D4xx cameras.

> **NOTE:** will not work on WSL2 (although I only tested on WSL2, I feel like it should work on regular Linux/Ubuntu, e.g., in a VM). See [rs-convert](#rs-convert) for an alternative.

| Input | Output (in `outputs/`) |
| --- | --- |
| Rosbag (`.bag`) | Color video file (`*_rgb.avi`) |
| | TODO (`*_depth.avi`) |

```bash
# See help text for detailed explanation of usage and available options
python3 realsense_video_extractor.py -h
```

<br>

### *samples_frames.py*

Sample images in a directory at a set interval. This is essentially the same logic as `extract_frames.py`, except it works with images that have already been extracted from a rosbag.

| Input | Output |
| --- | --- |
| Folder containing images | `images/` folder wth frames<br>(same directory as input) |
| Desired capture interval<br>(lower = more frames) | |

```bash
# See help text for detailed explanation of usage and available options
python3 sample_frames.py -h
```

<br><hr>

## Third-party Apps

### *rs-convert*

Converts the rosbag (`.bag`) file output by the Intel RealSense Viewer into various filetypes (PNG, CSV, RAW, PLY, BIN, txt).

For more information, see the project [on GitHub](https://github.com/IntelRealSense/librealsense/tree/master/tools/convert).

On Windows:

```powershell
# The executable isn't in PATH, so move to its directory
cd "C:\Program Files (x86)\Intel RealSense SDK 2.0\tools"
# Run the converter, outputting all RGB and depth frames
.\rs-convert.exe -p C:\path\to\your\image\output\folder\ -i C:\path\to\your\ros.bag
```

<br>

### *CloudCompare*

3D point cloud processing software for comparing two or more dense 3D points clouds.

For the project page, including downloads, see the [website](https://www.danielgm.net/cc/). The wiki can be found [here](https://www.cloudcompare.org/doc/wiki/index.php/Main_Page).

<br><hr>

## Documentation

See [INDEX.md](../INDEX.md) in the project root directory for a list of related SfM documentation.

## About Us

**Christian Brice** ([email](mailto:brice.c.67b9@m.isct.ac.jp)) is a doctoral student in mechanical engineering at the Tokyo Institute of Technology. The *LIBRA* project is the focus of his doctoral studies.

The **[Gen Endo Laboratory](www.robotics.mech.e.titech.ac.jp/gendo/en/)** is affiliated with the Department of Mechanical Engineering at the Tokyo Institute of Technology.

## Contributing

### *Giving proxy access to Git*

If you'd like to pull/push to this repo from within a proxy, you must first add your proxy settings to Git. Enter the following command in a terminal (replacing the text in brackets).

```bash
git config --global http.proxy <address>:<port>
```

### *Accessing the Code*

You can clone the repo either via a terminal or VS Code. If you're a beginner at Git, I recommend downloading VS Code and using its integrated "Source Control" tab.

In VS Code, press `Ctrl+Shift+P` to open the VS Code command prompt. Select "git clone", then copy/paste the following URL into the popup.

```txt
https://github.com/christian-brice/SfM.git
```

<br>

## Troubleshooting

...
