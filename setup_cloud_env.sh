#!/bin/bash
# 云端环境变量设置脚本
# Cloud Environment Variables Setup Script

echo "🌐 设置云端存储环境变量..."

# 获取当前脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 设置环境变量
export GOOGLE_APPLICATION_CREDENTIALS="${SCRIPT_DIR}/configs/service_account.json"
export GCP_STORAGE_BUCKET="grace-irvine-ministry-scheduler"
export GOOGLE_CLOUD_PROJECT="ai-for-god"
export STORAGE_MODE="cloud"

echo "✅ 环境变量设置完成："
echo "  GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}"
echo "  GCP_STORAGE_BUCKET=${GCP_STORAGE_BUCKET}"
echo "  GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}"
echo "  STORAGE_MODE=${STORAGE_MODE}"
echo ""

# 验证配置
echo "🧪 验证配置..."
if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ 服务账户文件存在"
else
    echo "❌ 服务账户文件不存在: $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

# 测试GCP连接（可选）
if command -v python3 &> /dev/null; then
    echo "🔗 测试GCP连接..."
    python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from src.cloud_storage_manager import get_storage_manager
try:
    manager = get_storage_manager()
    if manager.storage_client:
        print('✅ GCP连接成功')
    else:
        print('❌ GCP连接失败')
except Exception as e:
    print(f'❌ 测试失败: {e}')
"
fi

echo ""
echo "🚀 现在可以启动应用了："
echo "  python3 start.py"
echo ""
echo "💡 或者运行测试："
echo "  python3 test_gcp_upload.py"
