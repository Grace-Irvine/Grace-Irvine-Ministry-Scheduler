# 自动ICS更新设置指南
# Automatic ICS Update Setup Guide

## 🎯 功能概述

Grace Irvine Ministry Scheduler 现在支持自动化ICS日历更新功能：

- **自动更新频率**: 每4小时
- **数据来源**: Google Sheets最新排程数据
- **模板同步**: 从GCP Storage Bucket读取最新模板
- **自动生成**: 生成新的ICS日历文件
- **云端同步**: 自动上传到GCP Storage Bucket
- **手动触发**: 保留Web界面手动更新功能

## 🚀 部署步骤

### 1. 部署应用到Cloud Run

```bash
# 确保设置了环境变量
export GOOGLE_CLOUD_PROJECT=ai-for-god
export GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler

# 部署应用
python deploy_to_cloud_run.py
```

### 2. 设置Cloud Scheduler定时任务

```bash
# 运行设置脚本
chmod +x cloud_scheduler_setup.sh
./cloud_scheduler_setup.sh
```

或手动设置：

```bash
# 启用Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# 创建定时任务
gcloud scheduler jobs create http grace-irvine-ics-updater \
    --location=us-central1 \
    --schedule="0 */4 * * *" \
    --time-zone="America/Los_Angeles" \
    --uri="https://YOUR-SERVICE-URL/api/update-ics" \
    --http-method=POST \
    --headers="X-Auth-Token=grace-irvine-scheduler-2025" \
    --oidc-service-account-email=ics-updater@PROJECT_ID.iam.gserviceaccount.com
```

## 📡 API端点

### 健康检查
```
GET /api/health
```

### 系统状态
```
GET /api/status
```

### 触发ICS更新（需要认证）
```
POST /api/update-ics
Headers:
  X-Auth-Token: grace-irvine-scheduler-2025
```

## 🧪 测试API

### 本地测试
```bash
# 启动应用
python app_unified.py

# 运行测试脚本
python test_api_endpoints.py
```

### 云端测试
```bash
# 测试部署的服务
python test_api_endpoints.py https://YOUR-SERVICE-URL grace-irvine-scheduler-2025

# 或手动触发Cloud Scheduler
gcloud scheduler jobs run grace-irvine-ics-updater --location=us-central1
```

## 📅 更新时间表

定时任务将在以下时间执行（太平洋时间）：
- 00:00 (午夜)
- 04:00 (凌晨4点)
- 08:00 (早上8点)
- 12:00 (中午)
- 16:00 (下午4点)
- 20:00 (晚上8点)

## 🔧 管理命令

### 查看定时任务状态
```bash
gcloud scheduler jobs describe grace-irvine-ics-updater --location=us-central1
```

### 手动触发更新
```bash
gcloud scheduler jobs run grace-irvine-ics-updater --location=us-central1
```

### 查看执行日志
```bash
gcloud logging read 'resource.type="cloud_scheduler_job" AND resource.labels.job_id="grace-irvine-ics-updater"' --limit=50
```

### 暂停自动更新
```bash
gcloud scheduler jobs pause grace-irvine-ics-updater --location=us-central1
```

### 恢复自动更新
```bash
gcloud scheduler jobs resume grace-irvine-ics-updater --location=us-central1
```

## 🔐 安全设置

### 认证令牌
- 默认令牌: `grace-irvine-scheduler-2025`
- 可通过环境变量 `SCHEDULER_AUTH_TOKEN` 自定义
- 建议在生产环境使用强密码

### 服务账号权限
- Cloud Scheduler使用专用服务账号
- 仅授予 `roles/run.invoker` 权限
- 自动使用OIDC令牌认证

## 📊 监控和日志

### Cloud Run日志
```bash
gcloud run services logs read grace-irvine-scheduler --region=us-central1
```

### Cloud Scheduler日志
```bash
gcloud logging read 'resource.type="cloud_scheduler_job"' --limit=20
```

### 监控指标
- Cloud Run: 请求数、延迟、错误率
- Cloud Scheduler: 执行成功率、重试次数
- Storage: 文件更新频率、大小

## ❓ 常见问题

### Q: 自动更新失败怎么办？
A: 检查以下内容：
1. Cloud Run服务是否正常运行
2. Google Sheets访问权限
3. Storage Bucket权限
4. 查看执行日志定位问题

### Q: 如何更改更新频率？
A: 修改Cloud Scheduler的cron表达式：
```bash
gcloud scheduler jobs update http grace-irvine-ics-updater \
    --schedule="0 */2 * * *"  # 改为每2小时
```

### Q: 如何验证ICS文件是否更新？
A: 
1. 查看Web界面的"日历管理"页面
2. 访问公开URL查看文件更新时间
3. 检查日历应用中的事件是否更新

### Q: 手动更新和自动更新冲突吗？
A: 不会冲突。两者使用相同的更新函数，确保一致性。

## 📝 更新流程图

```
┌─────────────────┐
│ Cloud Scheduler │
│   (每4小时)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API端点       │
│ /api/update-ics │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Google Sheets   │────▶│  读取排程数据    │
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐              │
│ Storage Bucket  │────▶┌────────▼────────┐
│  (模板文件)      │     │  读取最新模板    │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  生成ICS文件    │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ 上传到Bucket    │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  返回成功响应   │
                        └─────────────────┘
```
