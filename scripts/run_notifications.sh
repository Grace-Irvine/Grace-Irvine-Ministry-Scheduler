#!/bin/bash

# Grace Irvine Ministry Scheduler - macOS/Linux 脚本
# 用于生成微信群通知

echo "================================================"
echo "Grace Irvine Ministry Scheduler"
echo "================================================"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3，请先安装 Python 3.8+"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d ".venv" ]; then
    echo "🔧 正在创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖包
echo "📦 安装/更新依赖包..."
pip install -r simple_requirements.txt

echo ""
echo "选择要生成的通知类型:"
echo "1. 周三确认通知"
echo "2. 周六提醒通知"
echo "3. 月度总览通知"
echo "4. 生成所有通知"
echo "5. 数据验证"
echo ""

read -p "请输入选择 (1-5): " choice

case $choice in
    1)
        python src/notification_generator.py weekly
        ;;
    2)
        python src/notification_generator.py sunday
        ;;
    3)
        python src/notification_generator.py monthly
        ;;
    4)
        python src/notification_generator.py all
        ;;
    5)
        python src/data_validator.py
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 完成!"
