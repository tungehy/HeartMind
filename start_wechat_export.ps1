# 启动微信导出服务（WeChatDataAnalysis），供 HeartMind「微信自动导出」调用。
# 用法：右键用 PowerShell 运行，或在终端执行 .\start_wechat_export.ps1
#
# 前置（已完成过一次即可，之后直接运行本脚本）：
#   1) cd WeChatDataAnalysis-main; uv sync   # 如网络超时，先设置镜像：
#      $env:UV_PYTHON_INSTALL_MIRROR="https://registry.npmmirror.com/-/binary/python-build-standalone"
#      $env:UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
#   2) 原生运行时已缓存到 %LOCALAPPDATA%\WeChatDataAnalysis\source-native-core
#      （若重装/失效，以管理员网络跑：
#        node -e "require('./desktop/src/source-native-core-bootstrap.cjs').ensureSourceNativeCore({env: process.env})"）

$ErrorActionPreference = "Stop"
$wcda = Join-Path $PSScriptRoot "WeChatDataAnalysis-main"

# 原生运行时（native core）：自动发现缓存目录中最新的一份
$cacheRoot = Join-Path $env:LOCALAPPDATA "WeChatDataAnalysis\source-native-core"
$nativeDir = Get-ChildItem $cacheRoot -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    ForEach-Object { Join-Path $_.FullName "native-core" } |
    Where-Object { Test-Path (Join-Path $_ "wechatdb_client.dll") } |
    Select-Object -First 1
if (-not $nativeDir) {
    Write-Error "未找到原生运行时缓存，请先按脚本头部注释第 2 条下载。"
}
$env:WCE_NATIVE_CORE_SOURCE_DIR = $nativeDir

Write-Host "使用原生运行时: $nativeDir"
Write-Host "启动 WeChatDataAnalysis API (http://127.0.0.1:10392) ..." -ForegroundColor Cyan
Write-Host "提示：首次导出前需在网页端完成密钥获取/数据库解密（微信需登录运行）。" -ForegroundColor DarkGray

Set-Location $wcda
uv run main.py
