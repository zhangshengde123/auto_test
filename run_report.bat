@echo off
REM One-click run tests and generate Allure report
REM Prerequisite: allure commandline tool installed (scoop install allure)

cd /d "%~dp0"

.venv\Scripts\python.exe -m pytest --alluredir=reports/allure-results --clean-alluredir
allure generate reports/allure-results -o reports/allure-report --clean

echo.
echo Report generated: reports/allure-report/index.html
pause
