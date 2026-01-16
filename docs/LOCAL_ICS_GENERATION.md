# 本地 ICS 生成和使用指南

## 📋 功能概述

本系统支持在本地生成 ICS 日历文件，并可以在前端查看器中查看。

## 🎯 生成 ICS 文件

### 方法 1: 使用生成脚本（推荐）

运行生成脚本：
```bash
python3 scripts/generate_local_ics.py
```

脚本会：
1. 从 `test_data/` 目录读取测试数据（如果 GCS 不可用）
2. 生成两种类型的 ICS 文件：
   - `media-team.ics` - 媒体部服事日历（周三、周六通知）
   - `children-team.ics` - 儿童部服事日历（周三、周六通知）
3. 保存到 `calendars/` 目录

### 方法 2: 在前端生成

1. 启动前端应用：
   ```bash
   streamlit run app_unified.py
   ```

2. 进入 **"📅 ICS日历管理"** 页面

3. 在 **"🆕 多类型 ICS 日历查看器"** 中：
   - 选择数据源：**"💻 本地文件"**
   - 选择要查看的 ICS 类型
   - 如果文件不存在，点击 **"🔄 生成 [类型]"** 按钮

## 📂 数据源配置

### 本地测试数据

系统会从以下位置读取测试数据：

1. **优先**: GCS bucket (`grace-irvine-ministry-data`)
   - `domains/sermon/latest.json`
   - `domains/volunteer/latest.json`

2. **回退**: 本地测试文件 (`test_data/`)
   - `sermon_latest.json`
   - `volunteer_latest.json`
   - `service_layer_latest.json` (旧格式兼容)

### 测试数据格式

#### 证道数据 (`sermon_latest.json`)
```json
{
  "sermons": [
    {
      "date": "2025-11-09",
      "title": "主日证道主题",
      "speaker": "讲员姓名",
      "scripture": "经文引用",
      "scripture_text": "经文内容..."
    }
  ],
  "metadata": {
    "last_updated": "2025-11-04T21:00:00Z",
    "source": "test_data"
  }
}
```

#### 服事人员数据 (`volunteer_latest.json`)
```json
{
  "volunteers": [
    {
      "date": "2025-11-09",
      "media": {
        "sound_control": "音控人员",
        "director": "导播/摄影",
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
  ],
  "metadata": {
    "last_updated": "2025-11-04T21:00:00Z",
    "source": "test_data"
  }
}
```

## 🔍 前端查看器使用

### 1. 启动前端应用

```bash
streamlit run app_unified.py
```

### 2. 进入 ICS 日历管理页面

在侧边栏选择 **"📅 ICS日历管理"** 页面

### 3. 使用多类型 ICS 日历查看器

在页面底部找到 **"🆕 多类型 ICS 日历查看器"**：

1. **选择数据源**:
   - 🌐 智能读取（云端优先）- 自动选择最佳数据源
   - 💻 本地文件 - 仅从本地 `calendars/` 目录读取
   - ☁️ 仅云端 - 仅从 GCS bucket 读取

2. **选择 ICS 类型**:
   - 🎤 媒体部服事日历 (`media-team.ics`)
   - 👶 儿童部服事日历 (`children-team.ics`)

3. **查看内容**:
   - 📅 事件列表 - 显示所有事件，支持搜索和筛选
   - 📊 统计分析 - 事件统计、时间分布等
   - 🔧 原始数据 - 查看原始 ICS 文件内容
   - 📖 事件详情 - 按日期分组显示事件

## 📁 文件结构

生成的文件会保存在以下位置：

```
calendars/
├── media-team.ics          # 媒体部服事日历
├── children-team.ics       # 儿童部服事日历
```

## 💡 使用技巧

### 1. 本地开发

如果在本地开发时没有 GCS 访问权限：
1. 在 `test_data/` 目录创建测试数据文件
2. 运行 `scripts/generate_local_ics.py` 生成 ICS 文件
3. 在前端查看器中选择 **"💻 本地文件"** 模式

### 2. 调试 ICS 内容

在前端查看器的 **"🔧 原始数据"** 标签页中：
- 查看完整的 ICS 文件内容
- 验证 ICS 格式是否正确
- 检查事件描述是否包含经文内容

### 3. 验证事件

在 **"📅 事件列表"** 标签页中：
- 展开事件查看详细描述
- 验证通知时间是否正确（周三、周六、周一）
- 检查服事安排信息是否完整

## 🐛 常见问题

### 问题 1: 生成失败，提示"未找到排程数据"

**解决方案**:
1. 检查 `test_data/` 目录是否存在测试数据文件
2. 验证数据文件格式是否正确
3. 确保日期字段使用 `date` 或 `service_date` 字段名

### 问题 2: 前端无法读取本地文件

**解决方案**:
1. 确保文件已生成到 `calendars/` 目录
2. 在前端查看器中选择 **"💻 本地文件"** 模式
3. 检查文件权限是否正确

### 问题 3: 事件数量为 0

**解决方案**:
1. 检查测试数据中的日期是否为未来日期
2. 验证配置中的日期范围设置
3. 查看日志了解详细错误信息

## 📚 相关文档

- [新 ICS 系统架构设计](NEW_ICS_ARCHITECTURE.md)
- [新 ICS 前端查看器使用指南](NEW_ICS_FRONTEND_VIEWER.md)
- [ICS 测试指南](ICS_TESTING_GUIDE.md)

