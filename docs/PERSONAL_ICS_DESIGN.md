# 个人ICS订阅系统设计方案

## 📋 需求概述

为每个服事同工创建独立的可订阅ICS日历文件，包含该同工的所有服事安排。

## 🎯 核心功能

### 1. 个人ICS文件生成
- 基于现有的 `ICSManager.generate_worker_calendar()` 方法
- 根据每个人的名字，自动提取该人所有服事记录
- 生成包含以下内容的ICS文件：
  - 彩排时间（到场时间）
  - 正式服事时间
  - 服事角色说明
  - 提醒通知

### 2. 个人ICS文件存储
- **本地存储**：`calendars/personal/` 目录
- **云端存储**：上传到GCS Bucket的 `calendars/personal/` 路径
- **命名规范**：`{姓名}_grace_irvine.ics`（例如：`靖铮_grace_irvine.ics`）

### 3. 前端管理页面
- 新增"个人日历管理"页面
- 功能包括：
  - 查看所有同工列表
  - 查看每个人的ICS文件内容
  - 预览即将到来的服事安排
  - 下载/订阅个人ICS文件
  - 获取订阅链接

### 4. 统一提醒时间管理
- 使用现有的 `configs/reminder_settings.json`
- 新增个人日历提醒配置：
  ```json
  {
    "personal_calendar_reminders": {
      "rehearsal_reminder": {
        "minutes_before": 60,
        "description": "彩排提醒"
      },
      "service_reminder": {
        "minutes_before": 30,
        "description": "服事提醒"
      }
    }
  }
  ```

### 5. 自动更新机制
- 云端定时器触发时，同时更新所有个人ICS
- 更新流程：
  1. 从Google Sheets获取最新数据
  2. 提取所有同工名单
  3. 为每个同工生成个人ICS
  4. 上传到云端存储
  5. 更新时间戳

## 📁 需要修改的文件

### 1. 核心功能文件

#### `src/personal_ics_manager.py` (新建)
```python
"""个人ICS日历管理器"""
- PersonalICSManager 类
- 批量生成个人ICS
- 管理个人ICS文件
- 获取订阅URL
```

#### `src/ics_manager.py` (修改)
```python
# 增强 generate_worker_calendar() 方法
- 支持自定义提醒时间
- 更详细的服事信息
- 标准化文件命名
```

#### `src/cloud_storage_manager.py` (修改)
```python
# 添加个人ICS上传功能
- upload_personal_ics()
- list_personal_ics_files()
- get_personal_ics_url()
```

### 2. 前端页面

#### `app_unified.py` (修改)
```python
# 添加新的页面和API endpoints
- show_personal_calendar_management() - 新页面
- /api/personal-ics/list - 列出所有个人ICS
- /api/personal-ics/{name} - 获取特定人的ICS
- /api/personal-ics/generate - 生成所有个人ICS
```

### 3. 配置文件

#### `configs/reminder_settings.json` (修改)
```json
{
  "personal_calendar": {
    "rehearsal_reminder_minutes": 60,
    "service_reminder_minutes": 30,
    "enabled": true
  }
}
```

#### `configs/personal_ics_config.yaml` (新建)
```yaml
personal_calendars:
  output_directory: "calendars/personal/"
  cloud_storage_path: "calendars/personal/"
  url_base: "https://storage.googleapis.com/{bucket}"
  auto_update_enabled: true
  
service_times:
  rehearsal_start: "09:00"
  service_start: "10:00"
  service_end: "12:00"
  
role_arrival_times:
  audio_tech: "09:00"
  video_director: "09:30"
  propresenter_play: "09:00"
  propresenter_update: "08:30"
```

### 4. 自动更新逻辑

#### `app_unified.py` 中的 `automatic_ics_update()` (修改)
```python
async def automatic_ics_update():
    # ... 现有代码 ...
    
    # 4. 生成个人ICS文件（新增）
    logger.info("Step 4: Generating personal ICS files")
    from src.personal_ics_manager import PersonalICSManager
    personal_manager = PersonalICSManager()
    
    # 生成所有个人ICS
    personal_files = personal_manager.generate_all_personal_ics(schedules)
    
    # 上传到云端
    for worker_name, file_path in personal_files.items():
        storage_manager.upload_file(
            file_path,
            f"calendars/personal/{worker_name}_grace_irvine.ics"
        )
```

## 🔄 工作流程

### 个人ICS生成流程

