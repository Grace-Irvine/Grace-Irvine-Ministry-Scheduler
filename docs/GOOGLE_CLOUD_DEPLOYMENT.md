# Google Cloud 部署指南

## 📋 概述

本指南将帮助你将 Grace Irvine Ministry Scheduler 部署到 Google Cloud Platform，实现自动化的定时邮件通知功能。

## 🏗️ 架构概览

```
Google Cloud Scheduler → Cloud Functions → Google Sheets + Gmail
        ⏰                    📧              📊        📮
    定时触发器           邮件发送函数        数据源     邮件服务
```

### 核心组件

- **Cloud Functions**: 运行邮件发送逻辑
- **Cloud Scheduler**: 定时触发任务
- **Secret Manager**: 安全存储敏感信息
- **Cloud Logging**: 监控和日志记录

## 🚀 部署步骤

### 1. 准备工作

#### 1.1 安装 Google Cloud CLI

```bash
# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# 下载并安装: https://cloud.google.com/sdk/docs/install
```

#### 1.2 登录并初始化

```bash
# 登录Google Cloud
gcloud auth login

# 创建新项目（或使用现有项目）
gcloud projects create grace-irvine-scheduler --name="Grace Irvine Ministry Scheduler"

# 设置默认项目
gcloud config set project grace-irvine-scheduler
```

#### 1.3 启用账单

