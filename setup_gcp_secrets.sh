#!/bin/bash
"""
Google Cloud Secret Manager 配置脚本
Setup environment variables in Google Cloud Secret Manager
"""

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_ID="ai-for-god"  # 使用现有项目

echo -e "${BLUE}🔐 配置 Google Cloud Secret Manager${NC}"
echo "======================================================================"

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ 错误: .env 文件不存在${NC}"
    echo "请先创建 .env 文件并配置必要的环境变量"
    exit 1
fi

# 读取 .env 文件
source .env

echo -e "${BLUE}📋 从 .env 文件读取配置并创建 secrets${NC}"

# 创建 secrets
echo -e "${YELLOW}🔑 创建 GOOGLE_SPREADSHEET_ID secret${NC}"
echo -n "${GOOGLE_SPREADSHEET_ID}" | gcloud secrets create google-spreadsheet-id \
    --data-file=- \
    --project=${PROJECT_ID} || echo "Secret 可能已存在，跳过创建"

echo -e "${YELLOW}📧 创建 SENDER_EMAIL secret${NC}"
echo -n "${SENDER_EMAIL:-jonathanjing@graceirvine.org}" | gcloud secrets create sender-email \
    --data-file=- \
    --project=${PROJECT_ID} || echo "Secret 可能已存在，跳过创建"

echo -e "${YELLOW}👤 创建 SENDER_NAME secret${NC}"
echo -n "${SENDER_NAME:-Grace Irvine 事工协调}" | gcloud secrets create sender-name \
    --data-file=- \
    --project=${PROJECT_ID} || echo "Secret 可能已存在，跳过创建"

echo -e "${YELLOW}🔒 创建 EMAIL_PASSWORD secret${NC}"
echo -n "${EMAIL_PASSWORD}" | gcloud secrets create email-password \
    --data-file=- \
    --project=${PROJECT_ID} || echo "Secret 可能已存在，跳过创建"

echo -e "${YELLOW}📮 创建 RECIPIENT_EMAILS secret${NC}"
echo -n "${RECIPIENT_EMAILS}" | gcloud secrets create recipient-emails \
    --data-file=- \
    --project=${PROJECT_ID} || echo "Secret 可能已存在，跳过创建"

# 如果有 Google Service Account Key，也创建对应的 secret
if [ -f "configs/service_account.json" ]; then
    echo -e "${YELLOW}🔐 创建 GOOGLE_SERVICE_ACCOUNT_KEY secret${NC}"
    gcloud secrets create google-service-account-key \
        --data-file=configs/service_account.json \
        --project=${PROJECT_ID} || echo "Secret 可能已存在，跳过创建"
fi

echo ""
echo -e "${GREEN}✅ Secret Manager 配置完成！${NC}"
echo "======================================================================"
echo -e "${BLUE}📋 创建的 secrets:${NC}"
echo "  - google-spreadsheet-id"
echo "  - sender-email"
echo "  - sender-name"
echo "  - email-password"
echo "  - recipient-emails"
if [ -f "configs/service_account.json" ]; then
    echo "  - google-service-account-key"
fi

echo ""
echo -e "${BLUE}🔍 查看 secrets:${NC}"
echo "  gcloud secrets list --project=${PROJECT_ID}"
echo ""
echo -e "${BLUE}📝 更新 secrets (如果需要):${NC}"
echo "  echo 'new_value' | gcloud secrets versions add secret-name --data-file=-"
