# Package current sources with the portable Python dependencies. Never copy a
# runtime wholesale: it may contain local projects, snapshots, or old sources.
param(
    [string]$RuntimeDirectory = '',
    [switch]$SkipArchive,
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$plugin = Join-Path $root 'dsh-chemellm'
$runtime = if ($RuntimeDirectory) { [IO.Path]::GetFullPath($RuntimeDirectory) } else { Join-Path $plugin 'runtime' }
$dist = [IO.Path]::GetFullPath((Join-Path $root 'dist'))
$target = [IO.Path]::GetFullPath((Join-Path $dist 'dsh-chemellm'))
if ($runtime.StartsWith($target + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'RuntimeDirectory cannot be inside the staging directory that will be replaced'
}
$manifest = Get-Content -LiteralPath (Join-Path $plugin 'package.json') -Raw -Encoding UTF8 | ConvertFrom-Json
# npm always includes package.json implicitly; a directory bundle must do so too.
$pluginFiles = @('package.json') + @($manifest.files)

foreach ($required in @('python\python.exe', 'site-packages\fastapi', 'requirements.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $runtime $required))) { throw "Portable runtime missing: $required" }
}
foreach ($entry in $pluginFiles) {
    if ($entry -eq 'runtime') { continue }
    if (-not (Test-Path -LiteralPath (Join-Path $plugin $entry))) { throw "Plugin source missing: $entry" }
}
foreach ($entry in @('kernel\server.py', 'old\app\documents.py')) {
    if (-not (Test-Path -LiteralPath (Join-Path $root $entry))) { throw "Kernel source missing: $entry" }
}
if ($ValidateOnly) {
    Write-Host 'Package inputs valid: package.json files + runtime/python + runtime/site-packages + current kernel/ and old/app/.'
    return
}

# Verify the exact resolved staging directory before replacing it.
if ((Split-Path -Parent $target) -ne $dist -or (Split-Path -Leaf $target) -ne 'dsh-chemellm') {
    throw "Unexpected staging path: $target"
}
if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
New-Item -ItemType Directory -Force -Path $target | Out-Null

foreach ($entry in $pluginFiles) {
    if ($entry -ne 'runtime') { Copy-Item -LiteralPath (Join-Path $plugin $entry) -Destination $target -Recurse }
}

function Copy-RuntimeTree([string]$Source, [string]$Destination) {
    & robocopy $Source $Destination /E /XJ /NFL /NDL /NJH /NJS /NP /XD __pycache__ .pytest_cache /XF *.pyc *.pyo > $null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE): $Source" }
}
$targetRuntime = Join-Path $target 'runtime'
Copy-RuntimeTree (Join-Path $runtime 'python') (Join-Path $targetRuntime 'python')
Copy-RuntimeTree (Join-Path $runtime 'site-packages') (Join-Path $targetRuntime 'site-packages')
Copy-RuntimeTree (Join-Path $root 'kernel') (Join-Path $targetRuntime 'kernel')
Copy-RuntimeTree (Join-Path $root 'old\app') (Join-Path $targetRuntime 'app')
Copy-Item -LiteralPath (Join-Path $runtime 'requirements.txt') -Destination $targetRuntime

$lines = Get-ChildItem -LiteralPath $target -Recurse -File | Sort-Object FullName | ForEach-Object {
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    $relative = $_.FullName.Substring($target.Length + 1).Replace('\', '/')
    "$hash  $relative"
}
$lines | Set-Content -LiteralPath (Join-Path $target 'SHA256SUMS.txt') -Encoding UTF8
Write-Host "Staged plugin: $target ($($lines.Count) files)"
if (-not $SkipArchive) {
    $zip = Join-Path $dist ("dsh-chemellm-" + (Get-Date -Format 'yyyyMMdd') + '-win-x64.zip')
    Compress-Archive -LiteralPath $target -DestinationPath $zip -CompressionLevel Optimal -Force
    Write-Host "Plugin bundle: $zip"
}
