# 通知模板自定义指南

## 📝 如何修改通知模板

### 1. 修改通知文本内容

模板内容在 `simple_scheduler.py` 文件的 `NotificationGenerator` 类中。三个主要方法对应三个模板：

#### 🔧 周三确认通知（模板1）

**位置：** `generate_weekly_confirmation()` 方法（约第254-262行）

**当前模板：**
```python
template = f"""【本周{month}月{day}日主日事工安排提醒】🕊️

• 音控：{assignment.audio_tech or '待安排'}
• 屏幕：{assignment.screen_operator or '待安排'}
• 摄像/导播：{assignment.camera_operator or '待安排'}
• Propresenter 制作：{assignment.propresenter or '待安排'}
• 视频剪辑：{assignment.video_editor}

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
```

**修改示例：**
```python
# 示例1：添加更多信息
template = f"""【本周{month}月{day}日主日事工安排提醒】🕊️

亲爱的同工们，主内平安！

本周服事安排如下：
• 音控：{assignment.audio_tech or '待安排'} 
• 屏幕：{assignment.screen_operator or '待安排'}
• 摄像/导播：{assignment.camera_operator or '待安排'}
• Propresenter 制作：{assignment.propresenter or '待安排'}
• 视频剪辑：{assignment.video_editor}

⏰ 到场时间：主日上午 9:00
📍 服事地点：主堂

请大家确认时间，若有冲突请尽快私信我，感谢摆上！
愿神祝福我们的服事 🙏"""

# 示例2：简化版本
template = f"""【{month}/{day} 主日事工】🕊️

音控:{assignment.audio_tech or 'TBD'} | 屏幕:{assignment.screen_operator or 'TBD'}
摄像:{assignment.camera_operator or 'TBD'} | 制作:{assignment.propresenter or 'TBD'}
剪辑:{assignment.video_editor}

有冲突请私信 🙏"""
```

#### 🔧 周六提醒通知（模板2）

**位置：** `generate_sunday_reminder()` 方法（约第274-281行）

**当前模板：**
```python
template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  
- 音控：{assignment.audio_tech or '待安排'} 9:00到，随敬拜团排练
- 屏幕：{assignment.screen_operator or '待安排'} 9:00到，随敬拜团排练
- 摄像/导播: {assignment.camera_operator or '待安排'} 9:30到，检查预设机位

愿主同在，出入平安。若临时不适请第一时间私信我。🙌"""
```

**修改示例：**
```python
# 示例1：添加详细信息
template = f"""【明日主日服事提醒】✨

亲爱的同工们，明天主日聚会安排：

📅 日期：{assignment.date.strftime('%Y年%m月%d日')} (主日)
⏰ 时间安排：
   8:30 - 布置会场
   9:00 - 敬拜彩排  
   10:00 - 正式敬拜

👥 服事同工：
• 音控：{assignment.audio_tech or '待安排'} (9:00到场)
• 屏幕：{assignment.screen_operator or '待安排'} (9:00到场)  
• 摄像/导播：{assignment.camera_operator or '待安排'} (9:30到场)
• 制作：{assignment.propresenter or '待安排'}

📍 地点：主堂
🅿️ 停车：教会停车场

愿主同在，出入平安！临时有事请立即私信。🙌
为明天的敬拜祷告 🙏"""

# 示例2：紧急提醒版
template = f"""🚨【明日主日紧急提醒】

⏰ 明天 8:30开始布置，请准时！

{assignment.audio_tech or 'TBD'}(音控) - 9:00到
{assignment.screen_operator or 'TBD'}(屏幕) - 9:00到  
{assignment.camera_operator or 'TBD'}(摄像) - 9:30到

有急事请立即联系！🙌"""
```

#### 🔧 月度总览通知（模板3）

**位置：** `generate_monthly_overview()` 方法（约第316-323行）

**当前模板：**
```python
template = f"""【{year}年{month:02d}月事工排班一览】📅
请各位同工先行预留时间，如有冲突尽快与我沟通：
{sheet_url}
{schedule_text}
温馨提示：
- 周三晚发布当周安排（确认/调换）
- 周六晚发布主日提醒（到场时间）
感谢大家同心配搭！🙏"""
```

**修改示例：**
```python
# 示例1：添加统计信息
total_services = len(assignments)
total_volunteers = len(set(person for assignment in assignments 
                          for person in [assignment.audio_tech, assignment.screen_operator, 
                                       assignment.camera_operator, assignment.propresenter] 
                          if person))

template = f"""【{year}年{month:02d}月事工排班一览】📅

亲爱的同工们，新的一月开始了！

📊 本月统计：
• 主日聚会：{total_services} 次
• 参与同工：{total_volunteers} 位
• 总服事次数：{len([p for a in assignments for p in [a.audio_tech, a.screen_operator, a.camera_operator, a.propresenter] if p])} 次

📋 详细安排请查看：
{sheet_url}

{schedule_text}

📌 重要提醒：
✓ 周三晚发布当周安排（确认/调换）
✓ 周六晚发布主日提醒（到场时间）
✓ 如有冲突请提前2周告知
✓ 临时调换请找到替补同工

感谢大家忠心的服事，愿神纪念！🙏"""

# 示例2：简洁版
template = f"""【{month}月排班】📅

{schedule_text}

表格链接：{sheet_url}

冲突请提前告知 🙏"""
```

