@echo off
set /p msg="Enter commit message (Press Enter for default 'Update'): "
if "%msg%"=="" set msg="Update IT News App"

echo.
echo Updating GitHub Repository...
git add .
git commit -m "%msg%"

echo.
echo Pushing to GitHub...
git push origin main --force

echo.
echo Done! Streamlit Cloud will detect this change and update in 1-2 minutes.
pause
