@echo off
REM Database backup script for Portfolio Tracker (Windows)

REM Configuration
set BACKUP_DIR=backups
set CONTAINER_NAME=portfolio_tracker_db
set DB_NAME=portfolio_tracker
set DB_USER=postgres

REM Create timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set BACKUP_FILE=portfolio_tracker_backup_%TIMESTAMP%.sql

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo 🔄 Creating database backup...
echo 📁 Backup location: %BACKUP_DIR%\%BACKUP_FILE%

REM Create backup using pg_dump
docker exec -t %CONTAINER_NAME% pg_dump -U %DB_USER% -d %DB_NAME% --clean --if-exists > "%BACKUP_DIR%\%BACKUP_FILE%"

if %errorlevel% equ 0 (
    echo ✅ Backup created successfully!
    for %%A in ("%BACKUP_DIR%\%BACKUP_FILE%") do echo 📊 Backup size: %%~zA bytes
    echo.
    echo To restore this backup, run:
    echo   docker exec -i %CONTAINER_NAME% psql -U %DB_USER% -d %DB_NAME% ^< %BACKUP_DIR%\%BACKUP_FILE%
) else (
    echo ❌ Backup failed!
    exit /b 1
)
