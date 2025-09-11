# 🚀 部署指南

Grace Irvine Ministry Scheduler v2.0 - 本地和云端双模式部署指南

## 📋 部署准备

### 1. 环境变量配置

创建 `.env` 文件：
```bash
# Google Sheets配置（必需）
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here

# 邮件配置（可选）
SENDER_EMAIL=your_email@example.com
EMAIL_PASSWORD=your_app_password

# 云端部署配置（云端部署时必需）
GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler
GOOGLE_CLOUD_PROJECT=ai-for-god
STORAGE_MODE=cloud
```

### 2. 依赖包安装

```bash
pip install -r requirements.txt
```

## 💻 本地开发部署

### 快速启动
```bash
# 1. 启动应用
python3 start.py

# 2. 访问Web界面
# http://localhost:8501

# 3. 生成日历文件
python3 generate_calendars.py
```

### 本地功能
- ✅ 完整的Web管理界面
- ✅ 模板编辑和预览
- ✅ 数据处理和清洗
- ✅ ICS日历生成
- ✅ 邮件发送功能
- ✅ 文件存储在本地目录

## ☁️ 云端部署

### 第一步：设置GCP Storage

```bash
# 1. 设置环境变量
export GOOGLE_CLOUD_PROJECT=ai-for-god
export GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler

# 2. 运行存储设置脚本
python3 setup_cloud_storage.py
```

这将创建：
- Storage Bucket和目录结构
- 公开访问权限配置
- 初始文件上传
- 部署配置文件

### 第二步：部署应用

```bash
# 使用新的部署脚本
python3 deploy_to_cloud_run.py
```

### 第三步：验证部署

部署完成后，您将获得：
- 🌐 **应用URL**: `https://grace-irvine-scheduler-xxx.run.app`
- 📅 **日历订阅URL**: `https://storage.googleapis.com/your-bucket/calendars/grace_irvine_coordinator.ics`

## 📁 云端存储文件结构

```
gs://grace-irvine-ministry-scheduler/
├── templates/
│   ├── dynamic_templates.json     # 🔧 主模板配置（可在线编辑）
│   └── backups/                   # 📋 模板备份
│       ├── templates_20250910_120000.json
│       └── templates_20250909_180000.json
├── calendars/
│   ├── grace_irvine_coordinator.ics # 📅 负责人日历（公开订阅）
│   └── archives/                   # 📚 历史版本
├── data/
│   ├── cache/
│   │   └── processed_schedules.json # 💾 数据缓存
│   └── exports/                    # 📊 导出文件
└── logs/                           # 📝 应用日志
```

## 🔄 存储策略

### 📝 模板文件
- **本地开发**: 存储在 `templates/dynamic_templates.json`
- **云端部署**: 存储在 `gs://bucket/templates/dynamic_templates.json`
- **读取优先级**: 云端 > 本地 > 默认
- **编辑方式**: Web界面在线编辑，自动保存到云端

### 📅 ICS文件
- **生成位置**: 本地生成后自动上传到云端
- **公开访问**: `https://storage.googleapis.com/bucket/calendars/*.ics`
- **订阅方式**: 用户直接订阅公开URL
- **更新机制**: 手动触发或定时更新

### 💾 数据缓存
- **缓存位置**: 云端存储，减少API调用
- **缓存时间**: 6小时
- **更新触发**: 手动刷新或数据变化检测

## 🌐 双模式对比

| 功能 | 本地模式 | 云端模式 |
|------|----------|----------|
| **模板存储** | 本地JSON文件 | GCP Storage |
| **模板编辑** | 本地文件编辑 | Web界面在线编辑 |
| **ICS文件** | 本地文件 | GCP Storage + 公开URL |
| **数据缓存** | 本地文件 | GCP Storage |
| **备份** | 本地目录 | GCP Storage |
| **访问方式** | localhost:8501 | 公开URL |
| **日历订阅** | 本地URL | 公开GCS URL |

## 🔧 部署后操作

### 1. 验证功能
```bash
# 检查应用状态
curl https://your-app-url.run.app/health

# 检查存储状态  
curl https://your-app-url.run.app/api/status
```

### 2. 模板管理
- 访问应用 → "🛠️ 模板编辑器"
- 编辑模板内容
- 点击"保存到云端"
- 模板自动保存到GCP Storage

### 3. 日历订阅
- 访问应用 → "📅 日历管理"
- 点击"生成/更新日历文件"
- 复制公开订阅URL
- 在日历应用中订阅URL

### 4. 数据更新
- 访问应用 → "📊 数据概览"
- 点击"刷新数据"
- 系统自动从Google Sheets获取最新数据

## ⚙️ 环境变量配置

### Cloud Run环境变量
```yaml
GCP_STORAGE_BUCKET: grace-irvine-ministry-scheduler
GOOGLE_CLOUD_PROJECT: ai-for-god
STORAGE_MODE: cloud
PORT: 8080
GOOGLE_SPREADSHEET_ID: your_sheet_id
```

### 本地开发环境变量
```bash
# .env 文件
GOOGLE_SPREADSHEET_ID=your_sheet_id
SENDER_EMAIL=your_email@example.com
EMAIL_PASSWORD=your_app_password
```

## 🔒 权限配置

### Storage Bucket权限
- **应用服务账户**: `objectAdmin` (读写权限)
- **公开访问**: `objectViewer` (仅calendars目录)

### Cloud Run权限
- **默认服务账户**: 自动配置Storage访问
- **自定义服务账户**: 需要Storage权限

## 🛠️ 故障排除

### 常见问题

1. **模板加载失败**
   - 检查GCP_STORAGE_BUCKET环境变量
   - 验证Storage权限配置
   - 查看应用日志

2. **日历文件访问失败**
   - 检查Bucket公开权限
   - 验证文件是否存在
   - 测试公开URL访问

3. **数据获取失败**
   - 检查GOOGLE_SPREADSHEET_ID
   - 验证Google Sheets公开访问
   - 检查网络连接

### 调试命令
```bash
# 查看应用日志
gcloud run services logs read grace-irvine-scheduler --region=us-central1

# 检查Storage文件
gsutil ls -r gs://grace-irvine-ministry-scheduler/

# 测试存储访问
gsutil cat gs://grace-irvine-ministry-scheduler/templates/dynamic_templates.json
```

## 📊 监控和维护

### 定期任务
- 每周检查应用状态
- 每月清理旧备份文件
- 定期更新依赖包

### 备份策略
- 模板文件：每次修改自动备份
- 日历文件：每日归档
- 数据缓存：每周备份

---

**Grace Irvine Ministry Scheduler v2.0** - 云端部署指南
Made with ❤️ for Grace Irvine Presbyterian Church
