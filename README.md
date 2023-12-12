# SfM using COLMAP

This file contains setup and usage information for COLMAP in the context of the LIBRA project.

Documentation for the COLMAP project can be found [here](https://colmap.github.io/index.html).

## Table of Contents

1. [Setup](#setup)
2. [Usage](#usage)
3. [Troubleshooting](#troubleshooting)

## Setup

Getting started with COLMAP is very straightforward.

- For Windows, you can just download a pre-built binary; see [COLMAP docs: Installation - Pre-built Binaries](https://colmap.github.io/install.html#pre-built-binaries).
- For Linux, you must first build from source; see [COLMAP docs: Installation - Build from Source](https://colmap.github.io/install.html#build-from-source).

If you wish to link against the COLMAP API in your code, you *must* build it from source regardless of your operating system.
Follow the instructions in [COLMAP docs: Installation - Library](https://colmap.github.io/install.html#library).

## Usage

### *Application*

- In Windows, simply extract the .zip file containing the pre-built binary and run `COLMAP.bat` (located in the root directory).
- In Linux, ...?

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
    colmap::InitializeGlog(argv);

    std::string message;
    colmap::OptionManager options;
    options.AddRequiredOption("message", &message);
    options.Parse(argc, argv);

    std::cout << colmap::StringPrintf("Hello %s!", message.c_str()) << std::endl;

    return EXIT_SUCCESS;
}
```

<br>

# Troubleshooting

...
