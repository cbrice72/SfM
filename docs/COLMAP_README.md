# Using COLMAP

This file contains setup and usage information for COLMAP in the context of the LIBRA project.

Documentation for the COLMAP project can be found [here](https://colmap.github.io/index.html).

## Table of Contents

1. [Setup](#setup)
2. [Terminology](#terminology)
3. [Usage](#usage)
    - [Generating Images](#generating-images)
    - [GUI Application](#gui-application)
    - [Command-line Application](#command-line-application)
    - [C++ Programming API](#c-programming-api)
4. [Tips](#tips)
5. [Troubleshooting](#troubleshooting)

## Setup

Getting started with COLMAP is very straightforward.

- For **Windows**, you can just download a pre-built binary; see [COLMAP docs: Installation - Pre-built Binaries](https://colmap.github.io/install.html#pre-built-binaries).
- For **Linux**, you must first build from source; see [COLMAP docs: Installation - Build from Source](https://colmap.github.io/install.html#build-from-source).
    - At the time of writing (2024-01-30), the instructions in this document relate solely to Windows.

If you wish to link against the COLMAP API in your code, you *must* build it from source regardless of your operating system.
Follow the instructions in [COLMAP docs: Installation - Library](https://colmap.github.io/install.html#library).

## Terminology

- **Shared Intrinsics**: the property of images which refer to the same camera. In COLMAP, this is specified by the `camera_id` property in the databse.

## Usage

### *Generating Images*

Keep the following points in mind when capturing images for SfM generation.

- Use a **fixed focal length**
- The subject and environment should be **well lit**, but under **indirect lighting**
- Take pictures of the subject from **as many angles as possible**
- Avoid **shadows, reflections, and transparent objects**
- Avoid **moving objects**
- Avoid **shaky, blurry, or warped** images

### *GUI Application*

1. Create a project directory and place your images folder inside it.
2. Run COLMAP.
    - In **Windows**, simply extract the .zip file containing the pre-built binary and run `COLMAP.bat` (located in the root directory)
    - In **Linux**, ...
3. Create a new project via "File" -> "New Project".
    - For "Database", select "New" and save it in your project directory (just call it `database`)
    - For "Images", select your images folder
    - Click "Save" to instantiate your project
    - Press Ctrl+S to actually save your project config file (just call it `project`)

Your project directory should now look similar to this.
```txt
|- images/
|   |- 0.jpg
|   |- 1.jpg
|   |- ...
|- database.db
|- project.ini
```

#### **Quickest Method**

4. Click "Reconstruction" -> "Automatic reconstruction".
    - For "Workspace folder", select your project folder
    - For "Image folder", select your images folder
    - Check options related to your dataset, such as "Data type" or "Shared intrinsics"
5. Click "Run".

#### **Full Process**

4. Extract features by clicking "Processing" -> "Feature extraction". This finds sparse feature points in each image.
5. Match features by clicking "Processing" -> "Feature matching". This finds correspondences between the feature points in different images. To increase matches, see [Tips/Feature Matching](#feature-matching).
6. Run the sparse reconstruction by clicking "Reconstruction" -> "Start reconstruction". The viewer will dynamically populate with points as more images are matched.
    - To save your progress, export the resulting model to a folder in your workspace (e.g., `$WS_PATH/sparse/0/`)
7. Bring up the dense reconstruction window by clicking "Reconstruction" -> "Dense reconstruction".
    - Click "Select" to specify the workspace directory (e.g., `$WS_PATH/dense/0/`)
    - Click "Undistortion" to initialize the dense reconstruction workspace
    - Click "Stereo" to carry out dense reconstruction; **this can take anywhere from 15 minutes to a few hours**
    - Click "Fusion" to fuse the results into a colored point cloud; this concludes the dense reconstruction process
8. Run the Poisson mesher from the dense reconstruction window by clicking "Poisson".
9. Run the Delaunay mesher from the dense reconstruction window by clicking "Delaunay".

### *Command-line Application*

1. Create a project directory and place your images folder inside it.
2. Open a terminal/PowerShell instance and navigate to the directory where you extracted the ZIP file from [Setup](#setup). There should be a file named `COLMAP.bat`.
3. Set the following environment variable for ease of use in later commands.
    ```bash
    $Env:WS_PATH = "[path/to/workspace/folder]"
    ```

#### **Quickest Method**

4. Simply run the automatic reconstruction. (TODO: untested)
    ```bash
    .\COLMAP.bat automatic_reconstructor `
        --workspace_path $Env:WS_PATH `
        --image_path $Env:WS_PATH/images
    ```

#### **Full Process**

4. Extract features.
    ```bash
    .\COLMAP.bat feature_extractor `
        --database_path $Env:WS_PATH/database.db `
        --image_path $Env:WS_PATH/images
    ```

5. Match features.
    ```bash
    .\COLMAP.bat exhaustive_matcher `
        --database_path $Env:WS_PATH/database.db
    ```

6. Run the sparse reconstruction.
    ```bash
    mkdir $Env:WS_PATH/sparse
    
    .\COLMAP.bat mapper `
        --database_path $Env:WS_PATH/database.db `
        --image_path $Env:WS_PATH/images `
        --output_path $Env:WS_PATH/sparse
    ```

7. Run the dense reconstruction. (TODO: untested)
    ```bash
    mkdir $DATASET_PATH/dense
    
    .\COLMAP.bat image_undistorter `
        --image_path $Env:WS_PATH/images `
        --input_path $Env:WS_PATH/sparse/0 `
        --output_path $Env:WS_PATH/dense `
        --output_type COLMAP `                    # optional
        --max_image_size 2000                     # optional
    
    .\COLMAP.bat patch_match_stereo `
        --workspace_path $Env:WS_PATH/dense `
        --workspace_format COLMAP `               # optional
        --PatchMatchStereo.geom_consistency true  # optional
    
    .\COLMAP.bat stereo_fusion `
        --workspace_path $Env:WS_PATH/dense `
        --output_path $Env:WS_PATH/dense/fused.ply `
        --workspace_format COLMAP `               # optional
        --input_type geometric                    # optional
    ```

8. [OPTIONAL] Run the Poisson mesher.
    ```bash
    TODO
    ```

9. [OPTIONAL] Run the Delaunay mesher.
    ```bash
    TODO
    ```

### *C++ Programming API*

#### **Building COLMAP from Source**

First, ensure you have the CUDA toolkit/compiler installed on your system. If you're not sure, download it from [here](https://developer.nvidia.com/cuda-downloads).

Before linking against COLMAP, you must first [build it from source](https://colmap.github.io/install.html#build-from-source). Note that if you are on Ubuntu 22.04, you will need to implement some workarounds.

- There is a problem when compiling with Ubuntu's default CUDA package and GCC, so you must compile against GCC 10.
    ```bash
    # There is a problem when compiling with Ubuntu 22.04's default CUDA package and GCC; implement a workaround
    sudo apt-get install gcc-10 g++-10
    export CC=/usr/bin/gcc-10
    export CXX=/usr/bin/g++-10
    export CUDAHOSTCXX=/usr/bin/g++-10
    # Run CMake against COLMAP's sources and build
    cmake .. -GNinja -DCMAKE_CUDA_ARCHITECTURES=75
    ninja
    sudo ninja install
    ```

- During compilation, the Boost library may throw an error about deprecated `Bind` placeholder useage. This must be manually fixed in `src/colmap/exe/sfm.cc` by adding the following lines under the last `#include`.
    ```cpp
    #include <boost/bind/bind.hpp>
    
    using namespace boost::placeholders;
    ```

- If you are getting an error about CUDA architecture (specifically that `compute_native` isn't recognized), ensure there are no versions of the CUDA toolkit older than 12.3 installed on your system. See [this GitHub issue thread](https://github.com/ggerganov/llama.cpp/issues/1940) for more information.

#### **Using COLMAP in C++**

In order to include and link against COLMAP in your C++ code, it's best to have a [CMake](https://cmake.org/) project; you may use the one located at `src/tools/exmaple.cc` of the [COLMAP source](https://github.com/colmap/colmap).

You'll need to know the following paths.

- Headers: `${CMAKE_INSTALL_PREFIX}/include/colmap`
- Libraries: `${CMAKE_INSTALL_PREFIX}/lib/colmap`
- CMake config: `${CMAKE_INSTALL_PREFIX}/share/colmap`

A sample `CMakeLists.txt` and `hello_world.cpp` are reproduced below from the COLMAP docs, for your convenience.

#### **CMakeLists.txt**

```cmake
cmake_minimum_required(VERSION 3.10)

project(SampleProject)

find_package(colmap REQUIRED)
# or to require a specific version: find_package(colmap 3.4 REQUIRED)

add_executable(hello_world hello_world.cpp)
target_link_libraries(hello_world colmap::colmap)
```

#### **hello_world.cpp**

```cpp
#include <cstdlib>
#include <iostream>

#include <colmap/controllers/option_manager.h>
#include <colmap/util/string.h>

int main(int argc, char** argv) {
    // Initialize COLMAP (via its global logger)
    colmap::InitializeGlog(argv);

    // Parse the user-input command line arguments
    std::string message;
    colmap::OptionManager options;
    options.AddRequiredOption("message", &message);
    options.Parse(argc, argv);

    // Output "Hello" + the message typed by the user
    std::cout << colmap::StringPrintf("Hello %s!", message.c_str()) << std::endl;

    return EXIT_SUCCESS;
}
```

## Tips

### *Feature Extraction*

- Ensure you are using the most applicable camera model (in GUI: directly under "Camera model", e.g., `SIMPLE_RADIAL`, `SIMPLE_PINHOLE`, etc.).
- Use the options `--SiftExtraction.estimate_affine_shape=true` and `--SiftExtraction.domain_size_pooling=true`.

### *Feature Matching*

- Enable "Guided Feature Matching" (in GUI: `guided_matching` under "General Options").

### *Reconstruction*

- Geo-registration is possible by providing the 3D centers of a camera for three or more images. The coordinates can be either cartesian (`x y z`) or GPS (`lat lon alt`); note that if you use GPS coordinates you will have to specify additional conversion settings (see [this FAQ post](https://colmap.github.io/faq.html#geo-registration)).
    ```txt
    image_name1.jpg X1 Y1 Z1
    image_name2.jpg X2 Y2 Z2
    image_name3.jpg X3 Y3 Z3
    ...
    ```

#### **Sparse Reconstruction**

- TODO ("Shared intrinsics"? "Image type"?).
- Use known camera poses if you have them (see [this FAQ post](https://colmap.github.io/faq.html#reconstruct-sparse-dense-model-from-known-camera-poses)).
    - If you're confused about the format of `cameras.txt` and `images.txt`, check out the [Text Format](https://colmap.github.io/format.html#text-format) section of the wiki.
    - Note: if your known camera instrinsics have large distortion coefficients, you must copy the parameters from your `cameras.txt` to the project database using `scripts/python/database.py`.

#### **Dense Reconstruction**

- ...

## Troubleshooting

### *Feature Matching*

If you encounter either of the following error messages, it means your GPU has run out of memory during the matching process.
```bash
# GUI
ERROR: Feature matching failed. This probably caused by insufficient GPU
memory. Consider reducing the maximum number of features.
# Command-line
MultiplyDescriptor: an illegal memory access was encountered
```

The maximum required GPU memory can be approximated using this formula:
```txt
(4 * num_matches^2) + (4 * num_matches * 256)
```
For example, if you set `--SiftMatching.max_num_matches 10000`, the maximum required GPU memory will be around 400MB, which are only allocated if one of your images actually has that many features.

### *Dense Reconstruction*

If the dense point cloud contains **too many outliers** and **too much noise**, try increasing the value of the `--StereoFusion.min_num_pixels` option.

#### **Poisson-specific**

If the reconstructed surface mesh model **contains no surface** or there are **too many outlier surfaces**, try reducing the value of the `--PoissonMeshing.trim` option.

#### **Delaunay-specific**

If the reconstructed surface mesh model contains **surfaces which are too noisy or incomplete**, try increasing the `--DelaunayMeshing.quality_regularization` parameter.

If the **resolution of the mesh is too coarse**, try reducing the `--DelaunayMeshing.max_proj_dist` option.

#### **Improving reconstruction speed**

Note that the following changes might degrade the quality of the dense reconstruction. The only change that will improve reconstruction speed without sacrificing quality is upgrading your hardware.

- Disable geometric dense stereo reconstruction via `--PatchMatchStereo.geom_consistency false`; note that you must enable `--PatchMatchStereo.filter true` in this case
- Reduce the maximum image resolution via `--PatchMatchStereo.max_image_size` and `--StereoFusion.max_image_size`
- Reduce the number of source images per reference image to be considered (see [Reducing memory usage](#reducing-memory-usage))
- Increase the patch window step `--PatchMatchStereo.window_step` to 2
- Reduce the patch window radius via `--PatchMatchStereo.window_radius`
- Reduce the number of patch match iterations via `--PatchMatchStereo.num_iterations`
- Reduce the number of sampled views via `--PatchMatchStereo.num_samples`
- For very large reconstructions, use CMVS to partition your scene into multiple clusters and prune redundant images (see [this FAQ post](https://colmap.github.io/faq.html#faq-dense-memory))

#### **Reducing memory usage**

In your GPU (VRAM)...

- Reduce the maximum image size via `--PatchMatchStereo.max_image_size`
- Reduce the number of source images in the `stereo/patch-match.cfg` file from e.g., `__auto__, 30` to `__auto__, 10`
- Disable geometric dense stereo reconstruction via `--PatchMatchStereo.geom_consistency false`; note that you must enable `--PatchMatchStereo.filter true` in this case

In your CPU (RAM)...

- Reduce the patch match cache size via `PatchMatchStereo.cache_size` (specified in GB); note that too low a value might lead to a slower processing time and heavy load on the hard disk
- Reduce the maximum image size via `--PatchMatchStereo.max_image_size` or `--StereoFusion.max_image_size`
