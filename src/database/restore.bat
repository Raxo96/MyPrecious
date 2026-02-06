@echo off
REM Database restore script for Portfolio Tracker (Windows)

REM Configuration
set BACKUP_DIR=backups
set CONTAINER_NAME=portfolio_tracker_db
set DB_NAME=portfolio_tracker
set DB_USER=postgres

REM Check if backup file is provided
if "%~1"=="" (
    echo ❌ Error: Please provide a backup file name
    echo.
    echo Usage: restore.bat ^<backup_file^>
    echo.
    echo Available backups:
    dir /b "%BACKUP_DIR%\*.sql"
    exit /b 1
)

set BACKUP_FILE=%~1

REM Check if backup file exists
if not exist "%BACKUP_DIR%\%BACKUP_FILE%" (
    echo ❌ Error: Backup file not found: %BACKUP_DIR%\%BACKUP_FILE%
    exit /b 1
)

echo ⚠️  WARNING: This will replace all data in the database!
echo 📁 Backup file: %BACKUP_DIR%\%BACKUP_FILE%
echo.
set /p CONFIRM="Are you sure you want to restore? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo ❌ Restore cancelled
    exit /b 0
)

echo.
echo 🔄 Restoring database from backup...

REM Restore backup using psql
docker exec -i %CONTAINER_NAME% psql -U %DB_USER% -d %DB_NAME% < "%BACKUP_DIR%\%BACKUP_FILE%"

if %errorlevel% equ 0 (
    echo ✅ Database restored successfully!
) else (
    echo ❌ Restore failed!
    exit /b 1
)
