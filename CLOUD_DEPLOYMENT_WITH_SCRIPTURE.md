# ☁️ 云端部署指南（包含经文分享功能）

## 📋 概述

本指南说明如何将包含经文分享功能的Grace Irvine Ministry Scheduler部署到Google Cloud Run。

## ✨ 新增功能

- **📖 经文分享**: 周三确认通知自动包含轮换的经文内容
- **🔄 智能轮换**: 经文按顺序自动循环使用
- **☁️ 云端同步**: 经文配置自动同步到GCP Storage
- **🛠️ 在线管理**: 通过Web界面管理经文内容

## 🔧 部署前检查

运行部署检查脚本：
```bash
python3 check_cloud_deployment.py
```

确保所有检查项目都通过：
- ✅ 本地文件检查 
- ✅ 经文配置检查
- ✅ 部署配置检查  
- ✅ Dockerfile检查
- ✅ 存储桶文件检查

## 📦 部署步骤

### 1. 环境准备

```bash
# 设置环境变量
export GOOGLE_CLOUD_PROJECT="ai-for-god"
export GCP_STORAGE_BUCKET="grace-irvine-ministry-scheduler"

# 认证Google Cloud
gcloud auth login
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

### 2. 初始化云端存储

```bash
# 运行存储设置脚本
python3 setup_cloud_storage.py
```

这个脚本会：
- 创建GCP Storage bucket
- 设置目录结构
- 上传初始配置文件（包括经文配置）
- 配置权限和访问控制

### 3. 部署到Cloud Run

```bash
# 运行部署脚本
python3 deploy_to_cloud_run.py
```

部署脚本会：
- 构建Docker镜像
- 推送到Google Container Registry
- 部署到Cloud Run
- 配置环境变量和资源限制

## 🔍 部署验证

### 1. 访问应用

部署完成后，访问提供的应用URL，验证以下功能：

- **📊 数据概览**: 查看排程数据
- **📝 模板生成**: 生成包含经文的周三通知
- **📖 经文管理**: 管理经文内容
- **🛠️ 模板编辑**: 在线编辑模板
- **📅 日历管理**: 生成ICS文件

### 2. 测试经文分享

1. 进入"📖 经文管理"页面
2. 查看当前经文库（应该包含10段预设经文）
3. 在"📊 使用预览"中测试模板生成
4. 验证周三通知包含经文内容

### 3. 测试云端同步

1. 在"📖 经文管理"中添加新经文
2. 检查是否自动保存到云端
3. 在"🛠️ 模板编辑器"中编辑模板
4. 点击"☁️ 保存到云端"验证同步

## 📁 云端存储结构

部署后的GCP Storage结构：

```
gs://grace-irvine-ministry-scheduler/
├── templates/
│   ├── dynamic_templates.json      # 动态模板配置
│   └── scripture_sharing.json      # 经文分享配置
├── calendars/
│   └── grace_irvine_coordinator.ics # 负责人日历
├── data/cache/                      # 数据缓存
└── backups/                         # 配置备份
```

## 🔗 重要URL

部署完成后，记录以下重要URL：

- **应用主页**: `https://your-service-url.run.app`
- **系统状态**: `https://your-service-url.run.app/api/status`
- **日历订阅**: `https://storage.googleapis.com/grace-irvine-ministry-scheduler/calendars/grace_irvine_coordinator.ics`

## 🛠️ 管理操作

### 查看服务状态
```bash
gcloud run services describe grace-irvine-scheduler --region=us-central1
```

### 查看应用日志
```bash
gcloud run services logs read grace-irvine-scheduler --region=us-central1
```

### 更新部署
```bash
# 修改代码后重新部署
python3 deploy_to_cloud_run.py
```

### 手动上传配置
```bash
# 上传经文配置
gsutil cp templates/scripture_sharing.json gs://grace-irvine-ministry-scheduler/templates/

# 上传模板配置  
gsutil cp templates/dynamic_templates.json gs://grace-irvine-ministry-scheduler/templates/
```

## 🔧 故障排除

### 常见问题

1. **经文不显示**
   - 检查云端经文配置: `gsutil cat gs://grace-irvine-ministry-scheduler/templates/scripture_sharing.json`
   - 验证应用日志中的错误信息

2. **配置不同步**
   - 确认环境变量 `STORAGE_MODE=cloud`
   - 检查GCP Storage权限设置

3. **部署失败**
   - 运行 `python3 check_cloud_deployment.py` 检查配置
   - 确认Docker镜像构建成功

### 重新初始化

如果需要重新初始化：

```bash
# 1. 删除存储桶（可选）
gsutil rm -r gs://grace-irvine-ministry-scheduler

# 2. 重新设置存储
python3 setup_cloud_storage.py

# 3. 重新部署
python3 deploy_to_cloud_run.py
```

## 📈 使用监控

### 应用指标
- **请求数**: Cloud Run 控制台
- **错误率**: 应用日志
- **响应时间**: Cloud Run 指标

### 存储使用
```bash
# 查看存储使用情况
gsutil du -s gs://grace-irvine-ministry-scheduler
```

### 经文使用统计
- 在应用的"📖 经文管理"页面查看使用统计
- 当前位置、总数、最后更新时间

## 🔄 更新和维护

### 经文内容更新
1. 在Web界面"📖 经文管理"中添加/编辑经文
2. 自动保存到云端存储
3. 立即生效，无需重新部署

### 模板更新
1. 在"🛠️ 模板编辑器"中修改模板
2. 点击"☁️ 保存到云端"
3. 立即生效，无需重新部署

### 应用代码更新
1. 修改源代码
2. 运行 `python3 deploy_to_cloud_run.py`
3. 自动构建和部署新版本

---

**📞 技术支持**: 如有问题，请检查应用日志或联系系统管理员。
