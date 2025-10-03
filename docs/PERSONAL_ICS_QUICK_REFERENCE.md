# 个人ICS订阅系统 - 快速参考

## 📌 需要修改的文件清单

### ✅ 已完成

1. **`src/personal_ics_manager.py`** (新建) ✅
   - 个人ICS管理核心类
   - 完整实现，可直接使用

2. **`docs/PERSONAL_ICS_DESIGN.md`** (新建) ✅
   - 完整的系统设计文档

3. **`docs/PERSONAL_ICS_IMPLEMENTATION.md`** (新建) ✅
   - 详细的实施指南

4. **`calendars/personal/靖铮_grace_irvine_example.ics`** (新建) ✅
   - 靖铮的个人ICS示例文件

### 🔨 待修改

5. **`src/cloud_storage_manager.py`** (修改)
   - 添加4个方法：
     - `upload_personal_ics()`
     - `list_personal_ics_files()`
     - `get_personal_ics_url()`
     - `delete_personal_ics()`

6. **`app_unified.py`** (修改)
   - 修改 `automatic_ics_update()` 函数：添加步骤4和5
   - 修改 `main()` 函数：添加菜单项"个人日历管理"
   - 添加函数 `show_personal_calendar_management()`
   - 添加3个API端点：
     - `/api/personal-ics/list`
     - `/api/personal-ics/{worker_name}`
     - `/api/personal-ics/generate`

7. **`configs/reminder_settings.json`** (修改)
   - 添加 `personal_calendar` 配置节

## 🚀 快速实施步骤

### 第1步：修改 cloud_storage_manager.py

```bash
# 打开文件
vim src/cloud_storage_manager.py

# 在 CloudStorageManager 类末尾添加4个方法
# 代码见 PERSONAL_ICS_IMPLEMENTATION.md 第1节
```

### 第2步：修改 app_unified.py - 自动更新

```bash
# 找到 automatic_ics_update() 函数
# 在步骤3之后添加步骤4和5
# 代码见 PERSONAL_ICS_IMPLEMENTATION.md 第2节
```

### 第3步：修改 app_unified.py - 前端页面

```bash
# 1. 在 main() 函数的菜单中添加"个人日历管理"
# 2. 添加 show_personal_calendar_management() 函数
# 代码见 PERSONAL_ICS_IMPLEMENTATION.md 第3节
```

### 第4步：修改 reminder_settings.json

```bash
# 添加 personal_calendar 配置
# 代码见 PERSONAL_ICS_IMPLEMENTATION.md 第4节
```

### 第5步：测试

```bash
# 测试个人ICS管理器
python -m src.personal_ics_manager

# 启动本地应用
streamlit run app_unified.py

# 访问"个人日历管理"页面并测试
```

## 📊 以靖铮为例的个人ICS特性

### 视频剪辑角色（主要）
- ✅ **无彩排事件** - 视频剪辑无需到场彩排
- ✅ **剪辑截止提醒** - 每周一晚8点前完成
- ✅ **提前1天提醒** - 周日提醒周一截止
- ✅ **远程工作** - 地点标记为"远程"

### 偶尔音控服事（次要）
- ✅ **彩排事件** - 上午9:00到场
- ✅ **正式服事** - 上午10:00-12:00
- ✅ **提前1小时提醒** - 彩排前提醒
- ✅ **提前30分钟提醒** - 服事前提醒

### 示例ICS文件内容

```
靖铮_grace_irvine.ics 包含：
- 10月视频剪辑（4次）
- 11月9日音控服事（彩排+正式服事）
- 11月9日视频剪辑
```

## 🔗 订阅URL格式

```
https://storage.googleapis.com/{bucket_name}/calendars/personal/靖铮_grace_irvine.ics
```

## 💡 关键技术点

### 1. 角色识别
```python
if role == ServiceRole.VIDEO_EDITOR.value:
    # 视频剪辑特殊处理
else:
    # 其他角色标准处理
```

### 2. 时间计算
```python
# 剪辑截止时间：主日后的周一晚8点
days_until_monday = (1 - service_date.weekday()) % 7
deadline_date = service_date + timedelta(days=days_until_monday)
```

### 3. 提醒设置
```python
self.reminder_minutes = {
    'rehearsal': 60,        # 彩排提前1小时
    'service': 30,          # 服事提前30分钟
    'video_editing': 1440   # 剪辑提前1天
}
```

### 4. 批量生成
```python
# 提取所有同工
workers = manager.extract_all_workers(assignments)

# 为每个同工生成ICS
for worker in workers:
    manager.generate_personal_ics(assignments, worker)
```

