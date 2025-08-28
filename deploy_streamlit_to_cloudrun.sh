#!/bin/bash
"""
Deploy Grace Irvine Ministry Scheduler Streamlit App to Cloud Run
将 Streamlit Web 应用部署到 Google Cloud Run
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
REGION="us-central1"  # 选择离你最近的区域
SERVICE_NAME="grace-irvine-scheduler"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
SERVICE_ACCOUNT_EMAIL="scheduler-service@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${BLUE}🚀 开始部署 Streamlit 应用到 Google Cloud Run${NC}"
echo "======================================================================"

# 1. 检查 gcloud CLI 是否已安装
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ 错误: Google Cloud CLI 未安装${NC}"
    echo "请访问 https://cloud.google.com/sdk/docs/install 安装 gcloud CLI"
    exit 1
fi

# 2. 检查 Docker 是否已安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker 未安装${NC}"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

# 3. 设置项目
echo -e "${BLUE}📋 设置项目: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# 4. 启用必需的API
echo -e "${BLUE}🔧 启用必需的API服务${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 5. 配置 Docker 认证
echo -e "${BLUE}🔑 配置 Docker 认证${NC}"
gcloud auth configure-docker

# 6. 构建 Docker 镜像
echo -e "${BLUE}🏗️  构建 Docker 镜像${NC}"
echo "镜像名称: ${IMAGE_NAME}"

# 使用 Cloud Build 构建镜像（推荐，更快更可靠）
gcloud builds submit --tag ${IMAGE_NAME} .

# 7. 部署到 Cloud Run
echo -e "${BLUE}☁️  部署到 Cloud Run${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --service-account=${SERVICE_ACCOUNT_EMAIL} \
    --memory=1Gi \
    --cpu=1 \
    --timeout=3600 \
    --concurrency=80 \
    --max-instances=10 \
    --set-env-vars="STREAMLIT_SERVER_HEADLESS=true,STREAMLIT_SERVER_ENABLE_CORS=false,STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false" \
    --port=8080

# 8. 获取服务URL
echo -e "${BLUE}🔗 获取服务访问URL${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "======================================================================"
echo -e "${BLUE}📋 部署摘要:${NC}"
echo -e "  项目ID: ${PROJECT_ID}"
echo -e "  区域: ${REGION}"
echo -e "  服务名称: ${SERVICE_NAME}"
echo -e "  镜像: ${IMAGE_NAME}"
echo -e "  服务URL: ${SERVICE_URL}"
echo ""
echo -e "${YELLOW}⚠️  重要提醒:${NC}"
echo "1. 确保 .env 文件中的环境变量已通过 Secret Manager 配置"
echo "2. 服务账号已具有必要的权限"
echo "3. 首次访问可能需要几秒钟启动时间"
echo ""
echo -e "${BLUE}🎯 访问应用:${NC}"
echo "  ${SERVICE_URL}"
echo ""
echo -e "${BLUE}📚 管理命令:${NC}"
echo "  查看服务: gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
echo "  查看日志: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}"
echo "  更新服务: gcloud run services update ${SERVICE_NAME} --region=${REGION}"
echo "  删除服务: gcloud run services delete ${SERVICE_NAME} --region=${REGION}"
