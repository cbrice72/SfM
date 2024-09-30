# Ease-of-use function for running rs-convert.exe
function Run-RSConvert {
    param (
        [string]$outDirs,
        [string]$inBag
    )

    Write-Host "<< Running rs-convert.exe with inputs: -p $outDirs and -i $inBag >>"
    .\rs-convert.exe -p $outDirs -i $inBag
}

# Array of -p and -i argument pairs (must use full paths)
$outDirs = @(
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\out_png\baseline\",
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\out_png\dark\",
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\out_png\light_0\",
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\out_png\light_45\",
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\out_png\light_90\"
)

$inBag = @(
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\baseline.bag",
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\dark.bag",
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\light_0.bag",
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\light_45.bag",
    "C:\Users\brice\Desktop\Projects\LIBRA\Software\SfM\scripts\light_90.bag"
)

# Run rs-convert.exe on each input arg pair
for ($i = 0; $i -lt $outDirs.Length; $i++) {
    Run-RSConvert -p $outDirs[$i] -i $inBag[$i]
}

Write-Host "<< All runs finished! >>"
