# ProPresenter更新远程工作功能

## 📅 更新日期：2025-10-03

## 🎯 功能概述

将ProPresenter更新角色设置为**远程工作**，工作时间为主日前的**周六晚上4点到9点**。

## ✨ 新增特性

### 1. ProPresenter更新为远程角色

**工作模式**：远程  
**工作时间**：主日前的周六 16:00-21:00  
**提醒时间**：工作开始时（16:00）

### 2. 事件详情

#### 标题格式
```
ProPresenter更新 - [日期]主日
```
例如：`ProPresenter更新 - 11/02主日`

#### 时间安排
- **日期**：主日前1天（周六）
- **开始时间**：16:00（下午4点）
- **结束时间**：21:00（晚上9点）
- **时长**：5小时

#### 地点
```
远程
```

#### 任务清单
- ✅ 更新主日敬拜歌词
- ✅ 检查经文投影
- ✅ 准备报告事项
- ✅ 测试播放流程

## 📊 示例

### 11/02主日的ProPresenter更新

```
事件标题：ProPresenter更新 - 11/02主日
工作日期：2025年11月01日 (周六)
工作时间：16:00-21:00
地点：远程
提醒：16:00 (工作开始时)

描述：
主日日期：2025年11月02日
工作时间：2025年11月01日 (周六) 16:00-21:00

📋 当日服事团队：
  • 音控: 张三
  • 导播/摄影: 李四
  • ProPresenter播放: 王五
  • ProPresenter更新: 靖铮
  • 视频剪辑: 靖铮

💡 ProPresenter更新任务：
• 更新主日敬拜歌词
• 检查经文投影
• 准备报告事项
• 测试播放流程

⏰ 请在周六 16:00-21:00 完成

🙏 感谢你的服事！
```

## 🔧 技术实现

### 代码修改位置

#### `src/personal_ics_manager.py`

**1. 配置部分**

```python
# 角色到场时间配置
self.role_arrival_times = {
    ServiceRole.AUDIO_TECH.value: '09:00',
    ServiceRole.VIDEO_DIRECTOR.value: '09:30',
    ServiceRole.PROPRESENTER_PLAY.value: '08:30',
    ServiceRole.PROPRESENTER_UPDATE.value: None,  # ProPresenter更新为远程
    ServiceRole.VIDEO_EDITOR.value: None  # 视频剪辑无需到场
}

# ProPresenter更新远程工作时间（周六晚上）
self.propresenter_update_time = {
    'day_offset': -1,  # 主日前1天（周六）
    'start_time': '16:00',  # 下午4点
    'end_time': '21:00'  # 晚上9点
}
```

**2. 事件创建逻辑**

```python
# 远程角色特殊处理
if role == ServiceRole.VIDEO_EDITOR.value:
    # 视频剪辑：创建截止提醒事件
    deadline_event = self._create_video_editing_event(...)
    events.append(deadline_event)
elif role == ServiceRole.PROPRESENTER_UPDATE.value:
    # ProPresenter更新：创建周六远程工作事件
    update_event = self._create_propresenter_update_event(...)
    events.append(update_event)
else:
    # 其他角色：创建现场服事事件
    service_event = self._create_worship_service_event(...)
    events.append(service_event)
```

**3. 新增方法**

```python
def _create_propresenter_update_event(self,
                                      service_date: date,
                                      worker_name: str,
                                      assignment: MinistryAssignment) -> Event:
    """创建ProPresenter更新远程工作事件"""
    # 计算周六的工作时间
    # 创建包含详细任务清单的事件
    # 添加工作开始时的提醒
    # 返回完整的事件对象
```

## 📱 用户体验

### 靖铮的日历视图

```
📅 2025年11月

周六 11/01
├─ 16:00-21:00 ProPresenter更新 - 11/02主日 📍远程
│  提醒：16:00 ⏰

周日 11/02
└─ (ProPresenter更新已在前一天完成)

周二 11/04
└─ 18:00-20:00 视频剪辑截止 - 11/02主日 📍远程
   提醒：提前1天 ⏰
```

### 与其他远程角色的对比

| 角色 | 工作时间 | 提醒时间 | 地点 |
|------|----------|----------|------|
| **ProPresenter更新** | 周六 16:00-21:00 | 工作开始时 | 远程 |
| **视频剪辑** | 周二 20:00截止 | 提前1天 | 远程 |

### 与现场角色的对比

| 角色 | 工作时间 | 提醒时间 | 地点 |
|------|----------|----------|------|
| ProPresenter播放 | 主日 08:30-12:00 | 提前30分钟 + 开始时 | 200 Cultivate, Irvine |
| 音控 | 主日 09:00-12:00 | 提前30分钟 + 开始时 | 200 Cultivate, Irvine |
| 摄像导播 | 主日 09:30-12:00 | 提前30分钟 + 开始时 | 200 Cultivate, Irvine |

## 🎯 优势

### 1. 时间灵活性
- ✅ 周六晚上有5小时的工作窗口
- ✅ 不需要早起赶到教会
- ✅ 可以在家中完成

