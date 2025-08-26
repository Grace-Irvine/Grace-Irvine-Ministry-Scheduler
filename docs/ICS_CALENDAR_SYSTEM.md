# ICS日历系统使用指南

## 概述

ICS日历系统为Grace Irvine教会事工通知系统提供日历集成功能，支持生成两种类型的日历：

1. **负责人日历** - 用于提醒协调员发送各类通知
2. **同工日历** - 显示个人事工服事安排

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                  ICS Calendar System                        │
├─────────────────────────────────────────────────────────────┤
│  Google Sheets ←→ Data Sync ←→ ICS Generator ←→ Calendar   │
│                      ↓                          ↓          │
│              Template Engine              Config Manager    │
│                      ↓                          ↓          │
│              Notification Events          Subscription     │
│                                          Management        │
└─────────────────────────────────────────────────────────────┘
```

## 核心功能

### 1. 负责人日历 (Ministry Coordinator Calendar)

**功能**：生成通知发送提醒事件
- 周三晚上 20:00 - 发送周末确认通知
- 周六晚上 20:00 - 发送主日提醒通知  
- 每月1日 09:00 - 发送月度总览通知

**事件内容**：
- 标题：发送通知类型和日期
- 描述：包含完整的模板生成内容
- 提醒：事件前30分钟提醒
- 分类：通知提醒、事工协调

### 2. 同工日历 (Ministry Workers Calendar)

**功能**：显示个人服事安排
- 彩排时间：根据角色不同（9:00-9:30到场）
- 正式服事：主日敬拜时间（10:00-12:00）

**事件内容**：
- 标题：服事类型和角色
- 描述：具体职责和注意事项
- 提醒：彩排前60分钟，服事前30分钟
- 分类：事工服事、主日敬拜、具体角色

## 安装配置

### 1. 安装依赖

```bash
pip install icalendar==5.0.11 pytz==2023.3 schedule==1.2.0
```

### 2. 配置文件设置

编辑 `configs/calendar_config.yaml`：

```yaml
# 负责人日历配置
coordinator_calendar:
  calendar_name: "Grace Irvine 事工协调日历"
  notification_times:
    weekly_confirmation: "20:00"    # 周三通知时间
    sunday_reminder: "20:00"        # 周六通知时间
    monthly_overview: "09:00"       # 月初通知时间
  subscribers:
    - "coordinator@graceirvine.org"

# 同工日历配置
worker_calendar:
  calendar_name: "Grace Irvine 同工服事日历"
  service_times:
    rehearsal_time: "09:00"
    service_start: "10:00"
    service_end: "12:00"
  subscribers:
    - "worker1@graceirvine.org"

# 自动同步设置
sync_settings:
  sync_frequency_hours: 12        # 12小时同步一次
  auto_sync_enabled: true
  google_sheets_id: ""           # 从环境变量获取
```

### 3. 环境变量设置

在 `.env` 文件中设置：

```bash
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
```

## 使用方法

### 命令行工具

使用 `scripts/manage_ics_calendar.py` 管理日历系统：

#### 基本操作

```bash
# 查看系统状态
python scripts/manage_ics_calendar.py status

# 手动同步日历
python scripts/manage_ics_calendar.py sync

# 启动自动同步（持续运行）
python scripts/manage_ics_calendar.py start

# 停止自动同步
python scripts/manage_ics_calendar.py stop
```

#### 生成日历文件

```bash
# 生成所有类型日历
python scripts/manage_ics_calendar.py generate

# 只生成负责人日历
python scripts/manage_ics_calendar.py generate --type coordinator

# 只生成同工日历
python scripts/manage_ics_calendar.py generate --type worker

# 生成特定同工的个人日历
python scripts/manage_ics_calendar.py generate --worker-name "张三"
```

#### 管理订阅者

```bash
# 查看所有订阅者
python scripts/manage_ics_calendar.py subscribers list

# 添加订阅者到负责人日历
python scripts/manage_ics_calendar.py subscribers add --calendar-type coordinator --email "new@example.com"

# 移除订阅者
python scripts/manage_ics_calendar.py subscribers remove --calendar-type worker --email "old@example.com"
```

#### 维护操作

```bash
# 清理7天前的旧文件
python scripts/manage_ics_calendar.py cleanup

# 清理30天前的旧文件
python scripts/manage_ics_calendar.py cleanup --days 30
```

### 程序化使用

```python
from src.ics_manager import ICSManager
from src.calendar_scheduler import CalendarScheduler
from src.scheduler import GoogleSheetsExtractor

# 初始化组件
extractor = GoogleSheetsExtractor(spreadsheet_id)
ics_manager = ICSManager()
scheduler = CalendarScheduler()

# 获取数据并生成日历
assignments = extractor.parse_ministry_data()
coordinator_calendar = ics_manager.generate_coordinator_calendar(assignments)
worker_calendar = ics_manager.generate_worker_calendar(assignments)

