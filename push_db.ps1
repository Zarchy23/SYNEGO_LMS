# Git push script for SQLite database
Set-Location "C:\Users\Zarchy\synego_lms"

Write-Host "Step 1: Adding db.sqlite3..." -ForegroundColor Cyan
git add db.sqlite3

Write-Host "Step 2: Committing..." -ForegroundColor Cyan
git commit -m "Add SQLite database with initial courses and users"

Write-Host "Step 3: Pushing to remote..." -ForegroundColor Cyan
git push origin main

Write-Host "Complete!" -ForegroundColor Green
