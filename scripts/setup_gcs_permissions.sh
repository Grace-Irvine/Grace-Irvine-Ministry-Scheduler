#!/bin/bash
# GCS 权限设置脚本
# Setup GCS permissions for service account

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="ai-for-god"
DATA_BUCKET="grace-irvine-ministry-data"
ICS_BUCKET="grace-irvine-ministry-scheduler"
SERVICE_ACCOUNT_FILE="configs/service_account.json"

echo "=========================================="
echo "🔐 GCS 权限设置"
echo "=========================================="
echo ""

# 检查服务账号文件
if [ ! -f "$SERVICE_ACCOUNT_FILE" ]; then
    echo -e "${RED}❌ 服务账号文件不存在: $SERVICE_ACCOUNT_FILE${NC}"
    echo ""
    echo "💡 请先创建服务账号文件:"
    echo "   1. 在 GCP Console 创建服务账号"
    echo "   2. 下载服务账号密钥 JSON 文件"
    echo "   3. 保存到 $SERVICE_ACCOUNT_FILE"
    exit 1
fi

# 获取服务账号邮箱
SERVICE_ACCOUNT_EMAIL=$(cat "$SERVICE_ACCOUNT_FILE" | jq -r '.client_email')

if [ -z "$SERVICE_ACCOUNT_EMAIL" ] || [ "$SERVICE_ACCOUNT_EMAIL" == "null" ]; then
    echo -e "${RED}❌ 无法从服务账号文件读取邮箱${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 服务账号: $SERVICE_ACCOUNT_EMAIL${NC}"
echo ""

# 设置数据源 bucket 权限
echo "=========================================="
echo "📊 设置数据源 Bucket 权限"
echo "=========================================="
echo ""

echo "🔄 授予 Storage Object Viewer 权限..."
if gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:roles/storage.objectViewer gs://$DATA_BUCKET; then
    echo -e "${GREEN}✅ 成功授予 Storage Object Viewer 权限${NC}"
else
    echo -e "${RED}❌ 授予权限失败${NC}"
    exit 1
fi

echo ""
echo "🔄 授予 Storage Legacy Bucket Reader 权限..."
if gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:roles/storage.legacyBucketReader gs://$DATA_BUCKET; then
    echo -e "${GREEN}✅ 成功授予 Storage Legacy Bucket Reader 权限${NC}"
else
    echo -e "${YELLOW}⚠️  授予 Storage Legacy Bucket Reader 权限失败（可选权限）${NC}"
fi

echo ""

# 设置 ICS 存储 bucket 权限
echo "=========================================="
echo "📅 设置 ICS 存储 Bucket 权限"
echo "=========================================="
echo ""

echo "🔄 授予 Storage Object Creator 权限..."
if gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:roles/storage.objectCreator gs://$ICS_BUCKET; then
    echo -e "${GREEN}✅ 成功授予 Storage Object Creator 权限${NC}"
else
    echo -e "${RED}❌ 授予权限失败${NC}"
    exit 1
fi

echo ""
echo "🔄 授予 Storage Object Viewer 权限..."
if gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:roles/storage.objectViewer gs://$ICS_BUCKET; then
    echo -e "${GREEN}✅ 成功授予 Storage Object Viewer 权限${NC}"
else
    echo -e "${RED}❌ 授予权限失败${NC}"
    exit 1
fi

echo ""

# 验证权限
echo "=========================================="
echo "✅ 验证权限"
echo "=========================================="
echo ""

echo "🔄 运行权限测试..."
if python3 scripts/test_gcs_permissions.py; then
    echo ""
    echo -e "${GREEN}✅ 权限设置完成！${NC}"
    echo ""
    echo "💡 现在可以运行以下命令生成 ICS 文件:"
    echo "   python3 scripts/generate_local_ics.py"
else
    echo ""
    echo -e "${YELLOW}⚠️  权限测试失败，请检查权限设置${NC}"
    exit 1
fi