# 启动自动同步
scheduler.start_auto_sync()
```

## 日历文件结构

### 输出目录

默认输出到 `calendars/` 目录：

```
calendars/
├── coordinator_calendar_20241201_120000.ics    # 负责人日历
├── worker_calendar_all_20241201_120000.ics     # 综合同工日历
├── worker_calendar_张三_20241201_120000.ics     # 张三个人日历
└── worker_calendar_李四_20241201_120000.ics     # 李四个人日历
```

### 文件命名规则

- 负责人日历：`coordinator_calendar_{timestamp}.ics`
- 综合同工日历：`worker_calendar_all_{timestamp}.ics`  
- 个人日历：`worker_calendar_{worker_name}_{timestamp}.ics`

## 日历订阅

### 导入到日历应用

生成的ICS文件可以导入到各种日历应用：

1. **Google Calendar**
   - 打开Google Calendar
   - 点击"+"按钮 → "从文件导入"
   - 选择ICS文件上传

2. **Apple Calendar**
   - 双击ICS文件
   - 选择要导入的日历

3. **Outlook**
   - 文件 → 打开和导出 → 导入/导出
   - 选择"导入iCalendar或vCalendar文件"

### 订阅URL（高级功能）

如果部署到Web服务器，可以通过URL订阅：

```
https://your-server.com/calendars/coordinator_calendar_latest.ics
https://your-server.com/calendars/worker_calendar_all_latest.ics
```

## 自动同步机制

### 同步频率

默认每12小时自动同步一次，可在配置文件中调整：

```yaml
sync_settings:
  sync_frequency_hours: 12    # 修改为需要的小时数
  auto_sync_enabled: true     # 启用/禁用自动同步
```

### 同步流程

1. 从Google Sheets读取最新数据
2. 解析事工安排信息
3. 生成负责人日历（通知提醒事件）
4. 生成综合同工日历（所有人的服事安排）
5. 为每位同工生成个人日历
6. 更新同步状态和时间戳

### 同步监控

```bash
# 查看详细同步状态
python scripts/manage_ics_calendar.py status
```

输出示例：
```
📊 ICS日历系统状态
==================================================
🔄 自动同步状态: 运行中
⏰ 同步频率: 每 12 小时
📅 上次同步: 2024-12-01T12:00:00
🎯 下次同步: 2024-12-02T00:00:00
📝 同步状态: 同步成功 - 2024-12-01 12:00:00
🔧 自动同步: 启用
📁 日历文件: 8 个
```

## 故障排除

### 常见问题

1. **同步失败**
   - 检查Google Sheets访问权限
   - 确认service_account.json文件存在
   - 验证GOOGLE_SPREADSHEET_ID环境变量

2. **日历文件为空**
   - 检查Google Sheets中是否有有效数据
   - 确认日期格式正确
   - 查看同步日志

3. **自动同步不工作**
   - 确认auto_sync_enabled为true
   - 检查进程是否在运行
   - 查看错误日志

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 手动测试

```python
# 测试数据获取
from src.scheduler import GoogleSheetsExtractor
extractor = GoogleSheetsExtractor(spreadsheet_id)
assignments = extractor.parse_ministry_data()
print(f"获取到 {len(assignments)} 条记录")

# 测试日历生成
from src.ics_manager import ICSManager
ics_manager = ICSManager()
calendar_path = ics_manager.generate_coordinator_calendar(assignments)
print(f"日历已生成: {calendar_path}")
```

## 高级配置

### 自定义通知时间

```yaml
coordinator_calendar:
  notification_times:
    weekly_confirmation: "19:30"    # 周三晚上7:30
    sunday_reminder: "21:00"        # 周六晚上9:00
    monthly_overview: "08:00"       # 每月1日早上8:00
```

### 自定义服事时间

```yaml
worker_calendar:
  service_times:
    setup_time: "08:00"           # 提前布置
    rehearsal_time: "08:45"       # 彩排时间
    service_start: "09:30"        # 服事开始
    service_end: "11:30"          # 服事结束
```

### 时区设置

```yaml
coordinator_calendar:
  timezone: "America/Los_Angeles"  # 太平洋时区
# 或
  timezone: "Asia/Shanghai"        # 中国时区
```

## 集成建议

### 与现有系统集成

1. **邮件通知系统**
   - 可以在发送邮件通知时同时更新日历
   - 将日历文件作为附件发送

2. **Streamlit界面**
   - 添加日历管理页面
   - 提供下载ICS文件的链接

3. **云部署**
   - 将日历文件上传到云存储
   - 提供公开的订阅URL

### 扩展功能

1. **多语言支持**
   - 中英文双语日历
   - 根据用户偏好生成

2. **移动端优化**
   - 生成适合移动设备的日历格式
   - 简化事件描述

3. **统计分析**
   - 同工参与频率统计
   - 服事时间分析

## 维护指南

### 定期维护

1. **清理旧文件**（建议每周执行）
   ```bash
   python scripts/manage_ics_calendar.py cleanup --days 7
   ```

2. **检查同步状态**（建议每日检查）
   ```bash
   python scripts/manage_ics_calendar.py status
   ```

3. **更新订阅者列表**（根据需要）
   ```bash
   python scripts/manage_ics_calendar.py subscribers list
   ```

### 备份建议

1. 定期备份配置文件 `configs/calendar_config.yaml`
2. 保存重要的日历文件版本
3. 备份同工邮箱列表

### 性能优化

1. 合理设置同步频率（避免过于频繁）
2. 定期清理旧日历文件
3. 监控输出目录大小

## 支持联系

如有问题或建议，请联系技术支持团队。

---

*Grace Irvine Ministry Scheduler - ICS Calendar System v1.0*
