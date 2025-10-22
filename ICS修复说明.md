# ICS日历生成问题修复说明

## 修复日期
2025年10月22日

## 问题总结

您反映了两个主要问题：

### 问题1：每次重新生成ICS文件后，过去的日历内容被删除
**原因**：代码中使用了 `if s.date >= today` 的过滤条件，只保留今天及未来的事件。

**影响**：每次自动更新ICS文件时，过去的通知记录都会被删除，导致历史记录丢失。

### 问题2：每次重新生成后，经文又重头开始
**原因**：
- 生成ICS文件时，为未来15周的每个主日都调用 `get_next_scripture()`
- 每次调用都会递增经文索引
- 但实际上只发送了当周的通知，其他周的经文都被浪费了
- 导致经文索引快速递增，但实际发送的通知始终使用开头几段经文

## 修复方案

### 修复1：保留过去4周的日历事件

在以下文件中修改了日期过滤逻辑：
- `src/calendar_generator.py`
- `scripts/ics_background_service.py`
- `cloud_functions/update_ics_calendars.py`

**修改示例**：
```python
# 修改前（只保留今天之后的）
future_assignments = [a for a in assignments if a.date >= today][:15]

# 修改后（保留过去4周到未来15周）
cutoff_date = today - timedelta(days=28)  # 4周前
relevant_assignments = [a for a in assignments if a.date >= cutoff_date][:19]
```

**效果**：
- ✅ 日历中会保留过去4周的通知记录
- ✅ 不会因为重新生成而丢失历史信息
- ✅ 可以回顾过去的事工安排

### 修复2：使用基于日期的稳定经文选择

#### 步骤1：添加新的经文获取方法
在 `src/scripture_manager.py` 中添加了 `get_scripture_by_date()` 方法：

```python
def get_scripture_by_date(self, target_date):
    """根据日期获取稳定的经文
    
    - 基于日期计算经文索引
    - 同一日期总是返回相同的经文
    - 不会改变全局的经文索引
    """
```

**工作原理**：
- 计算从2020年1月1日到目标日期的周数
- 用周数对经文总数取模，得到稳定的经文索引
- 同一周的日期会得到相同的经文

#### 步骤2：模板管理器支持两种模式
在 `src/dynamic_template_manager.py` 中修改了 `render_weekly_confirmation()` 方法：

```python
def render_weekly_confirmation(self, sunday_date, schedule, for_ics_generation=False):
    """渲染周三确认通知
    
    Args:
        for_ics_generation: 是否用于ICS生成
            - True：使用基于日期的固定经文（不改变索引）
            - False：使用递增索引的经文（用于实际发送）
    """
    if for_ics_generation:
        # ICS生成：使用固定经文
        scripture = self.scripture_manager.get_scripture_by_date(sunday_date)
    else:
        # 实际发送：使用递增经文
        scripture = self.scripture_manager.get_next_scripture()
```

#### 步骤3：更新ICS生成代码
在 `src/calendar_generator.py` 中，所有生成ICS的地方都传入 `for_ics_generation=True`：

```python
# 生成ICS内容时
notification_content = dynamic_template_manager.render_weekly_confirmation(
    schedule.date, 
    schedule, 
    for_ics_generation=True  # 使用基于日期的固定经文
)
```

**效果**：
- ✅ 每次重新生成ICS时，同一日期的经文保持不变
- ✅ 不会浪费经文索引
- ✅ 实际发送通知时仍然按顺序使用经文
- ✅ 经文的使用更加合理和可预测

## 使用方式

### 生成ICS文件
系统会自动定期重新生成ICS文件，现在：
- 会保留过去4周的记录
- 每个日期的经文是固定的

### 发送通知
当实际发送通知时（不是生成ICS预览），系统会：
- 按顺序使用下一段经文
- 正常递增经文索引

### 查看经文状态
```python
from src.scripture_manager import get_scripture_manager

manager = get_scripture_manager()
stats = manager.get_scripture_stats()
print(f"当前索引: {stats['current_index']}")
print(f"经文总数: {stats['total_count']}")
```

## 测试验证

创建了测试脚本 `scripts/test_ics_fixes.py`，可以验证：
1. 经文选择的稳定性（同一日期多次生成得到相同经文）
2. 经文索引的稳定性（生成ICS不改变索引）
3. 模板渲染的正确性（ICS生成和实际发送使用不同模式）
4. 日期范围的正确性（包含过去的事件）

## 技术细节

### 修改的文件
1. **核心修改**：
   - `src/scripture_manager.py` - 添加基于日期的经文选择
   - `src/dynamic_template_manager.py` - 添加ICS生成模式支持
   - `src/calendar_generator.py` - 使用新的经文选择逻辑

2. **日期范围修改**：
   - `src/calendar_generator.py`
   - `scripts/ics_background_service.py`
   - `cloud_functions/update_ics_calendars.py`

### 向后兼容性
- `for_ics_generation` 参数默认为 `False`
- 现有的通知发送代码不需要修改
- 保持了原有的经文递增行为

### 配置说明
- 过去事件保留期：4周（28天）
- 未来事件范围：15周
- 总日历范围：过去4周 + 未来15周 = 约19周

## 注意事项

1. **日历订阅更新**：
   - 大多数日历应用会自动刷新订阅
   - 可能需要几分钟到几小时才能看到更新

2. **经文循环**：
   - 经文会按照自然顺序循环使用
   - 每周使用不同的经文
   - 循环周期取决于经文总数

3. **历史记录限制**：
   - 目前只保留过去4周
   - 如需更长时间，可以调整 `cutoff_date` 的天数

## 问题排查

如果发现经文还是有问题：
1. 检查正在使用的是哪个ICS生成脚本
2. 确认使用的是 `DynamicTemplateManager` 而不是旧的 `NotificationTemplateManager`
3. 查看日志确认 `get_scripture_by_date()` 被正确调用

如果历史事件还是被删除：
1. 检查 ICS 生成脚本是否已更新
2. 确认使用的是修改后的代码
3. 查看生成的 ICS 文件内容

## 联系与支持

如有问题或需要进一步调整，请查看：
- 详细技术文档：`docs/ICS_GENERATION_FIX.md`
- 测试脚本：`scripts/test_ics_fixes.py`

