#!/bin/bash

# Ease-of-use function for running hloc_sfm.py
run_hloc_sfm() {
    input_dir="$1"
    echo "<< Running hloc_sfm with input: $input_dir >>"
    ./hloc_sfm.py -i "$input_dir" --use-defaults
}

# Array of input directories
input_dirs=(
    "/out_png/baseline/"
    "/out_png/dark/"
    "/out_png/light_0"
    "/out_png/light_45"
    "/out_png/light_90"
)

# Run hloc_sfm.py on each input directory
for dir in "${input_dirs[@]}"; do
    run_hloc_sfm "$dir"
done

echo "<< All runs finished! >>"