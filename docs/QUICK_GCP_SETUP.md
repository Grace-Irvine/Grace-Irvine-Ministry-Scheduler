# 🚀 Google Cloud 快速部署指南

## 一键部署到 Google Cloud

只需几个简单步骤，就能将你的邮件通知系统部署到云端，实现自动化定时发送！

## 📋 前置要求

- ✅ Google Cloud 账户（有信用卡绑定）
- ✅ Gmail 账户和应用专用密码
- ✅ Google Sheets 访问权限

## 🎯 3分钟快速部署

### 第1步：安装 Google Cloud CLI

```bash
# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows: 下载安装包
# https://cloud.google.com/sdk/docs/install
```

### 第2步：配置环境

```bash
# 1. 登录
gcloud auth login

# 2. 创建项目（替换为你的项目名）
gcloud projects create grace-irvine-scheduler-your-name

# 3. 设置项目
gcloud config set project grace-irvine-scheduler-your-name
```

### 第3步：配置邮件设置

创建 `.env` 文件：

```env
GOOGLE_SPREADSHEET_ID=你的表格ID
SENDER_EMAIL=你的Gmail地址
EMAIL_PASSWORD=Gmail应用专用密码
RECIPIENT_EMAILS=收件人1@example.com,收件人2@example.com
```

> 💡 **获取Gmail应用密码**: [点击这里](https://myaccount.google.com/apppasswords)

### 第4步：一键部署

```bash
# 修改脚本中的项目ID
vim deploy_to_gcp.sh  # 将 PROJECT_ID 改为你的项目ID

# 执行部署
./deploy_to_gcp.sh

# 配置密钥
./setup_gcp_secrets.sh
```

### 第5步：测试验证

```bash
# 测试函数是否正常工作
python test_gcp_functions.py 你的项目ID
```

## ✅ 部署完成！

🎉 恭喜！你的系统现在会自动发送通知：

- **周三上午10点**: 发送确认通知
- **周六下午6点**: 发送提醒通知

## 🔍 快速检查

```bash
# 查看定时任务
gcloud scheduler jobs list --location=us-central1

# 查看函数
gcloud functions list --region=us-central1

# 手动测试
gcloud scheduler jobs run weekly-confirmation-job --location=us-central1
```

## 📊 预估成本

**每月约 $0.18** 💰

- Cloud Functions: $0.01
- Cloud Scheduler: $0.10  
- Secret Manager: $0.06
- 网络流量: $0.01

## ❓ 遇到问题？

### 常见解决方案

1. **部署失败**: 检查项目ID是否正确
2. **邮件不发送**: 验证Gmail应用密码
3. **读取表格失败**: 确认服务账号权限

### 查看详细日志

```bash
gcloud functions logs read send-weekly-confirmation --region=us-central1
```

## 🔄 后续维护

### 修改发送时间

```bash
# 改为每周三上午9点
gcloud scheduler jobs update http weekly-confirmation-job \
    --schedule="0 9 * * 3" --location=us-central1
```

### 更新代码

```bash
# 修改代码后重新部署
./deploy_to_gcp.sh
```

### 添加收件人

```bash
# 更新 .env 文件，然后运行
./setup_gcp_secrets.sh
```

---

**🎯 目标**: 3分钟内完成部署，让技术服务于事工！

**📞 需要帮助**: 查看详细的 [完整部署指南](GOOGLE_CLOUD_DEPLOYMENT.md)
