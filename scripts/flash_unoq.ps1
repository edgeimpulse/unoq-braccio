param(
    [string]$Port = "COM3",
    [string]$Fqbn = "arduino:avr:uno"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path "$PSScriptRoot\.."
$SketchDir = Join-Path $RepoRoot "firmware\unoq_braccio_firmware"

arduino-cli lib install Braccio
arduino-cli compile --fqbn $Fqbn $SketchDir
arduino-cli upload -p $Port --fqbn $Fqbn $SketchDir
