# SfM Scripts used by the LIBRA Project

TODO

TODO

Project link: [https://github.com/christian-brice/SfM](https://github.com/christian-brice/SfM)

## Table of Contents

1. [Requirements・要件](#requirements・要件)
2. [Usage・使い方](#usage・使い方)
3. [Documentation・説明書](#documentation・説明書)
4. [About Us・メンバー](#about-us・メンバー)
5. [Contributing・Gitとの連携](#contributing・gitとの連携)
6. [Troubleshooting・トラブルシューティング](#troubleshooting・トラブルシューティング)

## Requirements・要件

### *OS & Software*

| | Minimum | Recommended |
|---|---|---|
| **Operating System** | Ubuntu 22.04<br>(Jammy package base) | Ubuntu 22.04<br>(Jammy package base) |
| **Python 3** | 3.8.0 | >= 3.10.0 |

### *Setup*

Overall, you should follow the instructions in [HLOC_README.md](../docs/HLOC_README.md).
When installing COLMAP and PyCOLMAP from source, refer to the [COLMAP_README.md](../docs/COLMAP_README.md) for installation notes.

## Usage・使い方

`hloc_sfm.py` is the main script. To run the demo, enter the following in a terminal.

```bash
python3 hloc_sfm.py -i mikan --use-defaults
```

> **_NOTE:_** the input argument `mikan` is a shortcut. You can add your own shortcuts by appending new map entries to the global variable `input_shortcuts`.

### *extract_frames.py・ビデオから連続画像を抽出する*

|Input|Output|
|---|---|
|Video file<br>(`.mp4`, `.avi`, `.mov`, etc.)|`images/` folder wth frames<br>(same directory as input)|
|Desired capture interval<br>(lower = more frames)||

```bash
# See help text for detailed explanation of usage and available options.
python3 extract_frames.py -h
```

### *hloc_sfm.py・メインSfMパイプライン*

|Input|Output (in `outputs/`)|
|---|---| 
|Folder containing images|COLMAP model (`sfm_*/`)
||2D visualizations (`.pdf`)<br>(point depth, tracklength, visibility)|
||3D sparse reconstruction (`.ply`)|
||3D sparse model turntable (`.gif`)|
||3D dense reconstruction (`.ply`)|
||Feature extraction & matching databases (`.h5`)|
||Script execution summary (`summary-*.txt`)|

```bash
# See help text for detailed explanation of usage and available options.
python3 hloc_sfm.py -h
```

### *make_turntable.py・3Dモデルの回転GIFを作る*

|Input|Output|
|---|---|
|`.ply` file|`.gif` file<br>(same directory as input)|

```bash
# See help text for detailed explanation of usage and available options.
python3 make_turntable.py -h
```

## Documentation・説明書

See [INDEX.md](../INDEX.md) in the project root directory for a list of related SfM documentation.

## About Us・メンバー

**Christian Brice** ([email](mailto:brice.c.aa@m.titech.ac.jp)) is a doctoral student in mechanical engineering at the Tokyo Institute of Technology.
The *LIBRA-II* project is the focus of his doctoral studies.

The **[Gen Endo Laboratory](www.robotics.mech.e.titech.ac.jp/gendo/en/)** is affiliated with the Department of Mechanical Engineering at the Tokyo Institute of Technology.

## Contributing・Gitとの連携

### *Giving proxy access to Git・Gitにプロキシアクセス*

If you'd like to pull/push to this repo from within a proxy, you must first add your proxy settings to Git.
Enter the following command in a terminal (replacing the text in brackets).
```bash
git config --global http.proxy <address>:<port>
```

### *Accessing the Code・コードへのアクセス*

You can clone the repo either via a terminal or VS Code.
If you're a beginner at Git, I recommend downloading VS Code and using its integrated "Source Control" tab.

In VS Code, press `Ctrl+Shift+P` to open the VS Code command prompt. Select "git clone", then copy/paste the following URL into the popup.
```txt
https://github.com/christian-brice/SfM.git
```

<br>

# Troubleshooting・トラブルシューティング

...
