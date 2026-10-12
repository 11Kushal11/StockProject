@echo off
REM Wrapper to run the stockanalysis main script using the project's venv
SETLOCAL
SET SCRIPT_DIR=%~dp0
SET PYTHON_EXE=%SCRIPT_DIR%venv\Scripts\python.exe
IF NOT EXIST "%PYTHON_EXE%" (
  REM Fallback to system python
  SET PYTHON_EXE=python
)

REM Ensure logs directory exists
SET LOG_DIR=%SCRIPT_DIR%logs
IF NOT EXIST "%LOG_DIR%" MKDIR "%LOG_DIR%"

REM Create timestamp using PowerShell for reliable formatting
FOR /F "usebackq tokens=*" %%T IN (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"`) DO SET TIMESTAMP=%%T
SET LOGFILE=%LOG_DIR%\run_%TIMESTAMP%.log

echo Running main.py, logging to %LOGFILE%
"%PYTHON_EXE%" "%SCRIPT_DIR%main.py" > "%LOGFILE%" 2>&1
SET RC=%ERRORLEVEL%
echo Finished with exit code %RC% >> "%LOGFILE%"
echo Log saved: %LOGFILE%
ENDLOCAL
EXIT /B %RC%
