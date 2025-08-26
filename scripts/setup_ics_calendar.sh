#!/bin/bash

# Grace Irvine ICS Calendar System Setup Script
# ICS日历系统快速设置脚本

set -e  # 遇到错误立即退出

echo "🚀 Grace Irvine ICS日历系统设置"
echo "=================================="

# 检查Python环境
echo "📋 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python"
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python版本: $python_version"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到pip3"
    exit 1
fi

echo "✅ pip3 可用"

# 创建虚拟环境（可选）
read -p "📦 是否创建虚拟环境? (y/n): " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 安装依赖包
echo "📦 安装ICS日历系统依赖包..."
pip3 install icalendar==5.0.11 pytz==2023.3 schedule==1.2.0

# 安装其他必要依赖
if [ -f "requirements.txt" ]; then
    echo "📦 安装其他依赖包..."
    pip3 install -r requirements.txt
else
    echo "⚠️  未找到requirements.txt文件"
fi

# 检查配置文件
echo "📋 检查配置文件..."

# 检查.env文件
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "📝 复制环境变量示例文件..."
        cp env.example .env
        echo "⚠️  请编辑.env文件，设置GOOGLE_SPREADSHEET_ID"
    else
        echo "📝 创建.env文件..."
        cat > .env << EOF
# Google Sheets配置
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here

# 其他配置
DEBUG=false
EOF
        echo "⚠️  请编辑.env文件，设置正确的配置"
    fi
else
    echo "✅ .env文件已存在"
fi

# 检查服务账户文件
if [ ! -f "configs/service_account.json" ]; then
    echo "⚠️  未找到服务账户文件 configs/service_account.json"
    echo "   请从Google Cloud Console下载服务账户密钥文件"
    echo "   并保存为 configs/service_account.json"
else
    echo "✅ 服务账户文件已存在"
fi

# 检查日历配置文件
if [ ! -f "configs/calendar_config.yaml" ]; then
    echo "⚠️  未找到日历配置文件，将创建默认配置"
else
    echo "✅ 日历配置文件已存在"
fi

# 创建输出目录
echo "📁 创建输出目录..."
mkdir -p calendars
mkdir -p logs
echo "✅ 目录创建完成"

# 设置脚本执行权限
echo "🔧 设置脚本执行权限..."
chmod +x scripts/manage_ics_calendar.py
if [ -f "scripts/run_ics_sync.sh" ]; then
    chmod +x scripts/run_ics_sync.sh
fi

# 测试系统
echo "🧪 测试ICS日历系统..."
echo "=================================="

# 检查是否可以导入模块
python3 -c "
try:
    import icalendar
    import pytz
    import schedule
    print('✅ ICS日历依赖包导入成功')
except ImportError as e:
    print(f'❌ 导入错误: {e}')
    exit(1)
"

# 测试配置加载
python3 -c "
import sys
import os
sys.path.append('.')

try:
    from src.ics_manager import ICSManager
    ics_manager = ICSManager()
    print('✅ ICS管理器初始化成功')
except Exception as e:
    print(f'⚠️  ICS管理器初始化警告: {e}')
"

echo ""
echo "🎉 ICS日历系统设置完成！"
echo "=================================="
echo ""
echo "📋 下一步操作："
echo "1. 编辑 .env 文件，设置正确的 GOOGLE_SPREADSHEET_ID"
echo "2. 确保 configs/service_account.json 文件存在且有效"
echo "3. 根据需要调整 configs/calendar_config.yaml 配置"
echo ""
echo "🚀 快速开始："
echo "# 查看系统状态"
echo "python3 scripts/manage_ics_calendar.py status"
echo ""
echo "# 手动同步日历"
echo "python3 scripts/manage_ics_calendar.py sync"
echo ""
echo "# 启动自动同步"
echo "python3 scripts/manage_ics_calendar.py start"
echo ""
echo "📖 详细文档: docs/ICS_CALENDAR_SYSTEM.md"
echo ""

# 提供快速测试选项
read -p "🧪 是否现在运行测试? (y/n): " run_test
if [[ $run_test =~ ^[Yy]$ ]]; then
    echo "🔍 运行系统状态检查..."
    python3 scripts/manage_ics_calendar.py status
fi

echo "✅ 设置完成！"