在 [Google Cloud Console](https://console.cloud.google.com) 中为项目启用账单功能。

### 2. 配置环境变量

#### 2.1 创建 .env 文件

在项目根目录创建 `.env` 文件：

```env
# Google Sheets 配置
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here

# 邮件发送配置
SENDER_EMAIL=jonathanjing@graceirvine.org
SENDER_NAME=Grace Irvine 事工协调
EMAIL_PASSWORD=your_gmail_app_password_here

# 收件人列表（用逗号分隔）
RECIPIENT_EMAILS=email1@example.com,email2@example.com,email3@example.com
```

#### 2.2 获取 Gmail 应用专用密码

1. 访问 [Google账户安全设置](https://myaccount.google.com/security)
2. 启用两步验证
3. 生成应用专用密码：[https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. 将生成的密码填入 `EMAIL_PASSWORD`

### 3. 执行部署

#### 3.1 运行部署脚本

```bash
# 给脚本执行权限
chmod +x deploy_to_gcp.sh
chmod +x setup_gcp_secrets.sh

# 修改脚本中的 PROJECT_ID
# 编辑 deploy_to_gcp.sh，将 PROJECT_ID 改为你的项目ID

# 执行部署
./deploy_to_gcp.sh
```

#### 3.2 配置密钥管理

```bash
# 设置环境变量到 Secret Manager
./setup_gcp_secrets.sh
```

### 4. 验证部署

#### 4.1 测试函数

```bash
# 安装测试依赖
pip install requests

# 运行测试
python test_gcp_functions.py grace-irvine-scheduler
```

#### 4.2 手动触发测试

```bash
# 获取函数URL
WEEKLY_URL=$(gcloud functions describe send-weekly-confirmation --region=us-central1 --format="value(serviceConfig.uri)")
SUNDAY_URL=$(gcloud functions describe send-sunday-reminder --region=us-central1 --format="value(serviceConfig.uri)")

# 手动触发
curl -X POST $WEEKLY_URL
curl -X POST $SUNDAY_URL
```

## ⏰ 定时任务配置

### 默认时间设置

- **周三确认通知**: 每周三上午 10:00 (太平洋时间)
- **周六提醒通知**: 每周六下午 6:00 (太平洋时间)

### 修改定时设置

```bash
# 修改周三通知时间为上午9点
gcloud scheduler jobs update http weekly-confirmation-job \
    --location=us-central1 \
    --schedule="0 9 * * 3"

# 修改周六通知时间为下午5点
gcloud scheduler jobs update http sunday-reminder-job \
    --location=us-central1 \
    --schedule="0 17 * * 6"
```

### Cron 表达式说明

```
┌───────────── 分钟 (0 - 59)
│ ┌─────────── 小时 (0 - 23)
│ │ ┌───────── 日 (1 - 31)
│ │ │ ┌─────── 月 (1 - 12)
│ │ │ │ ┌───── 星期 (0 - 6) (0=周日)
│ │ │ │ │
* * * * *
```

常用示例：
- `0 9 * * 1-5`: 工作日上午9点
- `0 18 * * 6`: 每周六下午6点
- `0 10 1 * *`: 每月1日上午10点

## 🔍 监控和维护

### 查看日志

```bash
# 查看函数日志
gcloud functions logs read send-weekly-confirmation --region=us-central1 --limit=50
gcloud functions logs read send-sunday-reminder --region=us-central1 --limit=50

# 实时监控日志
gcloud functions logs tail send-weekly-confirmation --region=us-central1
```

### 查看定时任务状态

```bash
# 列出所有定时任务
gcloud scheduler jobs list --location=us-central1

# 查看特定任务详情
gcloud scheduler jobs describe weekly-confirmation-job --location=us-central1
```

### 手动执行定时任务

```bash
# 手动触发周三通知
gcloud scheduler jobs run weekly-confirmation-job --location=us-central1

# 手动触发周六通知
gcloud scheduler jobs run sunday-reminder-job --location=us-central1
```

## 🔧 故障排除

### 常见问题

#### 1. 函数部署失败

**问题**: 部署时出现权限错误
**解决**: 确保已启用必要的API服务

```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

#### 2. 邮件发送失败

**问题**: 函数执行成功但邮件未发送
**解决**: 检查以下配置

```bash
# 检查密钥是否正确设置
gcloud secrets versions access latest --secret="email-password"

# 查看详细错误日志
gcloud functions logs read send-weekly-confirmation --region=us-central1
```

#### 3. Google Sheets 访问失败

**问题**: 无法读取Google Sheets数据
**解决**: 
1. 确保服务账号有权限访问表格
2. 检查表格ID是否正确
3. 验证服务账号密钥配置

#### 4. 定时任务未触发

**问题**: 到了预定时间但任务没有执行
**解决**: 

```bash
# 检查任务状态
gcloud scheduler jobs describe weekly-confirmation-job --location=us-central1

# 检查时区设置
# 确保时区设置为 "America/Los_Angeles"
```

### 调试技巧

1. **本地测试**: 在部署前先在本地运行 `scripts/send_email_notifications.py test`
2. **逐步验证**: 先手动触发函数，确认功能正常后再依赖定时任务
3. **日志分析**: 利用 Cloud Logging 的过滤功能快速定位问题

## 💰 成本估算

基于典型使用情况的预估成本（每月）：

- **Cloud Functions**: ~$0.01 (每月8次调用)
- **Cloud Scheduler**: ~$0.10 (2个定时任务)
- **Secret Manager**: ~$0.06 (5个密钥)
- **网络流量**: ~$0.01

**总计**: 约 $0.18/月

> 注意：实际成本可能因使用量和地区而有所不同

## 🔄 更新和维护

### 更新函数代码

```bash
# 修改代码后重新部署
./deploy_to_gcp.sh
```

### 更新环境变量

```bash
# 更新 .env 文件后重新设置密钥
./setup_gcp_secrets.sh
```

### 备份和恢复

```bash
# 导出定时任务配置
gcloud scheduler jobs describe weekly-confirmation-job --location=us-central1 > weekly-job-backup.yaml
gcloud scheduler jobs describe sunday-reminder-job --location=us-central1 > sunday-job-backup.yaml
```

## 🚨 安全最佳实践

1. **最小权限原则**: 只给服务账号必需的权限
2. **定期轮换密钥**: 定期更新邮件密码和API密钥
3. **监控访问**: 定期检查 Cloud Logging 中的访问日志
4. **备份配置**: 定期备份重要的配置文件

## 📞 支持和联系

如果在部署过程中遇到问题，可以：

1. 查看 [Google Cloud 文档](https://cloud.google.com/docs)
2. 检查项目的 GitHub Issues
3. 联系技术支持团队

---

**最后更新**: 2025年1月
**版本**: 1.0.0
