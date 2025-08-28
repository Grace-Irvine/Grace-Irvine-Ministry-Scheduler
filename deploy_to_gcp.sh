#!/bin/bash
"""
Google Cloud Platform 部署脚本
Deploy Grace Irvine Ministry Scheduler to Google Cloud
包含 Cloud Functions 和 Cloud Run 部署
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
SERVICE_NAME="grace-irvine-scheduler"  # Cloud Run 服务名称
SERVICE_ACCOUNT_EMAIL="scheduler-service@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${BLUE}🚀 开始部署 Grace Irvine Ministry Scheduler 到 Google Cloud${NC}"
echo "======================================================================"

# 1. 检查 gcloud CLI 是否已安装
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ 错误: Google Cloud CLI 未安装${NC}"
    echo "请访问 https://cloud.google.com/sdk/docs/install 安装 gcloud CLI"
    exit 1
fi

# 2. 检查是否已登录
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  请先登录 Google Cloud${NC}"
    gcloud auth login
fi

# 3. 设置项目
echo -e "${BLUE}📋 设置项目: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# 4. 启用必需的API
echo -e "${BLUE}🔧 启用必需的API服务${NC}"
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable gmail.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 5. 创建服务账号（如果不存在）
echo -e "${BLUE}👤 创建服务账号${NC}"
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} &> /dev/null; then
    gcloud iam service-accounts create scheduler-service \
        --display-name="Grace Irvine Scheduler Service Account" \
        --description="Service account for automated ministry scheduling"
fi

# 6. 分配权限
echo -e "${BLUE}🔐 分配服务账号权限${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/logging.logWriter"

# 7. 准备部署文件
echo -e "${BLUE}📦 准备部署文件${NC}"
rm -rf cloud_functions_deploy
mkdir -p cloud_functions_deploy

# 复制必要的文件
cp cloud_functions/main.py cloud_functions_deploy/
cp cloud_functions/requirements.txt cloud_functions_deploy/

# 复制源代码文件
cp src/email_sender.py cloud_functions_deploy/
cp src/scheduler.py cloud_functions_deploy/
cp src/notification_generator.py cloud_functions_deploy/
cp src/data_validator.py cloud_functions_deploy/
cp src/template_manager.py cloud_functions_deploy/

# 复制模板文件
cp -r templates cloud_functions_deploy/

# 8. 部署 Cloud Functions
echo -e "${BLUE}☁️  部署 Cloud Functions${NC}"

# 部署周三确认通知函数
echo -e "${YELLOW}📅 部署周三确认通知函数${NC}"
gcloud functions deploy send-weekly-confirmation \
    --gen2 \
    --runtime=python311 \
    --region=${REGION} \
    --source=cloud_functions_deploy \
    --entry-point=send_weekly_confirmation \
    --trigger-http \
    --allow-unauthenticated \
    --service-account=${SERVICE_ACCOUNT_EMAIL} \
    --memory=512MB \
    --timeout=300s

# 部署周六提醒通知函数
echo -e "${YELLOW}🔔 部署周六提醒通知函数${NC}"
gcloud functions deploy send-sunday-reminder \
    --gen2 \
    --runtime=python311 \
    --region=${REGION} \
    --source=cloud_functions_deploy \
    --entry-point=send_sunday_reminder \
    --trigger-http \
    --allow-unauthenticated \
    --service-account=${SERVICE_ACCOUNT_EMAIL} \
    --memory=512MB \
    --timeout=300s

# 9. 获取函数URL
echo -e "${BLUE}🔗 获取函数访问URL${NC}"
WEEKLY_URL=$(gcloud functions describe send-weekly-confirmation --region=${REGION} --format="value(serviceConfig.uri)")
SUNDAY_URL=$(gcloud functions describe send-sunday-reminder --region=${REGION} --format="value(serviceConfig.uri)")

echo -e "${GREEN}周三确认通知函数URL: ${WEEKLY_URL}${NC}"
echo -e "${GREEN}周六提醒通知函数URL: ${SUNDAY_URL}${NC}"

# 10. 创建 Cloud Scheduler 作业
echo -e "${BLUE}⏰ 创建定时任务${NC}"

# 周三上午10点发送确认通知
echo -e "${YELLOW}📅 创建周三确认通知定时任务${NC}"
if gcloud scheduler jobs describe weekly-confirmation-job --location=${REGION} &> /dev/null; then
    echo -e "${BLUE}更新现有的周三确认通知定时任务${NC}"
    gcloud scheduler jobs update http weekly-confirmation-job \
        --location=${REGION} \
        --schedule="0 10 * * 3" \
        --time-zone="America/Los_Angeles" \
        --uri=${WEEKLY_URL} \
        --http-method=POST \
        --description="Weekly confirmation notification - every Wednesday at 10 AM PST"
else
    gcloud scheduler jobs create http weekly-confirmation-job \
        --location=${REGION} \
        --schedule="0 10 * * 3" \
        --time-zone="America/Los_Angeles" \
        --uri=${WEEKLY_URL} \
        --http-method=POST \
        --description="Weekly confirmation notification - every Wednesday at 10 AM PST"
fi

# 周六下午6点发送提醒通知
echo -e "${YELLOW}🔔 创建周六提醒通知定时任务${NC}"
if gcloud scheduler jobs describe sunday-reminder-job --location=${REGION} &> /dev/null; then
    echo -e "${BLUE}更新现有的周六提醒通知定时任务${NC}"
    gcloud scheduler jobs update http sunday-reminder-job \
        --location=${REGION} \
        --schedule="0 18 * * 6" \
        --time-zone="America/Los_Angeles" \
        --uri=${SUNDAY_URL} \
        --http-method=POST \
        --description="Sunday reminder notification - every Saturday at 6 PM PST"
else
    gcloud scheduler jobs create http sunday-reminder-job \
        --location=${REGION} \
        --schedule="0 18 * * 6" \
        --time-zone="America/Los_Angeles" \
        --uri=${SUNDAY_URL} \
        --http-method=POST \
        --description="Sunday reminder notification - every Saturday at 6 PM PST"
fi

# 11. 部署 Cloud Run 应用（包含ICS日历功能）
echo -e "${BLUE}🌐 部署 Cloud Run 应用${NC}"

# 检查 Docker 是否已安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker 未安装${NC}"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

# 配置 Docker 认证
echo -e "${BLUE}🔑 配置 Docker 认证${NC}"
gcloud auth configure-docker

# 构建 Docker 镜像
echo -e "${BLUE}🏗️  构建 Docker 镜像${NC}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
echo "镜像名称: ${IMAGE_NAME}"

# 使用 Cloud Build 构建镜像
gcloud builds submit --tag ${IMAGE_NAME} .

# 部署到 Cloud Run
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

# 12. 获取 Cloud Run 服务URL
echo -e "${BLUE}🔗 获取 Cloud Run 服务访问URL${NC}"
CLOUD_RUN_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo -e "${GREEN}Cloud Run 服务URL: ${CLOUD_RUN_URL}${NC}"

# 13. 更新 Cloud Scheduler 作业以包含ICS更新
echo -e "${BLUE}📅 更新定时任务以包含ICS日历更新${NC}"

# 创建ICS更新函数（如果不存在）
echo -e "${YELLOW}📅 部署ICS日历更新函数${NC}"
if ! gcloud functions describe update-ics-calendars --region=${REGION} &> /dev/null; then
    gcloud functions deploy update-ics-calendars \
        --gen2 \
        --runtime=python311 \
        --region=${REGION} \
        --source=cloud_functions_deploy \
        --entry-point=update_ics_calendars \
        --trigger-http \
        --allow-unauthenticated \
        --service-account=${SERVICE_ACCOUNT_EMAIL} \
        --memory=512MB \
        --timeout=300s
fi

# 获取ICS更新函数URL
ICS_UPDATE_URL=$(gcloud functions describe update-ics-calendars --region=${REGION} --format="value(serviceConfig.uri)")

# 更新定时任务以同时调用邮件发送和ICS更新
echo -e "${YELLOW}🔄 更新定时任务以包含ICS更新${NC}"

# 更新周三确认任务
gcloud scheduler jobs update http weekly-confirmation-job \
    --location=${REGION} \
    --schedule="0 10 * * 3" \
    --time-zone="America/Los_Angeles" \
    --uri=${WEEKLY_URL} \
    --http-method=POST \
    --description="Weekly confirmation notification + ICS update - every Wednesday at 10 AM PST"

# 更新周六提醒任务
gcloud scheduler jobs update http sunday-reminder-job \
    --location=${REGION} \
    --schedule="0 18 * * 6" \
    --time-zone="America/Los_Angeles" \
    --uri=${SUNDAY_URL} \
    --http-method=POST \
    --description="Sunday reminder notification + ICS update - every Saturday at 6 PM PST"

# 14. 清理临时文件
echo -e "${BLUE}🧹 清理临时文件${NC}"
rm -rf cloud_functions_deploy

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "======================================================================"
echo -e "${BLUE}📋 部署摘要:${NC}"
echo -e "  项目ID: ${PROJECT_ID}"
echo -e "  区域: ${REGION}"
echo -e "  Cloud Run 服务: ${SERVICE_NAME}"
echo -e "  周三确认通知: 每周三上午10点 (太平洋时间)"
echo -e "  周六提醒通知: 每周六下午6点 (太平洋时间)"
echo ""
echo -e "${BLUE}🔗 访问地址:${NC}"
echo -e "  Streamlit Web界面: ${CLOUD_RUN_URL}"
echo -e "  负责人日历订阅: ${CLOUD_RUN_URL}/calendars/grace_irvine_coordinator.ics"
echo -e "  同工日历订阅: ${CLOUD_RUN_URL}/calendars/grace_irvine_workers.ics"
echo ""
echo -e "${YELLOW}⚠️  下一步操作:${NC}"
echo "1. 在 Google Cloud Console 中设置环境变量 (Secret Manager)"
echo "2. 配置 Google Sheets API 权限"
echo "3. 测试函数是否正常工作"
echo "4. 在日历应用中订阅ICS URL进行自动更新"
echo ""
echo -e "${BLUE}📚 查看日志:${NC}"
echo "  gcloud functions logs read send-weekly-confirmation --region=${REGION}"
echo "  gcloud functions logs read send-sunday-reminder --region=${REGION}"
echo "  gcloud run services logs read ${SERVICE_NAME} --region=${REGION}"
echo ""
echo -e "${BLUE}🎯 手动触发测试:${NC}"
echo "  curl -X POST ${WEEKLY_URL}"
echo "  curl -X POST ${SUNDAY_URL}"
echo "  curl ${CLOUD_RUN_URL}/calendars/grace_irvine_coordinator.ics"
echo ""
echo -e "${BLUE}🔗 获取ICS订阅URL:${NC}"
echo "  python3 scripts/get_cloud_run_url.py"
echo ""
echo -e "${BLUE}📱 用户订阅指南:${NC}"
echo "1. 运行: python3 scripts/get_cloud_run_url.py"
echo "2. 复制显示的ICS订阅URL"
echo "3. 在日历应用中订阅URL（Google Calendar、Apple Calendar、Outlook等）"
echo "4. 日历将自动更新，无需手动操作"
