@echo off
REM Grace Irvine Ministry Scheduler - Email Notifications (Windows)
REM 用于发送邮件通知的批处理脚本

echo ========================================
echo Grace Irvine 事工管理系统 - 邮件通知
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 切换到项目根目录
cd /d "%~dp0\.."

REM 显示菜单
echo 请选择要执行的操作:
echo   1. 发送周三确认通知
echo   2. 发送周六提醒通知
echo   3. 发送所有通知
echo   4. 测试模式（显示但不发送）
echo   5. 退出
echo.

set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" (
    echo.
    echo 正在发送周三确认通知...
    python scripts/send_email_notifications.py weekly
) else if "%choice%"=="2" (
    echo.
    echo 正在发送周六提醒通知...
    python scripts/send_email_notifications.py sunday
) else if "%choice%"=="3" (
    echo.
    echo 正在发送所有通知...
    python scripts/send_email_notifications.py all
) else if "%choice%"=="4" (
    echo.
    echo 测试模式 - 显示通知内容但不发送...
    python scripts/send_email_notifications.py test
) else if "%choice%"=="5" (
    echo 退出程序
    exit /b 0
) else (
    echo 无效的选项: %choice%
)

echo.
echo ========================================
echo 操作完成
echo ========================================
pause