```
1. 从Google Sheets获取数据
   ↓
2. 解析所有事工安排
   ↓
3. 提取所有同工名单
   (去重，排除"待安排")
   ↓
4. 为每个同工：
   - 筛选该同工的服事记录
   - 生成ICS事件
   - 添加提醒
   - 保存ICS文件
   ↓
5. 上传所有ICS到云端
   ↓
6. 生成订阅URL
```

### 前端展示流程

```
用户访问"个人日历管理"页面
   ↓
显示所有同工列表
   ↓
用户选择某个同工
   ↓
显示该同工的：
- 即将到来的服事（未来3个月）
- ICS文件信息（大小、事件数）
- 订阅链接（复制）
- 下载按钮
- 预览按钮
```

## 📊 数据结构

### 个人服事事件结构
```python
{
  "worker_name": "靖铮",
  "events": [
    {
      "date": "2025-10-05",
      "role": "视频剪辑",
      "rehearsal_time": null,  # 视频剪辑无需彩排
      "service_time": null,
      "deadline": "2025-10-08 20:00",  # 剪辑截止时间
      "reminder_minutes": 1440  # 提前1天提醒
    },
    {
      "date": "2025-10-12",
      "role": "音控",
      "rehearsal_time": "2025-10-12 09:00",
      "service_time": "2025-10-12 10:00",
      "reminder_minutes": 60
    }
  ]
}
```

## 🎨 前端UI设计

### 页面布局
```
┌─────────────────────────────────────────┐
│  📅 个人日历管理                          │
├─────────────────────────────────────────┤
│  🔄 全部更新    📊 统计信息              │
├─────────────────────────────────────────┤
│  同工列表                                │
│  ┌───────────────────────────────────┐  │
│  │ 👤 靖铮                            │  │
│  │    角色：视频剪辑                  │  │
│  │    服事次数：12次                  │  │
│  │    [查看详情] [下载] [订阅链接]    │  │
│  ├───────────────────────────────────┤  │
│  │ 👤 [其他同工]                      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 详情页面
```
┌─────────────────────────────────────────┐
│  👤 靖铮 - 个人服事日历                   │
├─────────────────────────────────────────┤
│  📊 统计信息                             │
│  • 未来服事：8次                         │
│  • 主要角色：视频剪辑                     │
│  • 日历订阅：✅ 已启用                    │
├─────────────────────────────────────────┤
│  📅 即将到来的服事                        │
│  ┌───────────────────────────────────┐  │
│  │ 10/05 (周日) - 视频剪辑            │  │
│  │   截止：10/08 20:00               │  │
│  ├───────────────────────────────────┤  │
│  │ 10/12 (周日) - 音控               │  │
│  │   彩排：09:00                     │  │
│  │   服事：10:00                     │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│  🔗 订阅链接                             │
│  [复制链接] [下载ICS] [预览日历]         │
└─────────────────────────────────────────┘
```

## 🔧 实施步骤

### 阶段一：核心功能（第1-2天）
1. ✅ 创建 `PersonalICSManager` 类
2. ✅ 增强个人ICS生成逻辑
3. ✅ 实现批量生成功能
4. ✅ 添加云端上传功能

### 阶段二：自动更新（第3天）
1. ✅ 修改 `automatic_ics_update()` 函数
2. ✅ 添加个人ICS更新逻辑
3. ✅ 测试定时器触发

### 阶段三：前端页面（第4-5天）
1. ✅ 创建个人日历管理页面
2. ✅ 实现API endpoints
3. ✅ 添加UI交互功能

### 阶段四：测试和优化（第6天）
1. ✅ 端到端测试
2. ✅ 性能优化
3. ✅ 文档完善

## 📝 特殊处理

### 视频剪辑角色（靖铮专属）
- 不显示彩排时间
- 显示剪辑截止时间（周一晚8点）
- 提醒时间：提前1天

### 其他角色
- 显示到场时间
- 显示彩排和服事时间
- 根据角色设置不同到场时间

## 🔐 安全考虑

1. **访问控制**：个人ICS URL需要验证
2. **数据隐私**：仅显示相关同工的信息
3. **更新权限**：仅管理员可触发更新

## 📈 后续优化

1. 邮件通知：ICS更新时发送邮件
2. 移动端优化：适配手机浏览器
3. 批量订阅：一键订阅所有相关日历
4. 历史记录：保留过往服事记录

---

**创建日期**：2025-10-03  
**负责人**：Jonathan  
**状态**：设计阶段