### 2. 修改角色名称和映射

如果您的表格中角色名称不同，需要修改两个地方：

#### A. 数据结构定义

**位置：** `MinistryAssignment` 类（约第15-25行）

```python
@dataclass
class MinistryAssignment:
    date: date
    audio_tech: str = ""      # 音控 -> 可改为其他名称
    screen_operator: str = ""  # 屏幕 -> 可改为其他名称
    camera_operator: str = ""  # 摄像/导播 -> 可改为其他名称
    propresenter: str = ""     # Propresenter 制作 -> 可改为其他名称
    video_editor: str = "靖铮"  # 视频剪辑（固定）-> 可改为其他人
```

#### B. 数据解析映射

**位置：** `parse_ministry_data()` 方法（约第80-90行）

```python
assignment = MinistryAssignment(
    date=parsed_date,
    audio_tech=self._clean_name(row[1]),        # B列 - 修改这里的索引
    screen_operator=self._clean_name(row[2]),   # C列 - 对应您的列位置
    camera_operator=self._clean_name(row[3]),   # D列
    propresenter=self._clean_name(row[4]),      # E列
    video_editor="靖铮"  # 固定值 - 可修改
)
```

### 3. 添加新的角色

如果要添加新的事工角色，需要：

#### 步骤1：修改数据结构
```python
@dataclass
class MinistryAssignment:
    date: date
    audio_tech: str = ""
    screen_operator: str = ""
    camera_operator: str = ""
    propresenter: str = ""
    video_editor: str = "靖铮"
    # 添加新角色
    usher: str = ""           # 招待
    worship_leader: str = ""  # 敬拜主领
    pianist: str = ""         # 司琴
```

#### 步骤2：修改数据解析
```python
assignment = MinistryAssignment(
    date=parsed_date,
    audio_tech=self._clean_name(row[1]),
    screen_operator=self._clean_name(row[2]),
    camera_operator=self._clean_name(row[3]),
    propresenter=self._clean_name(row[4]),
    video_editor="靖铮",
    # 添加新列
    usher=self._clean_name(row[5]),           # F列
    worship_leader=self._clean_name(row[6]),  # G列
    pianist=self._clean_name(row[7]),         # H列
)
```

#### 步骤3：修改模板
```python
template = f"""【本周{month}月{day}日主日事工安排提醒】🕊️

• 音控：{assignment.audio_tech or '待安排'}
• 屏幕：{assignment.screen_operator or '待安排'}
• 摄像/导播：{assignment.camera_operator or '待安排'}
• Propresenter 制作：{assignment.propresenter or '待安排'}
• 视频剪辑：{assignment.video_editor}
• 招待：{assignment.usher or '待安排'}
• 敬拜主领：{assignment.worship_leader or '待安排'}
• 司琴：{assignment.pianist or '待安排'}

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
```

### 4. 修改时间和格式

#### 修改到场时间
在 `generate_sunday_reminder()` 方法中：

```python
# 当前版本
- 音控：{assignment.audio_tech or '待安排'} 9:00到，随敬拜团排练
- 屏幕：{assignment.screen_operator or '待安排'} 9:00到，随敬拜团排练
- 摄像/导播: {assignment.camera_operator or '待安排'} 9:30到，检查预设机位

# 修改为不同时间
- 音控：{assignment.audio_tech or '待安排'} 8:45到，准备设备
- 屏幕：{assignment.screen_operator or '待安排'} 9:00到，测试投影
- 摄像/导播: {assignment.camera_operator or '待安排'} 9:15到，调试机位
```

#### 修改日期格式
```python
# 当前：1月14日
month = assignment.date.month
day = assignment.date.day
date_str = f"{month}月{day}日"

# 修改为：2024年1月14日
date_str = f"{assignment.date.year}年{assignment.date.month}月{assignment.date.day}日"

# 修改为：1/14
date_str = f"{assignment.date.month}/{assignment.date.day}"

# 修改为：Jan 14
import locale
locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
date_str = assignment.date.strftime("%b %d")
```

### 5. 添加条件逻辑

您可以根据不同情况显示不同内容：

