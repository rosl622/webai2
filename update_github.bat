@echo off
echo Updating GitHub Repository...

:: 1. Add all changes
git add .

:: 2. Commit (if there are changes)
git commit -m "Update IT News App: Blue Theme & Layout Fixes"

:: 3. Force Push to overwrite remote with local state
echo Pushing to GitHub (this may overwrite existing history)...
git push -u origin main --force

echo Done!
pause
