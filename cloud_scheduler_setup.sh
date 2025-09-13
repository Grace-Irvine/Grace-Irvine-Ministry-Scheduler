#!/bin/bash
# Cloud Scheduler 设置脚本
# 设置每4小时自动更新ICS文件的定时任务

# 配置变量
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-ai-for-god}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="grace-irvine-scheduler"
SCHEDULER_JOB_NAME="grace-irvine-ics-updater"
SCHEDULER_AUTH_TOKEN="${SCHEDULER_AUTH_TOKEN:-grace-irvine-scheduler-2025}"

echo "🔧 设置 Cloud Scheduler 定时任务"
echo "================================"
echo "项目ID: $PROJECT_ID"
echo "区域: $REGION"
echo "服务名称: $SERVICE_NAME"
echo "任务名称: $SCHEDULER_JOB_NAME"
echo ""

# 启用 Cloud Scheduler API
echo "1. 启用 Cloud Scheduler API..."
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID

# 获取 API 服务 URL
echo "2. 获取 API 服务 URL..."
API_SERVICE_NAME="grace-irvine-api"

# 优先使用环境变量中的API服务URL（从部署脚本传入）
if [ -n "$API_SERVICE_URL" ]; then
    SERVICE_URL=$API_SERVICE_URL
    echo "   使用传入的API服务URL: $SERVICE_URL"
else
    # 否则查询API服务URL
    SERVICE_URL=$(gcloud run services describe $API_SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format='value(status.url)' 2>/dev/null)
    
    if [ -z "$SERVICE_URL" ]; then
        echo "❌ 无法获取API服务URL，请确保grace-irvine-api服务已部署"
        exit 1
    fi
    echo "   API服务URL: $SERVICE_URL"
fi

# 创建服务账号（如果不存在）
echo "3. 检查/创建服务账号..."
SERVICE_ACCOUNT="ics-updater@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT --project=$PROJECT_ID &>/dev/null; then
    echo "创建服务账号..."
    gcloud iam service-accounts create ics-updater \
        --display-name="ICS Calendar Updater" \
        --project=$PROJECT_ID
fi

# 授予服务账号 Cloud Run 调用权限
echo "4. 授予服务账号权限..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.invoker" \
    --region=$REGION \
    --project=$PROJECT_ID

# 删除旧的定时任务（如果存在）
echo "5. 检查并删除旧任务..."
if gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "删除现有任务..."
    gcloud scheduler jobs delete $SCHEDULER_JOB_NAME \
        --location=$REGION \
        --project=$PROJECT_ID \
        --quiet
fi

# 创建新的定时任务
echo "6. 创建新的定时任务..."
gcloud scheduler jobs create http $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID \
    --schedule="0 */4 * * *" \
    --time-zone="America/Los_Angeles" \
    --uri="${SERVICE_URL}/api/update-ics" \
    --http-method=POST \
    --headers="X-Auth-Token=${SCHEDULER_AUTH_TOKEN},Content-Type=application/json" \
    --oidc-service-account-email=$SERVICE_ACCOUNT \
    --oidc-token-audience=$SERVICE_URL \
    --attempt-deadline="30m" \
    --description="每4小时自动更新Grace Irvine Ministry ICS日历文件"

# 验证任务创建成功
echo ""
echo "7. 验证任务状态..."
gcloud scheduler jobs describe $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID

echo ""
echo "✅ Cloud Scheduler 设置完成！"
echo "================================"
echo "📅 任务名称: $SCHEDULER_JOB_NAME"
echo "⏰ 执行频率: 每4小时 (0:00, 4:00, 8:00, 12:00, 16:00, 20:00 PST)"
echo "🔗 目标端点: ${SERVICE_URL}/api/update-ics"
echo ""
echo "🔧 管理命令:"
echo "  查看任务: gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$REGION"
echo "  手动触发: gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$REGION"
echo "  查看日志: gcloud logging read 'resource.type=\"cloud_scheduler_job\" AND resource.labels.job_id=\"$SCHEDULER_JOB_NAME\"' --limit=50"
echo "  暂停任务: gcloud scheduler jobs pause $SCHEDULER_JOB_NAME --location=$REGION"
echo "  恢复任务: gcloud scheduler jobs resume $SCHEDULER_JOB_NAME --location=$REGION"
echo "  删除任务: gcloud scheduler jobs delete $SCHEDULER_JOB_NAME --location=$REGION"
