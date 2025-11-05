# 新 ICS 系统架构设计

## 📋 概述

本系统将从 Google Sheets 迁移到基于清洗数据的 JSON 数据源，支持生成多种类型的 ICS 日历，并具备灵活的通知时间配置。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Source Layer                        │
├─────────────────────────────────────────────────────────────┤
│  GCS Bucket: grace-irvine-ministry-data                    │
│  ├── service-layer/                                          │
│  │   ├── latest.json              # 最新清洗数据             │
│  │   ├── service_schedule.json    # 服事安排数据             │
│  │   └── sermon_schedule.json     # 证道安排数据             │
│  └── metadata/                                               │
│      └── last_updated.txt                                   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Service Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ICS Generation Service (FastAPI)                          │
│  ├── POST /api/update-ics                                   │
│  ├── GET  /api/status                                       │
│  ├── GET  /calendars/{calendar_type}.ics                   │
│  └── GET  /health                                           │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    ICS Generation Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Calendar Generators                                        │
│  ├── MediaTeamCalendar      # 媒体部服事日历                │
│  ├── ChildrenTeamCalendar    # 儿童部服事日历                │
│  └── WeeklyOverviewCalendar # 每周全部事工概览              │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                            │
├─────────────────────────────────────────────────────────────┤
│  GCS Bucket: grace-irvine-ministry-scheduler                │
│  ├── calendars/                                             │
│  │   ├── media-team.ics              # 媒体部日历          │
│  │   ├── children-team.ics             # 儿童部日历          │
│  │   └── weekly-overview.ics           # 每周概览日历       │
│  └── configs/                                               │
│      └── ics_notification_config.json  # ICS 通知配置       │
└─────────────────────────────────────────────────────────────┘
```

## 📊 数据源结构

### 清洗数据 JSON 格式（来自 Grace-Irvine-Ministry-Clean）

```json
{
  "service_schedule": [
    {
      "date": "2025-01-26",
      "sermon": {
        "title": "证道主题",
        "speaker": "讲员",
        "series": "系列名称",
        "scripture": "经文引用",
        "scripture_text": "经文内容"
      },
      "volunteers": {
        "media": {
          "audio_tech": "音控人员",
          "video_director": "导播/摄影",
          "propresenter_play": "ProPresenter播放",
          "propresenter_update": "ProPresenter更新"
        },
        "children": {
          "teacher": "主日学老师",
          "assistant": "助教",
          "worship": "敬拜带领"
        },
        "worship": {
          "leader": "敬拜主领",
          "team": ["成员1", "成员2"],
          "pianist": "钢琴"
        }
      }
    }
  ]
}
```

## 📅 ICS 日历类型

### 1. 媒体部服事日历 (`media-team.ics`)
- **目标用户**: 媒体部同工
- **事件类型**: 
  - 周三确认通知（提醒本周服事）
  - 周六提醒通知（提醒明日服事）
- **通知时间**: 可配置（默认周三20:00，周六20:00）
- **包含内容**: 
  - 音控、导播/摄影、ProPresenter播放、ProPresenter更新

### 2. 儿童部服事日历 (`children-team.ics`)
- **目标用户**: 儿童部同工
- **事件类型**: 
  - 周三确认通知（提醒本周服事）
  - 周六提醒通知（提醒明日服事）
- **通知时间**: 可配置（默认周三20:00，周六20:00）
- **包含内容**: 
  - 主日学老师、助教、敬拜带领

### 3. 每周全部事工概览日历 (`weekly-overview.ics`)
- **目标用户**: 事工协调人/负责人
- **事件类型**: 
  - 周一全部事工通知（包含整周所有事工）
- **通知时间**: 可配置（默认周一20:00）
- **包含内容**: 
  - 所有证道信息（主题、讲员、经文）
  - 所有服事安排（媒体部、儿童部、敬拜团队等）

## ⚙️ 通知时间配置系统

### 配置文件结构

```json
{
  "calendars": {
    "media-team": {
      "enabled": true,
      "notifications": {
        "wednesday_confirmation": {
          "enabled": true,
          "relative_to_sunday": -4,
          "time": "20:00",
          "duration_minutes": 30,
          "reminder_minutes": 30
        },
        "saturday_reminder": {
          "enabled": true,
          "relative_to_sunday": -1,
          "time": "20:00",
          "duration_minutes": 30,
          "reminder_minutes": 30
        }
      }
    },
    "children-team": {
      "enabled": true,
      "notifications": {
        "wednesday_confirmation": {
          "enabled": true,
          "relative_to_sunday": -4,
          "time": "20:00",
          "duration_minutes": 30,
          "reminder_minutes": 30
        },
        "saturday_reminder": {
          "enabled": true,
          "relative_to_sunday": -1,
          "time": "20:00",
          "duration_minutes": 30,
          "reminder_minutes": 30
        }
      }
    },
    "weekly-overview": {
      "enabled": true,
      "notifications": {
        "monday_overview": {
          "enabled": true,
          "relative_to_sunday": -6,
          "time": "20:00",
          "duration_minutes": 60,
          "reminder_minutes": 60
        }
      }
    }
  }
}
```

### 配置说明

- **relative_to_sunday**: 相对于主日（周日）的天数偏移
  - `-4` = 周三（主日前4天）
  - `-1` = 周六（主日前1天）
  - `-6` = 周一（主日前6天）
- **time**: 通知时间（24小时制）
- **duration_minutes**: 事件持续时间
- **reminder_minutes**: 提醒提前时间（分钟）

## 📁 GCS Bucket 文件架构

### 数据源 Bucket: `grace-irvine-ministry-data`

```
grace-irvine-ministry-data/
├── service-layer/
│   ├── latest.json                    # 最新完整数据
│   ├── service_schedule.json          # 服事安排数据
│   └── sermon_schedule.json           # 证道安排数据
└── metadata/
    └── last_updated.txt               # 最后更新时间戳
```

### 输出 Bucket: `grace-irvine-ministry-scheduler`

```
grace-irvine-ministry-scheduler/
├── calendars/
│   ├── media-team.ics                 # 媒体部日历
│   ├── children-team.ics              # 儿童部日历
│   └── weekly-overview.ics            # 每周概览日历
├── configs/
│   ├── ics_notification_config.json   # ICS 通知配置
│   └── data_source_config.json       # 数据源配置
└── logs/
    └── ics_generation_*.log           # 生成日志
```

## 🔄 数据流程

1. **数据读取**: 从 `grace-irvine-ministry-data/service-layer/latest.json` 读取清洗数据
2. **数据解析**: 解析 JSON 数据，转换为内部数据模型
3. **ICS 生成**: 根据配置生成3种不同的 ICS 日历
4. **文件上传**: 将生成的 ICS 文件上传到 `grace-irvine-ministry-scheduler/calendars/`
5. **状态更新**: 更新生成状态和元数据

## 🚀 API 端点

### 更新 ICS 日历
```
POST /api/update-ics
Headers:
  X-Auth-Token: <token>
Body (可选):
  {
    "calendar_types": ["media-team", "children-team", "weekly-overview"],
    "force_refresh": false
  }
```

### 获取 ICS 日历
```
GET /calendars/{calendar_type}.ics
calendar_type: media-team | children-team | weekly-overview
```

### 获取系统状态
```
GET /api/status
```

### 健康检查
```
GET /health
```

## 📝 实现计划

1. ✅ 架构设计
2. ⏳ 实现 JSON 数据读取器
3. ⏳ 实现数据模型适配器
4. ⏳ 实现3种 ICS 生成器
5. ⏳ 实现配置系统
6. ⏳ 更新 API 端点
7. ⏳ 测试和验证

