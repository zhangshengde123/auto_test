@echo off
REM 一键运行测试并生成 Allure 报告
REM 前提：已安装 allure 命令行工具（scoop install allure 或下载 allure-commandline）

python -m pytest --alluredir=reports/allure-results
allure generate reports/allure-results -o reports/allure-report --clean

echo.
echo 报告已生成：reports/allure-report/index.html
pause
