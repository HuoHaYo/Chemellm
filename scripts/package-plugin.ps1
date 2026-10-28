# Assemble a deployable plugin bundle with its portable runtime.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\package-plugin.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$plugin = Join-Path $root "dsh-chemellm"
$runtime = Join-Path $plugin "runtime"
$dist = Join-Path $root "dist"
$target = Join-Path $dist "dsh-chemellm"

if (-not (Test-Path (Join-Path $runtime "python\python.exe"))) {
    throw "runtime/python/python.exe missing; build the portable runtime first"
}
if (-not (Test-Path (Join-Path $runtime "kernel\server.py"))) {
    throw "runtime/kernel/server.py missing"
}
if (-not (Test-Path (Join-Path $runtime "app\documents.py"))) {
    throw "runtime/app/documents.py missing"
}
if (-not (Test-Path (Join-Path $runtime "site-packages\fastapi"))) {
    throw "runtime/site-packages incomplete (fastapi missing)"
}

if (Test-Path $target) { Remove-Item $target -Recurse -Force }
New-Item -ItemType Directory -Force -Path $target | Out-Null

# plugin code
Copy-Item (Join-Path $plugin "index.js") $target
Copy-Item (Join-Path $plugin "client.js") $target
Copy-Item (Join-Path $plugin "icon.svg") $target
Copy-Item (Join-Path $plugin "cordis.patch.yml") $target
Copy-Item (Join-Path $plugin "package.json") $target
Copy-Item (Join-Path $plugin "README.md") $target

# runtime (excluding caches)
$rc = Start-Process robocopy -ArgumentList $runtime, (Join-Path $target "runtime"), "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/XD", "__pycache__", ".pytest_cache" -Wait -PassThru
if ($rc.ExitCode -ge 8) { throw "robocopy runtime failed: $($rc.ExitCode)" }

# checksums
$lines = Get-ChildItem $target -Recurse -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | ForEach-Object {
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    $rel = $_.FullName.Substring($target.Length + 1).Replace('\', '/')
    "$hash  $rel"
}
$lines | Set-Content -Path (Join-Path $target "SHA256SUMS.txt") -Encoding UTF8

# zip
$zip = Join-Path $dist ("dsh-chemellm-" + (Get-Date -Format "yyyyMMdd") + "-win-x64.zip")
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $target -DestinationPath $zip -CompressionLevel Optimal
$size = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "plugin bundle: $zip ($size MB)"
Write-Host "contents: $((Get-ChildItem $target -Recurse -File | Measure-Object).Count) files"