```python
def generate_weekly_confirmation(self) -> str:
    assignment = self.extractor.get_current_week_assignment()
    
    if not assignment:
        return "【本周主日事工安排提醒】🕊️\n\n暂无本周事工安排，请联系协调员确认。"
    
    # 检查是否是特殊节日
    month = assignment.date.month
    day = assignment.date.day
    
    special_note = ""
    if month == 12 and day >= 20:  # 圣诞节期间
        special_note = "\n🎄 圣诞节期间，请提前15分钟到场准备！"
    elif month == 1 and day == 1:  # 新年
        special_note = "\n🎊 新年第一个主日，愿神祝福新的开始！"
    elif month == 4 and 5 <= day <= 25:  # 复活节期间（大致时间）
        special_note = "\n🌅 复活节期间，感谢主的救恩！"
    
    # 检查是否有空缺
    missing_roles = []
    if not assignment.audio_tech:
        missing_roles.append("音控")
    if not assignment.screen_operator:
        missing_roles.append("屏幕")
    # ... 其他检查
    
    urgent_note = ""
    if missing_roles:
        urgent_note = f"\n⚠️ 紧急：仍需{', '.join(missing_roles)}同工，请尽快联系！"
    
    template = f"""【本周{month}月{day}日主日事工安排提醒】🕊️

• 音控：{assignment.audio_tech or '❌待安排'}
• 屏幕：{assignment.screen_operator or '❌待安排'}
• 摄像/导播：{assignment.camera_operator or '❌待安排'}
• Propresenter 制作：{assignment.propresenter or '❌待安排'}
• 视频剪辑：{assignment.video_editor}
{special_note}
{urgent_note}

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
    
    return template
```

## 🔧 实际修改步骤

### 1. 备份原文件
```bash
cp simple_scheduler.py simple_scheduler.py.backup
```

### 2. 编辑文件
```bash
# 使用任意文本编辑器
nano simple_scheduler.py
# 或
code simple_scheduler.py  # VS Code
# 或
vim simple_scheduler.py
```

### 3. 测试修改
```bash
python3 test_simple.py  # 运行测试确保没有语法错误
python3 generate_notifications.py weekly  # 测试实际输出
```

### 4. 常见问题排查

#### 缩进错误
Python 对缩进很敏感，确保修改后的代码缩进一致。

#### 引号问题
模板中如果包含引号，使用三重引号 `"""` 包围。

#### 变量名错误
确保使用正确的变量名，如 `assignment.audio_tech`。

## 📋 模板变量参考

在模板中可以使用的变量：

### 周三和周六模板
- `assignment.date` - 日期对象
- `assignment.audio_tech` - 音控人员
- `assignment.screen_operator` - 屏幕操作员
- `assignment.camera_operator` - 摄像/导播
- `assignment.propresenter` - Propresenter制作
- `assignment.video_editor` - 视频剪辑
- `assignment.notes` - 备注信息
- `month`, `day` - 月份和日期数字

### 月度模板
- `year`, `month` - 年份和月份
- `assignments` - 所有月度安排列表
- `schedule_text` - 格式化的安排文本
- `sheet_url` - Google Sheets链接

## 🎨 模板美化建议

### 1. 使用表情符号
```python
template = f"""🎵【本周{month}月{day}日主日事工安排提醒】🎵

🎤 音控：{assignment.audio_tech or '待安排'}
📺 屏幕：{assignment.screen_operator or '待安排'}
📹 摄像/导播：{assignment.camera_operator or '待安排'}
💻 Propresenter 制作：{assignment.propresenter or '待安排'}
✂️ 视频剪辑：{assignment.video_editor}

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏✨"""
```

### 2. 添加分割线
```python
template = f"""═══════════════════════
    恩典尔湾长老教会
═══════════════════════

【本周{month}月{day}日主日事工安排提醒】🕊️

• 音控：{assignment.audio_tech or '待安排'}
• 屏幕：{assignment.screen_operator or '待安排'}
• 摄像/导播：{assignment.camera_operator or '待安排'}
• Propresenter 制作：{assignment.propresenter or '待安排'}
• 视频剪辑：{assignment.video_editor}

─────────────────────────
请大家确认时间，若有冲突请尽快私信我
感谢摆上 🙏
─────────────────────────"""
```

### 3. 使用表格格式
```python
template = f"""【本周{month}月{day}日主日事工安排提醒】🕊️

┌─────────────┬──────────────┐
│   服事项目   │   负责同工    │
├─────────────┼──────────────┤
│     音控     │ {assignment.audio_tech or '待安排':^10} │
│     屏幕     │ {assignment.screen_operator or '待安排':^10} │
│   摄像/导播   │ {assignment.camera_operator or '待安排':^10} │
│ PP制作       │ {assignment.propresenter or '待安排':^10} │
│   视频剪辑    │ {assignment.video_editor:^10} │
└─────────────┴──────────────┘

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
```

这样您就可以根据教会的具体需求，灵活地调整和美化通知模板了！
