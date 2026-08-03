$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$outDir = Join-Path $PSScriptRoot "submission"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$zipPath = Join-Path $outDir "xiaopeng-travel-agent-code.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

$staging = Join-Path $env:TEMP ("xp-agent-pack-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $staging | Out-Null

$excludeDirs = @(".venv", ".git", "submission", "__pycache__", ".cursor")
$excludeFiles = @(".env", ".env.local")

Get-ChildItem -Force | ForEach-Object {
  if ($_.PSIsContainer) {
    if ($excludeDirs -contains $_.Name) { return }
    Copy-Item $_.FullName -Destination (Join-Path $staging $_.Name) -Recurse -Force
  } else {
    if ($excludeFiles -contains $_.Name) { return }
    Copy-Item $_.FullName -Destination (Join-Path $staging $_.Name) -Force
  }
}

Get-ChildItem $staging -Recurse -Filter ".env" -Force -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem $staging -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zipPath -Force
Remove-Item $staging -Recurse -Force

$docs = @(
  "STAR_final.md",
  "forum_post.md",
  "tech_report.md",
  "tech_report_print.html",
  "demo_results.md",
  "_demo_results.json",
  "next_steps.md",
  "demo_script.md",
  "qoder_checklist.md",
  "提交清单.md",
  "论坛发帖正文.md",
  "你的下一步.md"
)
foreach ($name in $docs) {
  $src = Join-Path $PSScriptRoot ("docs\" + $name)
  if (Test-Path $src) {
    Copy-Item $src (Join-Path $outDir $name) -Force
  }
}

$printScript = Join-Path $PSScriptRoot "scripts\make_print_html.py"
if (Test-Path $printScript) {
  $py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
  if (-not (Test-Path $py)) { $py = "python" }
  & $py $printScript | Out-Host
}

Write-Host "OK: $zipPath"
Write-Host "Docs copied to submission/"
Write-Host "Open docs/tech_report_print.html -> Ctrl+P -> Save as PDF (<=10 pages)."
Write-Host "Checklist: docs/提交清单.md"
