# HeartMind 一键启动（后端 + 前端）
# 用法：右键“使用 PowerShell 运行”，或在终端执行  .\start.ps1

$root = $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "首次运行，正在创建 Python 虚拟环境并安装依赖…" -ForegroundColor Cyan
    python -m venv (Join-Path $root ".venv")
    & $py -m pip install -r (Join-Path $root "backend\requirements.txt")
}

# 首次启动若库为空则播种演示数据
$dbFile = Join-Path $root "backend\heartmind.db"
if (-not (Test-Path $dbFile)) {
    Write-Host "初始化演示数据…" -ForegroundColor Cyan
    Push-Location (Join-Path $root "backend"); & $py seed.py; Pop-Location
}

Write-Host "启动后端  http://127.0.0.1:8000  (API 文档 /docs)" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\backend'; & '$py' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

Write-Host "启动前端  http://127.0.0.1:3000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\frontend'; `$env:PORT='3000'; npm run dev"

Start-Sleep -Seconds 8
Start-Process "http://127.0.0.1:3000"
