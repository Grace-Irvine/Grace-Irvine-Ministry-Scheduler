# ICS 文件测试指南

## 📋 测试方法

### 1. 本地测试脚本

使用提供的测试脚本进行快速测试：

```bash
# 运行完整测试
python scripts/test_ics_generation.py
```

这个脚本会：
- ✅ 测试 JSON 数据读取器
- ✅ 测试 ICS 配置加载
- ✅ 生成所有类型的 ICS 文件
- ✅ 验证 ICS 文件格式
- ✅ 保存测试文件到 `calendars/` 目录

### 2. 手动测试 ICS 生成

```python
# 测试单个日历生成
from src.multi_calendar_generator import generate_media_team_calendar

ics_content = generate_media_team_calendar()
if ics_content:
    # 保存到文件
    with open('calendars/test.ics', 'w', encoding='utf-8') as f:
        f.write(ics_content)
    print("✅ ICS 文件生成成功")
```

### 3. API 测试

#### 启动 API 服务
```bash
# 设置环境变量
export DATA_SOURCE_BUCKET=grace-irvine-ministry-data
export GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler
export GOOGLE_CLOUD_PROJECT=ai-for-god
export SCHEDULER_AUTH_TOKEN=grace-irvine-scheduler-2025

# 启动服务
python start_api.py
```

#### 测试 API 端点

```bash
# 1. 更新所有 ICS 日历
curl -X POST "http://localhost:8080/api/update-ics" \
  -H "X-Auth-Token: grace-irvine-scheduler-2025" \
  -H "Content-Type: application/json"

# 2. 下载媒体部日历
curl "http://localhost:8080/calendars/media-team.ics" -o test_media.ics

# 3. 下载儿童部日历
curl "http://localhost:8080/calendars/children-team.ics" -o test_children.ics

# 4. 获取系统状态
curl "http://localhost:8080/api/status" | jq
```

## 🔍 ICS 文件验证

### 1. 格式验证

ICS 文件必须包含以下元素：
- ✅ `BEGIN:VCALENDAR`
- ✅ `VERSION:2.0`
- ✅ `END:VCALENDAR`
- ✅ 每个事件必须有 `BEGIN:VEVENT` 和 `END:VEVENT`
- ✅ 每个事件必须有 `UID`, `DTSTART`, `DTEND`, `SUMMARY`

### 2. 使用在线工具验证

- **ICS Validator**: https://icalendar.org/validator.html
- **iCal Validator**: https://severinghaus.org/projects/icv/

上传生成的 ICS 文件进行验证。

### 3. 命令行验证

```bash
# 检查文件格式
grep -E "^(BEGIN|END):VCALENDAR" test.ics
grep -E "^(BEGIN|END):VEVENT" test.ics | wc -l

# 检查事件数量
grep -c "BEGIN:VEVENT" test.ics

# 检查必需字段
grep -E "^(UID|DTSTART|DTEND|SUMMARY)" test.ics
```

## 📱 在日历应用中测试

### macOS (日历应用)

1. 打开日历应用
2. 选择 "文件" > "导入"
3. 选择生成的 ICS 文件
4. 选择要导入的日历
5. 检查事件是否正确显示

### Google Calendar

1. 打开 Google Calendar
2. 点击左侧的设置（齿轮图标）
3. 选择 "导入和导出"
4. 点击 "选择文件从计算机导入"
5. 选择 ICS 文件
6. 选择要导入的日历
7. 点击 "导入"

### iOS (iPhone/iPad)

1. 将 ICS 文件发送到设备（通过邮件或 AirDrop）
2. 点击文件
3. 选择 "添加到日历"
4. 选择要导入的日历
5. 检查事件是否正确显示

### Outlook

1. 打开 Outlook
2. 选择 "文件" > "打开和导出" > "导入/导出"
3. 选择 "从 iCalendar (.ics) 或 vCalendar 文件导入"
4. 选择 ICS 文件
5. 选择要导入的日历
6. 点击 "导入"

## 🔗 订阅测试（生产环境）

### 1. 获取订阅 URL

```bash
# 从 API 获取状态
curl "http://your-api-url/api/status" | jq '.calendars'
```

### 2. 在日历应用中订阅

#### Google Calendar
1. 打开 Google Calendar
2. 点击左侧的 "+" 号
3. 选择 "从 URL 添加"
4. 输入日历 URL: `https://your-api-url/calendars/media-team.ics`
5. 点击 "添加日历"

#### macOS Calendar
1. 打开日历应用
2. 选择 "文件" > "新建日历订阅"
3. 输入日历 URL: `https://your-api-url/calendars/media-team.ics`
4. 点击 "订阅"

#### iOS Calendar
1. 打开"设置" > "日历" > "账户" > "添加账户"
2. 选择 "其他" > "添加已订阅的日历"
3. 输入日历 URL: `https://your-api-url/calendars/media-team.ics`
4. 点击 "下一步"

## 🧪 测试清单

### 数据源测试
- [ ] JSON 数据读取器能够连接 GCS bucket
- [ ] 能够读取 `service-layer/latest.json`
- [ ] 能够解析媒体部数据
- [ ] 能够解析儿童部数据

### 配置测试
- [ ] ICS 配置能够正确加载
- [ ] 能够读取通知时间配置
- [ ] 配置的默认值正确

### ICS 生成测试
- [ ] 媒体部日历生成成功
- [ ] 儿童部日历生成成功
- [ ] ICS 文件格式正确
- [ ] 事件数量符合预期
- [ ] 事件时间正确（相对于主日）
- [ ] 事件描述内容完整

### API 测试
- [ ] `/api/update-ics` 端点正常工作
- [ ] `/calendars/{type}.ics` 端点能够下载文件
- [ ] `/api/status` 端点显示正确的状态
- [ ] 认证机制正常工作

### 日历应用测试
- [ ] ICS 文件能够导入到日历应用
- [ ] 事件显示正确
- [ ] 提醒功能正常工作
- [ ] 订阅功能正常工作（生产环境）

## 🐛 常见问题

### 问题 1: 无法读取数据源
**症状**: 测试脚本显示"未读取到数据"

**解决方案**:
1. 检查环境变量 `DATA_SOURCE_BUCKET` 是否正确
2. 检查 GCS bucket 是否存在
3. 检查服务账号权限
4. 检查 `service-layer/latest.json` 文件是否存在

### 问题 2: ICS 文件格式错误
**症状**: 日历应用无法导入文件

**解决方案**:
1. 检查 ICS 文件是否包含必需的字段
2. 检查日期时间格式是否正确
3. 检查特殊字符是否正确转义
4. 使用在线验证工具验证格式

### 问题 3: 事件数量为 0
**症状**: 生成的 ICS 文件没有事件

**解决方案**:
1. 检查数据源中是否有未来的日期
2. 检查配置中的 `relative_to_sunday` 是否正确
3. 检查事件日期是否在保留范围内（过去4周）
4. 检查日历配置是否启用

### 问题 4: 事件时间不正确
**症状**: 事件显示的时间不对

**解决方案**:
1. 检查配置中的 `time` 字段格式（应为 `HH:MM`）
2. 检查 `relative_to_sunday` 是否正确
3. 检查时区设置（应为 `America/Los_Angeles`）
4. 检查日期计算逻辑

## 📚 相关文档

- [新 ICS 系统架构设计](NEW_ICS_ARCHITECTURE.md)
- [新 ICS 系统实现总结](NEW_ICS_IMPLEMENTATION.md)

