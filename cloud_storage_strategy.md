# 🌐 GCP Storage 存储策略设计

## 📊 文件分类分析

### 🔄 **需要云端存储的文件（动态内容）**

#### 1. **输入配置文件** 
- `templates/dynamic_templates.json` - 模板配置
  - **原因**: 部署后需要在线编辑模板
  - **访问**: 读写频繁
  - **重要性**: 高（影响所有通知内容）

#### 2. **输出文件**
- `calendars/grace_irvine_coordinator.ics` - 负责人日历
  - **原因**: 需要公开订阅访问
  - **访问**: 读取频繁，定期更新
  - **重要性**: 高（用户订阅的核心文件）

#### 3. **数据缓存文件**
- `data/processed_schedules.json` - 处理后的排程数据
  - **原因**: 减少Google Sheets API调用
  - **访问**: 读取频繁
  - **重要性**: 中（性能优化）

#### 4. **备份文件**
- `templates/backups/` - 模板备份
- `data/backups/` - 数据备份
  - **原因**: 版本控制和灾难恢复
  - **访问**: 偶尔写入，很少读取
  - **重要性**: 中（安全保障）

### 🏠 **保持本地的文件（静态内容）**

#### 1. **应用代码**
- `src/*.py` - 核心业务逻辑
- `app_unified.py` - Web应用
- `start.py` - 启动脚本

#### 2. **静态配置**
- `configs/config.yaml` - 基础配置
- `requirements.txt` - 依赖包
- `Dockerfile` - 容器配置

#### 3. **模板资源**
- `templates/email/*.html` - 邮件HTML模板
- `templates/sms/*.txt` - 短信模板

## 🗂️ **推荐的Bucket结构**

```
gs://grace-irvine-ministry-scheduler/
├── templates/
│   ├── dynamic_templates.json          # 主模板配置
│   └── backups/
│       ├── templates_20250910_120000.json
│       └── templates_20250909_180000.json
├── calendars/
│   ├── grace_irvine_coordinator.ics    # 负责人日历
│   └── archives/
│       ├── coordinator_20250910.ics
│       └── coordinator_20250909.ics
├── data/
│   ├── cache/
│   │   ├── processed_schedules.json    # 数据缓存
│   │   └── last_update.json           # 更新时间戳
│   └── exports/
│       ├── schedule_20250910.xlsx     # 导出文件
│       └── reports/
└── logs/
    ├── application.log                 # 应用日志
    └── errors.log                      # 错误日志
```

## ⚙️ **存储策略**

### 📝 **模板文件策略**
- **读取优先级**: Bucket > 本地文件 > 默认模板
- **写入策略**: 同时保存到Bucket和本地
- **备份策略**: 每次修改自动备份到Bucket
- **缓存策略**: 本地缓存1小时，定期同步

### 📅 **ICS文件策略**
- **生成位置**: 本地生成后上传到Bucket
- **访问方式**: 通过CDN或直接Bucket URL
- **更新频率**: 每日自动更新
- **版本控制**: 保留最近7天的历史版本

### 📊 **数据缓存策略**
- **缓存时间**: Google Sheets数据缓存6小时
- **更新触发**: 手动刷新或定时任务
- **失效策略**: 检测到数据变化时立即更新
- **备份保留**: 保留最近30天的数据快照
