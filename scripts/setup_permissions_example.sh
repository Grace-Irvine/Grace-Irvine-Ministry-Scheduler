#!/bin/bash
# GCS 权限设置示例脚本
# 使用实际的服务账号邮箱设置权限

set -e

# 服务账号邮箱（从 service_account.json 读取）
SERVICE_ACCOUNT_EMAIL="scheduler-service@ai-for-god.iam.gserviceaccount.com"

# Bucket 名称
DATA_BUCKET="grace-irvine-ministry-data"
ICS_BUCKET="grace-irvine-ministry-scheduler"

echo "=========================================="
echo "🔐 设置 GCS 权限"
echo "=========================================="
echo ""
echo "📧 服务账号: $SERVICE_ACCOUNT_EMAIL"
echo ""

# 设置数据源 bucket 权限
echo "=========================================="
echo "📊 设置数据源 Bucket 权限"
echo "=========================================="
echo ""

echo "🔄 授予 Storage Object Viewer 权限..."
gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:roles/storage.objectViewer gs://$DATA_BUCKET

echo "🔄 授予 Storage Legacy Bucket Reader 权限..."
gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:roles/storage.legacyBucketReader gs://$DATA_BUCKET

echo ""
echo "✅ 数据源 bucket 权限设置完成"
echo ""

# 设置 ICS 存储 bucket 权限
echo "=========================================="
echo "📅 设置 ICS 存储 Bucket 权限"
echo "=========================================="
echo ""

echo "🔄 授予 Storage Object Creator 权限..."
gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:roles/storage.objectCreator gs://$ICS_BUCKET

echo "🔄 授予 Storage Object Viewer 权限..."
gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:roles/storage.objectViewer gs://$ICS_BUCKET

echo ""
echo "✅ ICS 存储 bucket 权限设置完成"
echo ""

# 验证权限
echo "=========================================="
echo "✅ 验证权限"
echo "=========================================="
echo ""

echo "🔄 运行权限测试..."
python3 scripts/test_gcs_permissions.py

echo ""
echo "✅ 权限设置完成！"
echo ""
echo "💡 现在可以运行以下命令生成 ICS 文件:"
echo "   python3 scripts/generate_local_ics.py"

