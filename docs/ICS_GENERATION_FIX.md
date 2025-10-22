# ICS日历生成修复文档

## 修复日期: 2025-10-22

## 问题描述

### 问题1: 每次重新生成ICS时删除过去的日历内容
- **现象**: ICS文件每次重新生成时只包含今天及未来的事件，导致过去的日历内容被删除
- **影响**: 用户订阅的日历会丢失历史记录，无法查看过去的通知安排

### 问题2: 经文选择每次重头开始
- **现象**: 每次重新生成ICS文件时，经文都从第一个开始
- **原因**: 
  - 生成ICS文件时为每个未来周次（15周）都调用 `get_next_scripture()`
  - 每次调用都会递增经文索引
  - 但用户实际只发送当周的通知，其他周的经文都被浪费
  - 导致经文索引快速递增，但实际使用的总是开头几段

## 修复方案

### 修复1: 保留过去的日历事件

修改了以下文件，保留过去4周的事件：
- `src/calendar_generator.py`
- `scripts/ics_background_service.py`
- `cloud_functions/update_ics_calendars.py`

**修改内容**:
```python
# 修改前
future_assignments = [a for a in assignments if a.date >= today][:15]

# 修改后
cutoff_date = today - timedelta(days=28)  # 4周前
relevant_assignments = [a for a in assignments if a.date >= cutoff_date][:19]  # 4周过去 + 15周未来
```

**优点**:
- 用户可以查看过去4周的通知记录
- 避免日历订阅者丢失历史信息
- 对于回顾和审计很有帮助

### 修复2: 使用基于日期的稳定经文选择

#### 2.1 在 `ScriptureManager` 中添加新方法

文件: `src/scripture_manager.py`

添加了 `get_scripture_by_date()` 方法：
```python
def get_scripture_by_date(self, target_date) -> Optional[Dict[str, Any]]:
    """根据日期获取稳定的经文（用于ICS生成，不会递增索引）
    
    基于日期生成一个稳定的索引，确保同一日期总是返回相同的经文。
    这样在重新生成ICS文件时不会导致经文索引快速递增。
    """
```

**工作原理**:
- 使用自2020年1月1日以来的周数来选择经文
- 同一周的不同生成会使用相同的经文
- 不会递增全局的经文索引

#### 2.2 在 `DynamicTemplateManager` 中添加参数

文件: `src/dynamic_template_manager.py`

修改 `render_weekly_confirmation()` 方法，添加 `for_ics_generation` 参数：
```python
def render_weekly_confirmation(self, sunday_date: date, schedule, for_ics_generation: bool = False) -> str:
    """渲染周三确认通知
    
    Args:
        for_ics_generation: 是否用于ICS生成（True时使用基于日期的固定经文，False时使用递增的经文索引）
    """
    if for_ics_generation:
        # ICS生成时：使用基于日期的固定经文
        current_scripture = self.scripture_manager.get_scripture_by_date(sunday_date)
    else:
        # 实际发送通知时：使用递增索引的经文
        current_scripture = self.scripture_manager.get_next_scripture()
```

#### 2.3 更新ICS生成调用

文件: `src/calendar_generator.py`

所有生成ICS的地方都传入 `for_ics_generation=True`：
```python
# 修改前
notification_content = dynamic_template_manager.render_weekly_confirmation(schedule.date, schedule)

# 修改后
notification_content = dynamic_template_manager.render_weekly_confirmation(schedule.date, schedule, for_ics_generation=True)
```

**优点**:
- 每个日期的经文是固定的，重新生成ICS不会改变
- 不会浪费经文索引
- 实际发送通知时仍然使用递增的经文索引（保持原有行为）

## 使用说明

### ICS生成调用

生成ICS文件时：
```python
# 使用基于日期的固定经文
content = manager.render_weekly_confirmation(sunday_date, schedule, for_ics_generation=True)
```

实际发送通知时：
```python
# 使用递增的经文索引
content = manager.render_weekly_confirmation(sunday_date, schedule, for_ics_generation=False)
# 或者省略参数（默认为False）
content = manager.render_weekly_confirmation(sunday_date, schedule)
```

### 经文管理

查看当前经文索引：
```python
from src.scripture_manager import get_scripture_manager
manager = get_scripture_manager()
stats = manager.get_scripture_stats()
print(f"当前索引: {stats['current_index']}")
print(f"经文总数: {stats['total_count']}")
```

手动重置经文索引：
```python
manager.reset_index()
```

## 测试建议

1. **测试日历历史记录**:
   - 生成ICS文件
   - 等待几天后重新生成
   - 验证过去的事件仍然存在

2. **测试经文稳定性**:
   - 生成ICS文件，记录某个日期的经文
   - 重新生成ICS文件
   - 验证同一日期的经文没有改变

3. **测试经文索引**:
   - 记录当前经文索引
   - 生成ICS文件
   - 验证经文索引没有快速递增

## 注意事项

1. **兼容性**: 
   - 旧的模板管理器 (`NotificationTemplateManager`) 不支持经文功能
   - 只有使用 `DynamicTemplateManager` 的代码才支持经文

2. **向后兼容**:
   - `for_ics_generation` 参数默认为 `False`，保持原有行为
   - 不会影响现有的通知发送逻辑

3. **日历订阅更新**:
   - 用户的日历应用通常会自动刷新订阅
   - 建议设置合理的缓存时间（如1小时）

## 相关文件

### 主要修改
- `src/calendar_generator.py` - 主要的ICS生成器
- `src/scripture_manager.py` - 经文管理器
- `src/dynamic_template_manager.py` - 动态模板管理器

### 次要修改
- `scripts/ics_background_service.py` - 后台服务（旧模板）
- `cloud_functions/update_ics_calendars.py` - Cloud Function（旧模板）

## 后续改进建议

1. **统一模板管理器**: 
   - 考虑将所有代码迁移到 `DynamicTemplateManager`
   - 淘汰旧的 `NotificationTemplateManager`

2. **经文选择策略**:
   - 可以考虑更灵活的经文选择算法
   - 例如按照教会年历、节期等选择经文

3. **历史记录保留期**:
   - 目前保留4周，可以根据实际需求调整
   - 可以添加配置参数

4. **测试覆盖**:
   - 添加单元测试验证经文选择逻辑
   - 添加集成测试验证ICS生成

