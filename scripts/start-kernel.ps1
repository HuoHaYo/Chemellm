# ChemELLM local workspace — 启动脚本
# 用法：./scripts/start-kernel.ps1            （默认 127.0.0.1:8765）
#       ./scripts/start-kernel.ps1 -Port 8765
param(
  [int]$Port = 8765
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
  throw "未找到 .venv Python：$python。请先创建虚拟环境并安装依赖（见 README.md）。"
}

$env:CHEMELLM_KERNEL_PORT = "$Port"
$env:CHEMELLM_KERNEL_HOST = '127.0.0.1'
if (-not $env:CHEMELLM_DATA_DIR) {
  $env:CHEMELLM_DATA_DIR = Join-Path $root 'data\kernel'
}

Write-Host "ChemELLM local kernel -> http://127.0.0.1:$Port"
Write-Host "data dir: $env:CHEMELLM_DATA_DIR（Ctrl+C 停止）"

Push-Location $root
try {
  & $python -X utf8 'kernel\server.py'
} finally {
  Pop-Location
}
