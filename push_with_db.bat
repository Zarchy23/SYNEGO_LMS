@echo off
cd /d C:\Users\Zarchy\synego_lms
echo Adding db.sqlite3...
git add db.sqlite3
echo Committing...
git commit -m "Add SQLite database with initial courses and users"
echo Pushing to remote...
git push origin main
echo Done!
pause