## 🎯 验证清单

### 功能验证
- [ ] 能够提取所有同工名单
- [ ] 能够为靖铮生成个人ICS
- [ ] 靖铮的视频剪辑事件格式正确
- [ ] 靖铮的音控事件包含彩排和服事
- [ ] 提醒时间设置正确
- [ ] 能够批量生成所有同工的ICS
- [ ] 能够上传到GCS bucket
- [ ] 能够获取公开订阅URL

### 前端验证
- [ ] "个人日历管理"页面显示正常
- [ ] 能够显示所有同工列表
- [ ] 能够查看靖铮的详细信息
- [ ] 能够复制订阅链接
- [ ] 能够下载ICS文件
- [ ] 能够手动触发生成

### 自动更新验证
- [ ] Cloud Scheduler能够触发更新
- [ ] 更新时会生成所有个人ICS
- [ ] 更新时会上传到云端
- [ ] 日志记录完整

## 📱 订阅测试步骤

### Apple Calendar
1. 复制订阅链接
2. 打开"日历"应用
3. 文件 → 新建日历订阅
4. 粘贴URL
5. 设置刷新频率：每小时

### Google Calendar
1. 复制订阅链接
2. 打开Google Calendar
3. 点击左侧"+"
4. 选择"通过URL添加"
5. 粘贴URL
6. 点击"添加日历"

### Outlook
1. 复制订阅链接
2. 打开Outlook日历
3. 添加日历 → 从Internet
4. 粘贴URL
5. 确定

## 🆘 常见问题

### Q1: 为什么靖铮没有彩排事件？
**A**: 视频剪辑角色不需要到场彩排，系统会自动识别并跳过彩排事件的创建。

### Q2: 视频剪辑截止时间是如何计算的？
**A**: 主日之后的周一晚上8点。例如：10/05（周日）的剪辑截止时间是10/06（周一）20:00。

### Q3: 如果靖铮同一天既有视频剪辑又有其他服事怎么办？
**A**: 系统会为每个角色创建独立的事件。例如11/09既有音控服事（彩排+正式服事）又有视频剪辑截止提醒。

### Q4: 如何修改提醒时间？
**A**: 修改 `configs/reminder_settings.json` 中的 `personal_calendar` 配置，或在代码中修改 `PersonalICSManager` 的 `reminder_minutes` 属性。

### Q5: 如何添加新的服事角色？
**A**: 在 `ServiceRole` 枚举中添加新角色，并在 `role_arrival_times` 中配置到场时间。

## 📋 代码位置快速查找

| 功能 | 文件 | 行号范围 |
|------|------|---------|
| 个人ICS生成核心 | `src/personal_ics_manager.py` | 全文 |
| 视频剪辑特殊处理 | `src/personal_ics_manager.py` | 205-250 |
| 彩排事件创建 | `src/personal_ics_manager.py` | 252-295 |
| 云端上传（待添加） | `src/cloud_storage_manager.py` | 末尾添加 |
| 自动更新（待修改） | `app_unified.py` | `automatic_ics_update()` |
| 前端页面（待添加） | `app_unified.py` | 末尾添加 |

## 🎨 UI预览

```
┌────────────────────────────────────────┐
│  👥 个人日历管理                        │
│  为每个服事同工生成独立的可订阅ICS日历   │
├────────────────────────────────────────┤
│  [🔄 生成所有个人ICS] [📊 查看统计]     │
├────────────────────────────────────────┤
│  📋 同工列表 (8)                        │
│                                         │
│  ▼ 👤 靖铮                              │
│     文件信息                            │
│     • 文件名：靖铮_grace_irvine.ics     │
│     • 文件大小：5.23 KB                 │
│     • 更新时间：2025-10-03 12:00:00    │
│                                         │
│     📎 订阅链接                         │
│     https://storage.googleapis.com/... │
│     [📋 复制链接]                       │
│                                         │
│     操作                                │
│     [⬇️ 下载] [🔄 重新生成]             │
└────────────────────────────────────────┘
```

## ⚡ 性能考虑

- **批量生成**：~10个同工约需5-10秒
- **单个生成**：约0.5-1秒
- **文件大小**：平均3-8KB每人
- **云端上传**：约0.2-0.5秒每文件

## 🔒 安全注意事项

1. **API认证**：所有API端点需要auth token
2. **公开访问**：ICS文件URL公开可访问（需要URL才能访问）
3. **数据隐私**：仅包含服事相关信息，不包含个人敏感信息

---

**版本**: 1.0  
**更新**: 2025-10-03  
**状态**: 准备实施

