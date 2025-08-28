# ICS日历自动更新部署指南

## 概述

要实现双击添加ICS后能自动更新，我们需要部署**ICS日历订阅服务**，而不是一次性导入。当Google Sheets数据变化时，订阅的日历会自动更新。

## 🎯 解决方案

### 方案1: 静态文件订阅 (推荐)

#### 特点：
- ✅ 简单易部署
- ✅ 兼容性好
- ✅ 成本低
- ✅ 维护简单

#### 实现步骤：

1. **生成固定文件名的日历**
```bash
python3 scripts/update_static_calendars.py
```

2. **部署到Web服务器**
```bash
# 上传到你的Web服务器
scp calendars/grace_irvine_coordinator.ics user@your-server.com:/var/www/html/calendars/
scp calendars/grace_irvine_workers.ics user@your-server.com:/var/www/html/calendars/
```

3. **用户订阅固定URL**
```
负责人日历: https://your-server.com/calendars/grace_irvine_coordinator.ics
同工日历: https://your-server.com/calendars/grace_irvine_workers.ics
```

4. **设置自动更新**
```bash
# 在服务器上设置cron任务，每小时更新一次
0 * * * * cd /path/to/project && python3 scripts/update_static_calendars.py
```

### 方案2: HTTP订阅服务器

#### 特点：
- ✅ 实时更新
- ✅ 动态生成
- ✅ 状态监控
- ❌ 需要持续运行

#### 实现步骤：

1. **启动订阅服务器**
```bash
python3 scripts/start_calendar_server.py --port 8080
```

2. **用户订阅动态URL**
```
负责人日历: http://your-server.com:8080/coordinator.ics
同工日历: http://your-server.com:8080/workers.ics
个人日历: http://your-server.com:8080/worker/张三.ics
```

### 方案3: 云端部署 (最佳)

#### 使用Google Cloud Run或其他云服务

## 📱 用户使用方法

### Google Calendar 订阅

1. **打开Google Calendar**
2. **点击左侧"+"号** → "从URL添加"
3. **输入订阅URL**:
   ```
   https://your-server.com/calendars/grace_irvine_coordinator.ics
   ```
4. **点击"添加日历"**

✅ **自动更新**: Google Calendar会定期检查URL并自动更新内容

### Apple Calendar 订阅

1. **打开Calendar应用**
2. **文件** → **新建日历订阅**
3. **输入订阅URL**
4. **点击订阅**

✅ **自动更新**: Apple Calendar会自动刷新订阅的日历

### Outlook 订阅

1. **打开Outlook**
2. **日历** → **添加日历** → **从Internet订阅**
3. **输入订阅URL**
4. **点击导入**

## 🔄 自动更新机制

### 更新流程

```
Google Sheets更新 → 定时脚本运行 → 重新生成ICS文件 → 日历应用自动刷新
```

### 更新频率设置

#### 服务器端更新
```bash
# 每小时更新（推荐）
0 * * * * cd /path/to/project && python3 scripts/update_static_calendars.py

# 每30分钟更新
*/30 * * * * cd /path/to/project && python3 scripts/update_static_calendars.py

# 持续监控模式
python3 scripts/update_static_calendars.py --watch
```

#### 客户端刷新
- **Google Calendar**: 每几小时自动检查
- **Apple Calendar**: 每15分钟到1小时检查一次
- **Outlook**: 可设置刷新频率

## 🚀 快速部署

### 本地测试

1. **生成静态文件**
```bash
python3 scripts/update_static_calendars.py
```

2. **启动简单HTTP服务器**
```bash
cd calendars/
python3 -m http.server 8000
```

3. **测试订阅**
```
http://localhost:8000/grace_irvine_coordinator.ics
```

### 生产部署

#### 使用现有的Streamlit部署

1. **添加到Streamlit应用**
```python
import streamlit as st

# 在streamlit_app.py中添加
@st.cache_data(ttl=3600)  # 1小时缓存
def get_coordinator_calendar():
    # 调用日历生成逻辑
    pass

# 提供下载链接
if st.button("下载负责人日历"):
    calendar_content = get_coordinator_calendar()
    st.download_button(
        label="📅 下载ICS文件",
        data=calendar_content,
        file_name="grace_irvine_coordinator.ics",
        mime="text/calendar"
    )
```

#### 使用Google Cloud Run

1. **修改Dockerfile**
```dockerfile
# 添加日历服务
EXPOSE 8080
CMD ["python3", "scripts/start_calendar_server.py", "--port", "8080"]
```

2. **部署到Cloud Run**
```bash
gcloud run deploy grace-irvine-calendar --source .
```

## 📊 监控和维护

### 检查更新状态

```bash
# 查看最后更新时间
ls -la calendars/grace_irvine_*.ics

# 检查文件内容
grep "X-WR-CALDESC:最后更新" calendars/grace_irvine_coordinator.ics
```

### 自动化监控

```bash
#!/bin/bash
# monitor_calendar_updates.sh

LOG_FILE="/var/log/grace_irvine_calendar.log"

echo "$(date): 开始更新日历文件" >> $LOG_FILE

cd /path/to/project
python3 scripts/update_static_calendars.py >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    echo "$(date): 日历文件更新成功" >> $LOG_FILE
else
    echo "$(date): 日历文件更新失败" >> $LOG_FILE
    # 可以添加邮件通知逻辑
fi
```

## 🔧 高级配置

### 自定义刷新频率

在ICS文件中添加刷新间隔：

```ics
REFRESH-INTERVAL;VALUE=DURATION:PT1H  # 1小时刷新一次
```

### 版本控制

```python
# 在ICS文件中添加版本信息
f"X-WR-CALDESC:版本: {datetime.now().strftime('%Y%m%d%H%M')}"
```

### 缓存策略

```python
# HTTP响应头设置
self.send_header('Cache-Control', 'max-age=3600')  # 1小时缓存
self.send_header('ETag', f'"{version_hash}"')      # 版本标识
```

## 📋 用户订阅指南

### 一次性设置

1. **获取订阅URL**
2. **在日历应用中添加订阅**
3. **设置刷新频率**（如果支持）

### 验证自动更新

1. **修改Google Sheets中的数据**
2. **运行更新脚本**
3. **等待日历应用刷新**（通常几分钟到1小时）
4. **检查日历是否显示新内容**

## 🎯 推荐方案

**对于Grace Irvine教会，我推荐使用方案1（静态文件订阅）：**

1. **简单可靠** - 不需要复杂的服务器配置
2. **成本低** - 可以使用现有的Web服务器
3. **兼容性好** - 所有日历应用都支持
4. **易维护** - 只需要定期运行更新脚本

### 实施步骤：

```bash
# 1. 生成静态日历文件
python3 scripts/update_static_calendars.py

# 2. 上传到Web服务器
# 3. 设置定时任务每小时更新
# 4. 用户订阅固定URL
```

这样用户只需要一次订阅，之后日历会自动更新，无需手动重新导入！🎉

---

*Grace Irvine Ministry Scheduler - Auto-Update Calendar System v1.0*
