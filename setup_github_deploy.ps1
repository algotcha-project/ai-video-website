# GitHub + Vercel Deployment Setup
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub + Vercel Deployment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "C:\Users\HDUser\ai-video-website"
$repoName = "ai-video-website"

Write-Host "Project path: $projectPath" -ForegroundColor White
Write-Host ""

# Check if git is available
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if ($gitCmd) {
    Write-Host "✓ Git is available" -ForegroundColor Green
    Write-Host ""
    Write-Host "Setting up Git repository..." -ForegroundColor Yellow
    
    Set-Location $projectPath
    
    # Initialize git if not already
    if (-not (Test-Path ".git")) {
        git init
        Write-Host "✓ Git repository initialized" -ForegroundColor Green
    }
    
    # Add all files
    git add .
    Write-Host "✓ Files staged" -ForegroundColor Green
    
    # Create initial commit
    git commit -m "Initial commit: AI Video website" 2>&1 | Out-Null
    Write-Host "✓ Initial commit created" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Next steps to deploy:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Create a new repository on GitHub:" -ForegroundColor White
    Write-Host "   https://github.com/new" -ForegroundColor Cyan
    Write-Host "   Repository name: $repoName" -ForegroundColor White
    Write-Host ""
    Write-Host "2. After creating the repo, connect it:" -ForegroundColor White
    Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/$repoName.git" -ForegroundColor Cyan
    Write-Host "   git branch -M main" -ForegroundColor Cyan
    Write-Host "   git push -u origin main" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. Then go to Vercel and import the repository" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Opening GitHub and Vercel..." -ForegroundColor Cyan
    Start-Process "https://github.com/new"
    Start-Sleep -Seconds 2
    Start-Process "https://vercel.com/new"
} else {
    Write-Host "✗ Git is not available" -ForegroundColor Red
    Write-Host ""
    Write-Host "Using ZIP upload method instead..." -ForegroundColor Yellow
    Write-Host ""
    
    # Create ZIP if not exists
    $zipPath = "C:\Users\HDUser\ai-video-website.zip"
    if (-not (Test-Path $zipPath)) {
        Write-Host "Creating ZIP file..." -ForegroundColor Yellow
        Compress-Archive -Path "$projectPath\*" -DestinationPath $zipPath -Force
    }
    
    Write-Host "✓ ZIP file ready: $zipPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Go to https://vercel.com/new" -ForegroundColor White
    Write-Host "2. Click 'Upload'" -ForegroundColor White
    Write-Host "3. Upload the ZIP file" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Opening Vercel..." -ForegroundColor Cyan
    Start-Process "https://vercel.com/new"
}
