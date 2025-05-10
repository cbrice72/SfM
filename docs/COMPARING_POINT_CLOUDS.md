# Comparing Point Clouds using CloudCompare

This document explains how to use [CloudCompare](https://www.danielgm.net/cc/) to compare two point clouds.

- [Alignment Process](#alignment-process)
    - [*Rough Alignment*](#rough-alignment)
    - [*Fine Alignment*](#fine-alignment)
- [Quantitative Comparison](#quantitative-comparison)
- [Creating Visualizations](#creating-visualizations)
    - [*Animations*](#animations)

## Alignment Process

### *Rough Alignment*

1. In the DB Tree tab, select both the to-be-aligned cloud and the reference cloud that will be used as "ground truth".
2. Click "Tools" -> "Registration" -> "Align (point pairs picking)".
3. In the "Entity selector" window, ONLY select the to-be-aligned cloud (click "OK").
4. Manually pick four equivalent point pairs (first pick four points in the to-be-aligned cloud, then pick the matching points in the reference cloud). They don't have to be in the exact same position - close enough is good enough!
    - If the resulting orientation of the to-be-aligned cloud is incorrect, some/all of the selected points may be too similar in terms of the plane they lie on when triangulated. Pick points that vary greatly along every axis/plane.

### *Fine Alignment*

1. In the DB Tree tab, select both the to-be-aligned cloud and the reference cloud that will be used as "ground truth".
2. Click "Tools" -> "Registration" -> "Fine registration (ICP)".
3. You can tell CloudCompare to iterate `n` times, or until the RMS difference is sufficiently small (default: `1.0e-5`). Once you click "OK", alignment will be carried out automatically.

## Quantitative Comparison

1. Click "Tools" -> "Distances" -> "Cloud/Cloud Dist", and ensure that the compared and reference clouds are correct.
2. You can leave the "Octree level" on `AUTO`, although 8 or higher is recommended.
3. The color of the compared cloud will change to a scalar, where BLUE = nearest and RED = furthest. The Console tab will show the mean distance and standard deviation.
    - To better visualize small differences, click on the compared cloud in the DB Tree tab, then in Properties scroll down to "SF display params". Click on the Parameters tab and select "log scale".
4. Click "Tools" -> "Statistics" -> "Compute stat. params (active SF)", and select a `Weibull` distribution.
    - If you want to compare multiple Weibull PDFs, move on to the next step. You should jot down the `a`, `b` and `shift` parameters at the top of the graph. Also, export the graph values to a CSV by clicking the green "CSV" icon on the right of the pop-up graph.
5. Use the MATLAB script `LIBRA_MATLAB/analysis/compare_weibulls.m` to generate a single graph comparing multiple Weibull PDFs. Note that you will need to add filepaths and parameters in the `SETUP` section.

## Creating Visualizations

### *Animations*

1. Orient the camera and set your near and far clipping depth, as desired. Click Ctrl + V to save a viewport (repeat this step as many times as you'd like).
    - Ctrl + Mouse wheel: adjust Near Clipping Depth
    - Ctrl + Shift + Mouse wheel: adjust Far Clipping Depth
2. Select all viewports and click "Plugins" -> "Animation".
3. Specify your animation duration (optionally: duration of steps between viewports), frame rate, and bitrate. For the latter two, >= 30 fps and 100,000 kbps are recommended (the plugin will compress the file size anyways).
4. Click "Render" (do NOT click "OK", as this won't create the animation!). To ensure CloudCompare has enough computational power to process it, it's recommended that you don't do anything in the background until it's done.
