# ICS日历提醒时间配置功能 ⏰

## 功能概述

新增的ICS日历提醒时间配置功能允许用户在前端界面灵活编辑日历提醒时间，包括事件发生时间（周几几点）和提醒提前时间。配置自动保存到云端/本地，每次生成ICS文件时会自动读取并应用这些配置。

## 🎯 主要特性

### 1. 灵活的时间配置
- **事件时间设置**: 自定义事件在一周中的哪一天、几点几分发生
- **持续时间配置**: 设置事件的持续时间（分钟）
- **提醒时间组合**: 支持天、小时、分钟的任意组合
  - 例如：提前1天2小时30分钟
  - 自动转换为标准ICS格式（如：`-P1DT2H30M`）

### 2. 前端可视化编辑
- **直观的界面**: 下拉菜单选择星期几，数字输入框设置时间
- **实时预览**: 编辑过程中即时显示配置效果
- **配置验证**: 自动验证输入的合理性并提示错误
- **测试功能**: 一键测试配置，显示下次事件和提醒时间

### 3. 智能配置管理
- **云端优先**: 优先从Google Cloud Storage读取和保存配置
- **本地备份**: 同时保存到本地作为备份，确保离线可用
- **自动同步**: 部署后自动初始化云端配置
- **状态监控**: 实时显示云端和本地配置的同步状态
- **强制同步**: 支持手动强制同步到云端
- **版本管理**: 支持配置导出、导入和重置
- **默认配置**: 内置合理的默认设置

### 4. 无缝集成
- **向后兼容**: 如果没有配置，自动使用原有的默认设置
- **自动应用**: 生成ICS文件时自动读取最新配置
- **错误容忍**: 配置读取失败时优雅降级到默认设置

## 🔧 技术实现

### 核心组件

#### 1. ReminderConfigManager
```python
# 提醒配置管理器
from src.reminder_config_manager import get_reminder_manager

manager = get_reminder_manager()
configs = manager.get_all_configs()
```

#### 2. 配置数据结构
```python
@dataclass
class NotificationConfig:
    event_type: str           # 事件类型
    name: str                # 配置名称
    description: str         # 描述
    event_timing: EventTiming    # 事件时间
    reminder_timing: ReminderTiming  # 提醒时间
    enabled: bool = True     # 是否启用

@dataclass
class EventTiming:
    weekday: int            # 星期几 (0=Monday, 6=Sunday)
    hour: int              # 小时 (0-23)
    minute: int            # 分钟 (0-59)
    duration_minutes: int  # 持续时间

@dataclass
class ReminderTiming:
    minutes_before: int    # 提前分钟数
    hours_before: int = 0  # 提前小时数
    days_before: int = 0   # 提前天数
```

#### 3. ICS生成集成
```python
# 增强的ICS事件创建函数
def create_ics_event(uid, summary, description, start_dt, end_dt, 
                    location="", reminder_trigger="-PT30M"):
    # 自动使用配置的提醒触发器
```

### 配置文件格式
```json
{
  "version": "1.0",
  "last_updated": "2025-09-15T16:39:54.724",
  "description": "Grace Irvine Ministry Scheduler - 提醒时间配置",
  "reminder_configs": {
    "weekly_confirmation": {
      "event_type": "weekly_confirmation",
      "name": "周三确认通知",
      "description": "发送周末服事安排确认通知",
      "event_timing": {
        "weekday": 2,
        "hour": 20,
        "minute": 0,
        "duration_minutes": 30
      },
      "reminder_timing": {
        "minutes_before": 30,
        "hours_before": 0,
        "days_before": 0
      },
      "enabled": true
    }
  }
}
```

## 📱 使用方法

### 1. 访问配置界面
1. 启动应用：`streamlit run app_unified.py`
2. 在侧边栏选择 "⏰ 提醒设置"
3. 进入配置编辑页面

### 2. 编辑配置
1. **选择配置**: 从下拉菜单选择要编辑的通知类型
2. **基本设置**: 
   - 启用/禁用开关
   - 修改配置名称和描述
3. **事件时间设置**:
   - 选择星期几
   - 设置小时和分钟
   - 配置持续时间
4. **提醒时间设置**:
   - 设置提前天数（0-7天）
   - 设置提前小时数（0-23小时）
   - 设置提前分钟数（0-59分钟）

### 3. 保存和测试
1. **实时预览**: 查看配置效果
2. **测试配置**: 点击"🧪 测试配置"验证设置
3. **保存配置**: 点击"💾 保存配置"应用更改
4. **重置默认**: 如需要可重置为默认设置

### 4. 高级功能
- **导出配置**: 下载配置文件作为备份
- **查看存储状态**: 监控云端和本地同步状态
- **配置总览**: 在"📊 配置预览"标签页查看所有配置

## 🎪 预设配置

