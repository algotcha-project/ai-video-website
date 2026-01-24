# Simple Vercel Deployment Script for PowerShell
# This script helps you deploy via Vercel web interface

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Vercel Deployment Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$zipPath = "C:\Users\HDUser\ai-video-website.zip"
$projectPath = "C:\Users\HDUser\ai-video-website"

# Check if zip exists
if (Test-Path $zipPath) {
    Write-Host "✓ ZIP file found: $zipPath" -ForegroundColor Green
} else {
    Write-Host "Creating ZIP file..." -ForegroundColor Yellow
    Compress-Archive -Path "$projectPath\*" -DestinationPath $zipPath -Force
    Write-Host "✓ ZIP file created: $zipPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open https://vercel.com/login in your browser" -ForegroundColor White
Write-Host "2. Click 'Add New...' → 'Project'" -ForegroundColor White
Write-Host "3. Select 'Upload'" -ForegroundColor White
Write-Host "4. Upload this file: $zipPath" -ForegroundColor White
Write-Host "5. Wait 2-3 minutes for deployment" -ForegroundColor White
Write-Host ""
Write-Host "Opening Vercel in browser..." -ForegroundColor Cyan
Start-Process "https://vercel.com/new"

Write-Host ""
Write-Host "ZIP file location: $zipPath" -ForegroundColor Green
Write-Host "You can drag and drop this file to Vercel!" -ForegroundColor Green
