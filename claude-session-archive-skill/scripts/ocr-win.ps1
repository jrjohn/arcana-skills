#requires -Version 7.0
<#
.SYNOPSIS
    Windows OCR helper for claude-session-archive v1.15+.
.DESCRIPTION
    Uses Windows.Media.Ocr (built into Windows 10+) to OCR an image file.
    Languages are picked from the system's display-language profile
    (typically zh-Hant + en-US on Taiwan systems).
    Outputs recognized text to stdout. Exit codes:
        0 ok
        1 bad args
        2 file/load fail
        3 OCR engine create failed
        4 OCR failed
.EXAMPLE
    pwsh -File ocr-win.ps1 -Path C:\Users\me\Desktop\screenshot.png
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Path
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Path)) {
    Write-Error "ocr-win: file not found: $Path"
    exit 2
}

# WinRT projection setup
Add-Type -AssemblyName 'System.Runtime.WindowsRuntime'

# Helper to await IAsyncOperation<T> synchronously
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
                   $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

function Await($WinRtOp, $ResultType) {
    $task = $asTaskGeneric.MakeGenericMethod([Type[]]@($ResultType)).Invoke($null, @($WinRtOp))
    $task.Wait() | Out-Null
    return $task.Result
}

# Load WinRT types
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile,           Windows.Storage,           ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,           Windows.Media.Ocr,         ContentType=WindowsRuntime] | Out-Null

# Open file as StorageFile
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path $Path).Path)) ([Windows.Storage.StorageFile])
if ($null -eq $file) {
    Write-Error "ocr-win: cannot open as StorageFile: $Path"
    exit 2
}

# Decode to SoftwareBitmap
$stream  = Await $file.OpenAsync([Windows.Storage.FileAccessMode]::Read) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap  = Await $decoder.GetSoftwareBitmapAsync() ([Windows.Graphics.Imaging.SoftwareBitmap])

# OCR engine — auto-pick user profile languages
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
    Write-Error 'ocr-win: TryCreateFromUserProfileLanguages returned null (no supported language installed)'
    exit 3
}

try {
    $result = Await $engine.RecognizeAsync($bitmap) ([Windows.Media.Ocr.OcrResult])
} catch {
    Write-Error "ocr-win: RecognizeAsync failed: $_"
    exit 4
}

# Output recognized text
[Console]::Out.Write($result.Text)
exit 0