### 默认配置
```
周三确认通知:
  - 事件时间: 周三 20:00
  - 持续时间: 30分钟
  - 提醒时间: 提前30分钟
  - 状态: 启用

周六提醒通知:
  - 事件时间: 周六 20:00
  - 持续时间: 30分钟
  - 提醒时间: 提前30分钟
  - 状态: 启用

月度总览通知:
  - 事件时间: 周日 19:00
  - 持续时间: 30分钟
  - 提醒时间: 提前2小时
  - 状态: 禁用（默认）
```

### 常用提醒时间设置
- **即时提醒**: 0分钟前 → `-PT0M`
- **短期提醒**: 15分钟前 → `-PT15M`
- **标准提醒**: 30分钟前 → `-PT30M`
- **提前提醒**: 1小时前 → `-PT1H`
- **早期提醒**: 2小时前 → `-PT2H`
- **日前提醒**: 1天前 → `-P1D`
- **组合提醒**: 1天2小时前 → `-P1DT2H`

## 🛠️ 开发者指南

### 扩展新的通知类型
1. 在`get_default_configs()`中添加新配置
2. 在`generate_coordinator_calendar()`中添加相应的处理逻辑
3. 更新前端界面以支持新的配置选项

### 自定义配置验证
```python
def validate_config(self, config: NotificationConfig) -> List[str]:
    """添加自定义验证规则"""
    errors = []
    
    # 添加业务逻辑验证
    if config.event_type == 'weekly_confirmation':
        if config.event_timing.weekday not in [1, 2, 3]:  # 只允许周二到周四
            errors.append("周三确认通知只能在周二到周四")
    
    return errors
```

### API集成
```python
# 通过API获取配置
GET /api/reminder-config/{event_type}

# 更新配置
POST /api/reminder-config/{event_type}
{
  "event_timing": {...},
  "reminder_timing": {...},
  "enabled": true
}
```

## 📊 配置示例

### 灵活的工作时间配置
```python
# 早会提醒：周一9点，提前1天
early_meeting = NotificationConfig(
    event_type='early_meeting',
    name='周一早会提醒',
    event_timing=EventTiming(weekday=0, hour=9, minute=0),
    reminder_timing=ReminderTiming(days_before=1)
)

# 紧急通知：当天，提前2小时
urgent_notice = NotificationConfig(
    event_type='urgent_notice',
    name='紧急通知',
    event_timing=EventTiming(weekday=6, hour=14, minute=0),
    reminder_timing=ReminderTiming(hours_before=2)
)
```

### 季节性配置调整
```python
# 夏季时间：提前更多时间
summer_config = ReminderTiming(hours_before=3)

# 冬季时间：标准提醒
winter_config = ReminderTiming(minutes_before=30)
```

## 🔮 未来扩展

1. **多时区支持**: 支持不同时区的时间配置
2. **条件触发**: 基于特殊日期或条件的动态配置
3. **批量配置**: 一次性配置多个相关事件
4. **模板系统**: 保存和应用配置模板
5. **统计分析**: 配置使用情况和效果分析
6. **移动端适配**: 响应式设计优化

## 🚀 部署注意事项

### 环境变量
```bash
# 云端存储配置
export GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler
export GOOGLE_CLOUD_PROJECT=ai-for-god
export STORAGE_MODE=cloud
```

### 权限要求
- 云端模式需要GCS读写权限
- 本地模式需要文件系统写权限

### 迁移指南
1. 现有系统无需修改，自动使用默认配置
2. 首次运行会创建默认配置文件
3. 可以逐步迁移到自定义配置

### 云端部署初始化
```bash
# 部署后运行初始化脚本
python3 scripts/init_cloud_config.py
```

### 配置文件结构
```
configs/
├── default_reminder_settings.json    # 默认配置模板
├── reminder_settings.json           # 用户配置（自动生成）
└── cloud_deployment.json           # 部署配置
```

### 故障排除
1. **配置无法保存到云端**:
   - 检查GCS权限设置
   - 验证环境变量配置
   - 使用"强制云端同步"按钮

2. **配置丢失**:
   - 系统会自动从本地备份恢复
   - 或使用默认配置初始化

3. **同步状态异常**:
   - 使用"重新加载配置"功能
   - 检查网络连接和云端服务状态

## 📈 性能优化

1. **配置缓存**: 使用单例模式减少重复加载
2. **懒加载**: 按需加载配置文件
3. **异步保存**: 非阻塞的配置保存操作
4. **错误恢复**: 自动从备份恢复损坏的配置

---

**开发完成日期**: 2025年9月15日  
**版本**: v1.0  
**开发者**: AI助手  
**项目**: Grace Irvine Ministry Scheduler

**测试状态**: ✅ 所有功能测试通过（5/5个测试）  
**部署状态**: 🚀 已集成到主应用，可立即使用
