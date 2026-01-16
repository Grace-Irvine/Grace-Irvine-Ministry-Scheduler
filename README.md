# Grace Irvine Ministry Scheduler - ICS 专用版

仅保留从 **GCS 清洗 JSON** 生成 **ICS 通知日历** 的功能（周三确认、周六提醒）。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `env.example` 为 `.env` 并按需调整：
```bash
DATA_SOURCE_BUCKET=grace-irvine-ministry-data
GOOGLE_CLOUD_PROJECT=ai-for-god
GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler
STORAGE_MODE=local
```

### 3. 生成 ICS（日历文件）
```bash
python3 scripts/generate_local_ics.py
```

或通过 UI：
```bash
python start.py
```

## 📅 输出日历

- `media-team.ics` - 媒体部通知（周三确认 / 周六提醒）
- `children-team.ics` - 儿童部通知（周三确认 / 周六提醒）

## 📁 目录结构（精简后）

```
Grace-Irvine-Ministry-Scheduler/
├── app_unified.py                # Streamlit ICS 管理界面
├── start.py                      # 启动脚本
├── start_api.py                  # API 服务（可选）
├── src/
│   ├── multi_calendar_generator.py
│   ├── dynamic_template_manager.py
│   ├── json_data_reader.py
│   ├── scripture_manager.py
│   ├── cloud_storage_manager.py
│   └── ics_notification_config.py
├── configs/
│   └── ics_notification_config.json
├── templates/
│   ├── dynamic_templates.json
│   └── scripture_sharing.json
├── calendars/                    # 生成的 ICS 输出
└── scripts/
    └── generate_local_ics.py
```

## 🧪 测试

```bash
python scripts/test_ics_generation.py
```

## 📚 文档

- `docs/LOCAL_ICS_GENERATION.md`
- `docs/NEW_ICS_ARCHITECTURE.md`
- `docs/NEW_ICS_IMPLEMENTATION.md`

