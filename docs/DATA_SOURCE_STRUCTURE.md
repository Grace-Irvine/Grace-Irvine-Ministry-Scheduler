# 数据源 Bucket 文件架构

## 📁 文件结构

```
grace-irvine-ministry-data/
├── domains/
│   ├── sermon/
│   │   ├── latest.json              # 最新证道数据（推荐使用）
│   │   ├── 2024/
│   │   │   └── sermon_2024.json      # 2024年证道数据
│   │   ├── 2025/
│   │   │   └── sermon_2025.json      # 2025年证道数据
│   │   └── 2026/
│   │       └── sermon_2026.json      # 2026年证道数据
│   └── volunteer/
│       ├── latest.json               # 最新服事人员数据（推荐使用）
│       ├── 2024/
│       │   └── volunteer_2024.json   # 2024年服事数据
│       ├── 2025/
│       │   └── volunteer_2025.json   # 2025年服事数据
│       └── 2026/
│           └── volunteer_2026.json   # 2026年服事数据
```

## 📊 数据结构

### 证道数据 (`domains/sermon/latest.json`)

```json
{
  "metadata": {
    "domain": "sermon",
    "version": "1.0",
    "generated_at": "2025-11-03T19:00:17.992771+00:00",
    "record_count": 131,
    "date_range": {
      "start": "2026-01-04",
      "end": "2026-07-05"
    },
    "last_updated": "2025-11-03T19:00:20.783735+00:00",
    "source": "merged_from_yearly",
    "yearly_files": ["domains/sermon/2024/sermon_2024.json", ...]
  },
  "sermons": [
    {
      "service_date": "2024-01-07",
      "service_week": 1,
      "service_slot": "morning",
      "sermon": "证道主题",
      "preacher": {
        "id": "person_xxx",
        "name": "讲员姓名"
      },
      "series": "系列名称",
      "scripture": "经文引用",
      "scripture_text": "经文内容",
      "songs": ["歌曲1", "歌曲2"],
      "source_row": 2,
      "updated_at": "2025-11-03T19:00:17.252458Z"
    }
  ]
}
```

### 服事人员数据 (`domains/volunteer/latest.json`)

```json
{
  "metadata": {
    "domain": "volunteer",
    "version": "1.0",
    "generated_at": "2025-11-03T19:00:17.997142+00:00",
    "record_count": 131,
    "date_range": {
      "start": "2026-01-04",
      "end": "2026-07-05"
    },
    "last_updated": "2025-11-03T19:00:21.085806+00:00",
    "source": "merged_from_yearly",
    "yearly_files": ["domains/volunteer/2024/volunteer_2024.json", ...]
  },
  "volunteers": [
    {
      "service_date": "2024-01-07",
      "service_week": 1,
      "service_slot": "morning",
      "worship": {
        "department": "敬拜部",
        "lead": {
          "id": "person_xxx",
          "name": "主领姓名"
        },
        "team": [
          {
            "id": "person_xxx",
            "name": "成员姓名"
          }
        ],
        "pianist": {
          "id": "person_xxx",
          "name": "钢琴姓名"
        }
      },
      "technical": {
        "department": "媒体部",
        "audio": {
          "id": "person_xxx",
          "name": "音控姓名"
        },
        "video": {
          "id": "person_xxx",
          "name": "导播/摄影姓名"
        },
        "propresenter_play": {
          "id": "person_xxx",
          "name": "ProPresenter播放姓名"
        },
        "propresenter_update": {
          "id": "person_xxx",
          "name": "ProPresenter更新姓名"
        }
      },
      "education": {
        "department": "儿童部",
        "sunday_child_teacher": {
          "id": "person_xxx",
          "name": "主日学老师姓名"
        },
        "sunday_child_assistants": [
          {
            "id": "person_xxx",
            "name": "助教姓名"
          }
        ],
        "sunday_child_worship": {
          "id": "person_xxx",
          "name": "敬拜带领姓名"
        }
      },
      "source_row": 2,
      "updated_at": "2025-11-03T19:00:17.252458Z"
    }
  ]
}
```

## 🔄 数据读取方式

### 推荐方式：使用 `get_service_schedule()`

系统会自动：
1. 从 `domains/sermon/latest.json` 读取证道数据
2. 从 `domains/volunteer/latest.json` 读取服事人员数据
3. 按日期合并数据，生成统一的 `service_schedule` 格式

### 直接读取方式

```python
from src.json_data_reader import get_json_data_reader

reader = get_json_data_reader()

# 读取证道数据
sermon_data = reader.read_json_file('domains/sermon/latest.json')

# 读取服事人员数据
volunteer_data = reader.read_json_file('domains/volunteer/latest.json')
```

## 📝 注意事项

1. **推荐使用 `latest.json`**：这些文件包含所有年份的合并数据
2. **数据格式**：每个数据项都包含 `metadata` 和实际数据数组
3. **日期格式**：使用 `YYYY-MM-DD` 格式
4. **人员信息**：使用对象格式 `{id, name}`，或直接为字符串
5. **向后兼容**：系统仍支持读取旧的 `service-layer/` 路径

