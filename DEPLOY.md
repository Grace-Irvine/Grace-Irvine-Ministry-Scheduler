# Grace Irvine ICS Generator - 部署说明

## 架构变更

### 旧架构
- 多个 Cloud Functions
- 复杂的模板系统 (dynamic_template_manager.py)
- 分散的代码逻辑

### 新架构
- 单个 Cloud Run 服务
- 精简的代码 (main.py 一个文件)
- 智能列匹配
- 灵活的配置选项

## 文件变更

### 新增/修改
```
main.py              # 新的主入口 (替代 cloud_functions/update_ics_calendars.py)
requirements.txt     # 精简依赖
Dockerfile           # Cloud Run 容器配置
```

### 可删除（重构后）
```
src/ 目录下的大部分文件
cloud_functions/ 目录
scripts/ 目录
app_unified.py
streamlit_*.py
```

## 部署步骤

### 1. 配置 Secret Manager

在 Google Cloud Console 中设置以下 Secret：

```bash
# 创建 Secret
gcloud secrets create grace-irvine-spreadsheet-id \
    --data-file="-" \
    --project=ai-for-god

# 设置值 (替换为实际的 Spreadsheet ID)
echo -n "1wescUQe9rIVLNcKdqmSLpzlAw9BGXMZmkFvjEF296nM" | \
    gcloud secrets versions add grace-irvine-spreadsheet-id --data-file="-"
```

### 2. 部署 Cloud Run

```bash
# 构建镜像
gcloud builds submit --tag gcr.io/ai-for-god/grace-irvine-ics-generator

# 部署服务
gcloud run deploy grace-irvine-ics-generator \
    --image gcr.io/ai-for-god/grace-irvine-ics-generator \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets="GOOGLE_SPREADSHEET_ID=grace-irvine-spreadsheet-id:latest" \
    --set-env-vars="GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler"
```

### 3. 配置 Cloud Scheduler

```bash
# 创建每4小时触发一次的 Job
gcloud scheduler jobs create http grace-irvine-ics-updater \
    --schedule="0 */4 * * *" \
    --uri="https://grace-irvine-ics-generator-xxx.run.app/generate-ics" \
    --http-method=POST \
    --time-zone="America/Los_Angeles" \
    --location=us-central1 \
    --project=ai-for-god
```

## 环境变量配置

### 必需
- `GOOGLE_SPREADSHEET_ID`: Google Sheets ID
- `GCP_STORAGE_BUCKET`: 存储桶名称 (默认: grace-irvine-ministry-scheduler)

### 当前默认配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ICS_WEEKS_AHEAD` | 4 | 生成未来几周的事件 |
| `WEDNESDAY_ENABLED` | true | 是否启用周三通知 |
| `WEDNESDAY_WEEKDAY` | 2 | 周三 (2=周三) |
| `WEDNESDAY_HOUR` | 19 | **晚上 7 点** |
| `WEDNESDAY_MINUTE` | 0 | |
| `WEDNESDAY_DURATION` | 120 | **持续 2 小时** (19:00-21:00) |
| `SATURDAY_ENABLED` | true | 是否启用周六通知 |
| `SATURDAY_WEEKDAY` | 5 | 周六 (5=周六) |
| `SATURDAY_HOUR` | 9 | **早上 9 点** |
| `SATURDAY_MINUTE` | 0 | |
| `SATURDAY_DURATION` | 60 | **持续 1 小时** (09:00-10:00) |

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

**示例：更新经文**
```bash
gcloud run services update grace-irvine-ics-generator \
    --set-env-vars='SCRIPTURES=["看哪，弟兄和睦同居...","又要彼此相顾..."]'
```

### 配置示例

```bash
# 当前配置（周三 19:00-21:00，周六 09:00-10:00）
WEDNESDAY_HOUR=19
WEDNESDAY_DURATION=120
SATURDAY_HOUR=9
SATURDAY_DURATION=60

# 改为只生成未来 2 周
ICS_WEEKS_AHEAD=2

# 改为周二和周五通知
WEDNESDAY_WEEKDAY=1      # 周二
SATURDAY_WEEKDAY=4       # 周五
```

## ICS 文件位置

重构后 ICS 文件位置保持不变：

```
https://storage.googleapis.com/grace-irvine-ministry-scheduler/calendars/grace_irvine_coordinator.ics
```

已订阅的用户无需重新订阅。

## 测试

```bash
# 本地测试
curl -X POST http://localhost:8080/generate-ics

# Cloud Run 测试
curl -X POST https://grace-irvine-ics-generator-xxx.run.app/generate-ics
```

## 回滚

如果需要回滚到旧版本：

```bash
# 重新部署旧版本
gcloud run deploy grace-irvine-ics-generator \
    --image gcr.io/ai-for-god/grace-irvine-ics-generator:OLD_TAG \
    --platform managed \
    --region us-central1
```