### 2. 工作效率
- ✅ 安静的环境利于专注
- ✅ 充足的时间进行准备和测试
- ✅ 提前一天完成，主日无压力

### 3. 日历清晰
- ✅ 清楚标明远程工作
- ✅ 明确的时间窗口
- ✅ 详细的任务清单

## 📋 示例ICS文件更新

### 靖铮的个人日历新增事件

**总事件数：12个** (原来8个)

新增ProPresenter更新事件：
1. **11/02主日 → 11/01周六 16:00-21:00**
2. **11/23主日 → 11/22周六 16:00-21:00**

完整事件列表：
```
视频剪辑截止（7次）：
├─ 10/05主日 → 10/07 (周二) 20:00
├─ 10/12主日 → 10/14 (周二) 20:00
├─ 10/19主日 → 10/21 (周二) 20:00
├─ 10/26主日 → 10/28 (周二) 20:00
├─ 11/02主日 → 11/04 (周二) 20:00
├─ 11/09主日 → 11/11 (周二) 20:00
└─ 11/23主日 → 11/25 (周二) 20:00

ProPresenter更新（2次）：
├─ 11/02主日 → 11/01 (周六) 16:00-21:00
└─ 11/23主日 → 11/22 (周六) 16:00-21:00

现场服事（3次）：
├─ 11/09 音控服事 09:00-12:00
├─ 11/16 ProPresenter播放 08:30-12:00
└─ 11/16主日 → 11/18 (周二) 20:00 视频剪辑
```

## 🔄 工作流程

### 典型的一周安排

**周六（主日前1天）**
```
16:00 📱 收到提醒：ProPresenter更新时间
16:00-21:00 🏠 远程完成ProPresenter更新
  ├─ 更新歌词
  ├─ 检查经文
  ├─ 准备报告
  └─ 测试流程
```

**周日（主日）**
```
服事日（如果不是ProPresenter播放，则无需到场）
```

**周二（主日后2天）**
```
17:00 📱 收到提醒：视频剪辑明天截止
20:00 ⏰ 视频剪辑截止时间
```

## ⚙️ 配置说明

### 修改工作时间

如需调整ProPresenter更新的工作时间，修改 `src/personal_ics_manager.py`：

```python
self.propresenter_update_time = {
    'day_offset': -1,      # 主日前几天（-1=周六）
    'start_time': '16:00', # 开始时间
    'end_time': '21:00'    # 结束时间
}
```

### 修改提醒时间

当前提醒在工作开始时（16:00）。如需修改：

```python
# 在 _create_propresenter_update_event 方法中
alarm.add('trigger', timedelta(minutes=-30))  # 改为提前30分钟
```

## 🧪 测试验证

### 验证清单

- [ ] ProPresenter更新事件显示在周六
- [ ] 时间为16:00-21:00
- [ ] 地点标记为"远程"
- [ ] 提醒在16:00触发
- [ ] 描述包含完整的任务清单
- [ ] UID格式正确且唯一
- [ ] 可以在日历应用中正常显示

### 测试命令

```bash
# 测试生成功能
python -m src.personal_ics_manager

# 查看示例ICS文件
open "calendars/personal/靖铮_grace_irvine_example.ics"
```

## 📞 常见问题

### Q1: 为什么选择周六晚上？
**A**: 
- 周六有充足时间准备，不会太仓促
- 4-9点是合适的工作时间窗口
- 完成后周日可以专注于其他事务

### Q2: 如果周六有事怎么办？
**A**: 
- 可以在时间窗口内的任何时候完成
- 5小时的窗口提供了灵活性
- 如需调整，可以修改配置

### Q3: ProPresenter播放和更新有什么区别？
**A**: 
- **ProPresenter更新**：周六远程准备内容（歌词、经文等）
- **ProPresenter播放**：周日现场操作播放

### Q4: 提醒时间可以调整吗？
**A**: 
可以。修改 `_create_propresenter_update_event` 方法中的提醒设置。

## 📈 后续优化

### 可能的改进方向

1. **多重提醒**
   - 周六上午提醒（预告）
   - 工作开始时提醒（主提醒）
   - 工作结束前1小时提醒

2. **工作时间弹性**
   - 根据主日特殊性调整时间
   - 节日前可能需要更多时间

3. **任务检查清单**
   - 集成到日历应用的任务列表
   - 完成进度追踪

## 📊 影响范围

### 修改的文件
- ✅ `src/personal_ics_manager.py` - 核心逻辑
- ✅ `calendars/personal/靖铮_grace_irvine_example.ics` - 示例文件
- ✅ `docs/PROPRESENTER_UPDATE_FEATURE.md` - 本文档

### 不受影响的功能
- ✅ 其他角色的事件生成
- ✅ 视频剪辑截止提醒
- ✅ 现场服事事件
- ✅ API接口
- ✅ 前端页面

## ✅ 完成状态

- [x] 代码实现完成
- [x] 示例ICS更新
- [x] 文档编写完成
- [x] 无linter错误
- [ ] 用户测试验证
- [ ] 生产环境部署

---

**版本**：1.0  
**创建日期**：2025-10-03  
**状态**：开发完成 ✅  
**下一步**：测试和部署

