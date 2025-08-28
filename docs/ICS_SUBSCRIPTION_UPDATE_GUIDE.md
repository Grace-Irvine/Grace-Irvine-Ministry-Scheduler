# ICS日历订阅更新指南

## 🎯 更新概述

已更新ICS日历订阅系统，使用新的Cloud Run服务名称 `grace-irvine-scheduler`，提供更稳定的自动更新服务。

## 🚀 新的URL结构

### Cloud Run服务
- **服务名称**: `grace-irvine-scheduler`
- **区域**: `us-central1`
- **项目**: `ai-for-god`

### ICS订阅URL格式
```
https://grace-irvine-scheduler-HASH-uc.a.run.app/calendars/grace_irvine_coordinator.ics
https://grace-irvine-scheduler-HASH-uc.a.run.app/calendars/grace_irvine_workers.ics
```

## 📋 部署步骤

### 1. 使用更新后的部署脚本

```bash
# 运行更新后的部署脚本
./deploy_to_gcp.sh
```

**新功能包括:**
- ✅ Cloud Functions 邮件通知
- ✅ Cloud Run Streamlit Web界面
- ✅ ICS日历自动更新服务
- ✅ Cloud Scheduler 定时任务

### 2. 获取正确的订阅URL

部署完成后，运行以下命令获取正确的URL：

```bash
python3 scripts/get_cloud_run_url.py
```

**输出示例:**
```
🔗 Grace Irvine Cloud Run URL 获取工具
==================================================
✅ Cloud Run 服务URL: https://grace-irvine-scheduler-abc123-uc.a.run.app

📅 ICS日历订阅URL:
==================================================
负责人日历: https://grace-irvine-scheduler-abc123-uc.a.run.app/calendars/grace_irvine_coordinator.ics
同工日历: https://grace-irvine-scheduler-abc123-uc.a.run.app/calendars/grace_irvine_workers.ics
```

## 📱 用户订阅指南

### Google Calendar 订阅

1. **打开Google Calendar**
2. **左侧点击"+"号** → "从URL添加"
3. **输入订阅URL**:
   ```
   https://grace-irvine-scheduler-abc123-uc.a.run.app/calendars/grace_irvine_coordinator.ics
   ```
4. **点击"添加日历"**

### Apple Calendar 订阅

1. **打开Calendar应用**
2. **"文件" → "新建日历订阅"**
3. **输入订阅URL**
4. **点击"订阅"**

### Outlook 订阅

1. **打开Outlook**
2. **"日历" → "添加日历"**
3. **"从Internet订阅"**
4. **输入订阅URL**

## 🔄 自动更新机制

### 更新频率
- **周三上午10点**: 发送确认通知 + 更新ICS日历
- **周六下午6点**: 发送提醒通知 + 更新ICS日历
- **后台监控**: 每30分钟检查数据变化

### 更新流程
```
Google Sheets数据变化 → Cloud Scheduler触发 → Cloud Functions执行 → 更新ICS文件 → 用户日历自动刷新
```

## 🛠️ 技术架构

### 服务组件

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                    │
├─────────────────────────────────────────────────────────────┤
│  Cloud Scheduler (定时任务)                                 │
│  ├── 周三10:00 → 发送确认通知 + 更新ICS                     │
│  └── 周六18:00 → 发送提醒通知 + 更新ICS                     │
│                                                             │
│  Cloud Functions (邮件通知)                                 │
│  ├── send-weekly-confirmation                              │
│  ├── send-sunday-reminder                                  │
│  └── update-ics-calendars                                  │
│                                                             │
│  Cloud Run (Web界面 + ICS服务)                              │
│  ├── Streamlit Web应用                                      │
│  ├── ICS文件服务 (/calendars/*.ics)                        │
│  └── 后台更新服务                                           │
└─────────────────────────────────────────────────────────────┘
```

### 文件结构

```
/calendars/
├── grace_irvine_coordinator.ics  # 负责人日历订阅
└── grace_irvine_workers.ics      # 同工日历订阅
```

## 🔧 管理和监控

### Web界面管理

访问Cloud Run URL，使用"📅 ICS日历管理"页面：

1. **📋 日历生成** - 手动生成和下载ICS文件
2. **🔗 订阅管理** - 查看订阅URL和使用方法
3. **⚙️ 自动更新** - 手动触发后台服务更新
4. **📊 系统状态** - 监控文件状态和更新时间

### 命令行管理

```bash
# 查看Cloud Run服务状态
gcloud run services describe grace-irvine-scheduler --region=us-central1

# 查看服务日志
gcloud run services logs read grace-irvine-scheduler --region=us-central1

# 查看Cloud Functions日志
gcloud functions logs read send-weekly-confirmation --region=us-central1
gcloud functions logs read send-sunday-reminder --region=us-central1
gcloud functions logs read update-ics-calendars --region=us-central1

# 手动触发更新
curl -X POST https://grace-irvine-scheduler-abc123-uc.a.run.app/api/update-calendars
```

## 🎯 关键优势

### 1. **真正的自动更新**
- ✅ 用户订阅后无需手动操作
- ✅ Google Sheets数据变化自动同步
- ✅ 日历应用自动检测并更新

### 2. **企业级可靠性**
- ✅ Cloud Run自动扩缩容
- ✅ 健康检查和自动重启
- ✅ 高可用性保证

### 3. **统一管理**
- ✅ 一个Cloud Run实例包含所有功能
- ✅ Web界面统一管理
- ✅ 简化的部署和维护

### 4. **成本效益**
- ✅ 复用现有Cloud Scheduler
- ✅ 复用现有Cloud Functions
- ✅ 最小化额外资源消耗

## 🚨 故障排除

### 常见问题

#### 1. 无法获取Cloud Run URL
```bash
# 检查服务是否存在
gcloud run services list --region=us-central1

# 检查部署状态
gcloud run services describe grace-irvine-scheduler --region=us-central1
```

#### 2. ICS文件无法访问
```bash
# 检查文件是否存在
curl https://grace-irvine-scheduler-abc123-uc.a.run.app/calendars/grace_irvine_coordinator.ics

# 手动触发更新
curl -X POST https://grace-irvine-scheduler-abc123-uc.a.run.app/api/update-calendars
```

#### 3. 日历不自动更新
- 确认使用的是"订阅URL"而不是"导入文件"
- 检查日历应用的刷新设置
- 等待Cloud Scheduler下次触发（最多30分钟）

### 联系支持

如果遇到问题，请检查：
1. Cloud Run服务是否正常运行
2. Cloud Functions是否正常执行
3. Google Sheets数据是否正确
4. 网络连接是否正常

## 📞 技术支持

如需技术支持，请提供：
1. 错误信息截图
2. Cloud Run服务URL
3. 具体的操作步骤
4. 浏览器控制台错误信息（如果有）

---

**最后更新**: 2024年12月
**版本**: 2.0
**服务名称**: grace-irvine-scheduler
