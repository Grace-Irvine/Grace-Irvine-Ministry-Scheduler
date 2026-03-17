# Grace Irvine ICS Generator

精简版 ICS 日历生成器，部署在 Google Cloud Run。

## 功能

- 从 Google Sheets 读取事工排程数据
- 生成 ICS 日历文件（周三/周六通知提醒）
- 上传到 Cloud Storage 供订阅

## 文件

```
main.py              # 主入口 (包含所有核心逻辑)
requirements.txt     # Python 依赖
Dockerfile           # Cloud Run 容器配置
DEPLOY.md            # 部署说明
```

## 部署

详见 [DEPLOY.md](DEPLOY.md)

## 配置

通过环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `GOOGLE_SPREADSHEET_ID` | - | Google Sheets ID (必需) |
| `GCP_STORAGE_BUCKET` | grace-irvine-ministry-scheduler | 存储桶名称 |
| `WEDNESDAY_HOUR` | 19 | 周三通知时间 (19:00) |
| `WEDNESDAY_DURATION` | 120 | 周三持续时间 (2小时) |
| `SATURDAY_HOUR` | 9 | 周六通知时间 (09:00) |
| `SATURDAY_DURATION` | 60 | 周六持续时间 (1小时) |
| `ICS_WEEKS_AHEAD` | 4 | 生成未来几周的事件 |

## 触发

Cloud Scheduler 每 4 小时调用一次：
```
POST https://[CLOUD_RUN_URL]/generate-ics
```
