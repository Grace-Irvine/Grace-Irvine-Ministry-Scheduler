# Grace Irvine ICS Generator

精简版 ICS 日历生成器，部署在 Google Cloud Run。

## 功能

- 从 Google Sheets 读取事工排程数据（智能列匹配）
- 生成 ICS 日历文件（周三/周六通知提醒）
- 支持 5 个事工岗位：音控、导播/摄影、ProPresenter播放、ProPresenter更新、视频剪辑
- 空缺岗位自动显示"待安排"
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

### 必需配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `GOOGLE_SPREADSHEET_ID` | - | Google Sheets ID (必需) |
| `GCP_STORAGE_BUCKET` | grace-irvine-ministry-scheduler | 存储桶名称 |

### 时间配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WEDNESDAY_HOUR` | 19 | 周三通知时间 (19:00 = 晚上7点) |
| `WEDNESDAY_MINUTE` | 0 | 周三通知分钟 |
| `WEDNESDAY_DURATION` | 120 | 周三持续时间 (分钟，120 = 2小时) |
| `SATURDAY_HOUR` | 9 | 周六通知时间 (09:00 = 早上9点) |
| `SATURDAY_MINUTE` | 0 | 周六通知分钟 |
| `SATURDAY_DURATION` | 60 | 周六持续时间 (分钟，60 = 1小时) |
| `ICS_WEEKS_AHEAD` | 4 | 生成未来几周的事件 |

### 经文配置（可选）

经文可以通过环境变量动态配置，无需重新部署：

**方法 1: JSON 数组（推荐）**
```bash
SCRIPTURES='["经文1内容", "经文2内容", "经文3内容"]'
```

**方法 2: 单独设置每条经文**
```bash
SCRIPTURE_1="看哪，弟兄和睦同居..."
SCRIPTURE_2="又要彼此相顾..."
SCRIPTURE_3="用诗章、颂词..."
```

## 通知格式

### 周三通知示例
```
【本周3月22日主日事工安排提醒】🕊️

• 音控：靖铮
• 导播/摄影：待安排
• ProPresenter播放：Joe
• ProPresenter更新：忠涵
• 视频剪辑：Roxy

📖 按我们所得的恩赐，各有不同。
或说预言，就当照着信心的程度说预言；
...
(罗马书 12:6-8 和合本)

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏
```

### 周六通知示例
```
【明天3月22日主日事工提醒】🕊️

• 音控：靖铮
• 导播/摄影：待安排
• ProPresenter播放：Joe
• ProPresenter更新：忠涵
• 视频剪辑：Roxy

请提前做好准备，按时到场。

愿神祝福！
```

## 触发

Cloud Scheduler 每 4 小时调用一次：
```
POST https://[CLOUD_RUN_URL]/generate-ics
```

## ICS 文件位置

```
https://storage.googleapis.com/grace-irvine-ministry-scheduler/calendars/grace_irvine_coordinator.ics
```

## 数据格式

### Google Sheets 表格结构

表格需要包含以下列（列名会自动匹配）：

| 列名 | 说明 | 匹配模式 |
|------|------|----------|
| 主日日期 | 主日日期 | 主日日期、date、主日 |
| 音控 | 音控人员 | 音控、audio、sound |
| 导播/摄影 | 导播或摄影人员 | 导播/摄影、导播、摄影 |
| ProPresenter播放 | PPT播放人员 | ProPresenter播放、ppt播放 |
| ProPresenter更新 | PPT更新人员 | ProPresenter更新、ppt更新 |
| 视频剪辑 | 视频剪辑人员 | 视频剪辑、video editor |

**注意：**
- 第1行：部门标题（会被跳过）
- 第2行：列名（程序会读取这一行作为表头）
- 第3行开始：数据行
- 程序会自动过滤 2026 年以前的数据

## 修改配置（无需重新部署）

```bash
# 修改周三时间为 20:00-22:00
gcloud run services update grace-irvine-ics-generator-v2 \
    --set-env-vars="WEDNESDAY_HOUR=20,WEDNESDAY_DURATION=120" \
    --region=us-central1

# 修改经文
gcloud run services update grace-irvine-ics-generator-v2 \
    --set-env-vars='SCRIPTURES=["看哪，弟兄和睦同居...","又要彼此相顾..."]'
```

## 技术细节

- **列名匹配**：智能匹配，支持中英文变体，优先匹配更精确的列名
- **日期解析**：支持 MM/DD/YYYY 格式
- **空缺处理**：空缺岗位显示"待安排"，方便识别需要安排的岗位
- **经文轮换**：根据日期自动轮换 8 条预设经文
- **换行符**：使用真实换行符，复制到微信群时格式正确

## 开发团队

Grace Irvine Ministry Scheduler Team
