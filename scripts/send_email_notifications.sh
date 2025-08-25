#!/bin/bash
# Grace Irvine Ministry Scheduler - Email Notifications (Linux/Mac)
# 用于发送邮件通知的Shell脚本

echo "========================================"
echo "Grace Irvine 事工管理系统 - 邮件通知"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8或更高版本"
    exit 1
fi

# 切换到项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# 显示菜单
echo "请选择要执行的操作:"
echo "  1. 发送周三确认通知"
echo "  2. 发送周六提醒通知"
echo "  3. 发送所有通知"
echo "  4. 测试模式（显示但不发送）"
echo "  5. 退出"
echo

read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo
        echo "正在发送周三确认通知..."
        python3 scripts/send_email_notifications.py weekly
        ;;
    2)
        echo
        echo "正在发送周六提醒通知..."
        python3 scripts/send_email_notifications.py sunday
        ;;
    3)
        echo
        echo "正在发送所有通知..."
        python3 scripts/send_email_notifications.py all
        ;;
    4)
        echo
        echo "测试模式 - 显示通知内容但不发送..."
        python3 scripts/send_email_notifications.py test
        ;;
    5)
        echo "退出程序"
        exit 0
        ;;
    *)
        echo "无效的选项: $choice"
        exit 1
        ;;
esac

echo
echo "========================================"
echo "操作完成"
echo "========================================"
