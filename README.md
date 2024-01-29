# SfM using COLMAP

This file contains setup and usage information for COLMAP in the context of the LIBRA project.

Documentation for the COLMAP project can be found [here](https://colmap.github.io/index.html).

## Table of Contents

1. [Setup](#setup)
2. [Usage](#usage)
    - [Image Generation](#image-generation)
    - [Application](#application)
    - [Programming API](#programming-api)
3. [Troubleshooting](#troubleshooting)

## Setup

Getting started with COLMAP is very straightforward.

- For **Windows**, you can just download a pre-built binary; see [COLMAP docs: Installation - Pre-built Binaries](https://colmap.github.io/install.html#pre-built-binaries).
- For **Linux**, you must first build from source; see [COLMAP docs: Installation - Build from Source](https://colmap.github.io/install.html#build-from-source).

If you wish to link against the COLMAP API in your code, you *must* build it from source regardless of your operating system.
Follow the instructions in [COLMAP docs: Installation - Library](https://colmap.github.io/install.html#library).

## Usage

### *Image Generation*

Keep the following points in mind when capturing images for SfM generation.

- Use a **fixed focal length**.
- The subject and environment should be **well lit**, but under **indirect lighting**.
- Take pictures of the subject from **as many angles as possible**.
- Avoid **shadows, reflections, and transparent objects**.
- Avoid **moving objects**.
- Avoid **shaky, blurry, or warped** images.

### *Application*

1. Create a project directory and place your images folder inside it.
2. Run COLMAP
    - In **Windows**, simply extract the .zip file containing the pre-built binary and run `COLMAP.bat` (located in the root directory).
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
5. Click "Run"

Processing time increases exponentially based on the number of images, but expect at least **30 minutes** for generating sparse and dense point clouds from **~25 images**.

#### **Full Process**

4. Click "Processing" -> "Feature extraction" to find sparse feature points in each image.
5. Click "Processing" -> "Feature matching" to find correspondences between the feature points in different images.
6. Click "Reconstruction" -> "Start reconstruction" to begin the 3D reconstruction. The viewer (sparse point cloud) will dynamically populate as more images are matched.
7. ...

### *Programming API*

In order to include and link COLMAP in your C++ code, it's best to have a [CMake](https://cmake.org/) project.
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

<br>

# Troubleshooting

...
