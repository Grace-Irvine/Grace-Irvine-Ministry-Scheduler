# Scripts 目录说明

本目录包含各种管理和维护脚本。

## 📅 ICS日历相关

### 主要使用脚本

#### `upload_to_gcs.py` ⭐ **推荐使用**
**用途**：生成ICS日历并直接上传到Google Cloud Storage

**特点**：
- ✅ 应用了所有最新修复（保留历史4周 + 稳定经文选择）
- ✅ 直接上传到GCS，公开可访问
- ✅ 不依赖本地存储配置

**使用方法**：
```bash
python3 scripts/upload_to_gcs.py
```

**适用场景**：
- 手动更新云端ICS文件
- 按需生成和发布日历

---

#### `update_static_calendars.py`
**用途**：生成静态ICS文件（本地或服务器文件系统）

**特点**：
- ✅ 应用了日期范围修复（保留历史4周）
- 生成两个日历：负责人日历 + 同工日历
- 保存到本地 `calendars/` 目录

**使用方法**：
```bash
python3 scripts/update_static_calendars.py
python3 scripts/update_static_calendars.py --watch  # 持续监控模式
```

**适用场景**：
- 本地开发测试
- 部署到自己的Web服务器

---

### Cloud Run相关

#### `ics_background_service.py`
**用途**：Cloud Run后台服务，提供API端点

**特点**：
- ✅ 应用了日期范围修复
- 提供HTTP API接口
- 可配合Cloud Scheduler自动更新

**部署后可用端点**：
- `POST /api/update-calendars` - 触发更新
- `GET /api/status` - 获取状态
- `GET /calendars/<filename>` - 下载ICS文件
- `GET /health` - 健康检查

---

## 🧪 测试脚本

#### `test_ics_fixes.py`
**用途**：验证ICS生成修复效果

**测试内容**：
1. 经文选择稳定性
2. 经文索引稳定性
3. 模板渲染经文使用
4. 日期范围检查

**使用方法**：
```bash
python3 scripts/test_ics_fixes.py
```

---

## 📧 通知发送

#### `send_email_notifications.py`
**用途**：发送事工通知邮件

**使用方法**：
```bash
python3 scripts/send_email_notifications.py
```

---

## 🛠️ 工具脚本

#### `check_template_consistency.py`
检查模板一致性

#### `check_template_rendering.py`
检查模板渲染效果

#### `template_preview.py`
预览模板输出

#### `get_template_content.py`
获取模板内容

#### `get_cloud_run_url.py`
获取Cloud Run服务URL

---

## 📝 配置和管理

#### `init_cloud_config.py`
初始化云端配置

#### `manage_ics_calendar.py`
管理ICS日历

#### `manage_unified_system.py`
统一系统管理

---

## 🔄 快速参考

### 更新云端ICS文件
```bash
python3 scripts/upload_to_gcs.py
```

### 测试修复效果
```bash
python3 scripts/test_ics_fixes.py
```

### 本地生成ICS文件
```bash
python3 scripts/update_static_calendars.py
```

### 发送通知
```bash
python3 scripts/send_email_notifications.py
```

---

## 📚 相关文档

- `/docs/ICS_GENERATION_FIX.md` - ICS生成修复技术文档
- `/ICS修复说明.md` - 中文用户指南
- `/docs/` - 其他详细文档

---

## 🗑️ 已清理的文件

以下文件已被删除（功能重复或已过时）：

### ICS生成脚本（已整合）
- ~~`upload_ics_to_cloud.py`~~ → 被 `upload_to_gcs.py` 替代
- ~~`demo_coordinator_ics.py`~~ → 演示脚本，功能已整合
- ~~`simple_coordinator_ics.py`~~ → 简化版本，功能已整合
- ~~`generate_coordinator_ics.py`~~ → 旧版生成器，功能已整合到 `src/calendar_generator.py`

### 服务脚本（已整合）
- ~~`simple_ics_service.py`~~ → 被 `ics_background_service.py` 替代

### 测试脚本（已整合）
- ~~`simple_ics_test.py`~~ → 旧测试脚本
- ~~`test_ics_fix.py`~~ → 被 `test_ics_fixes.py` 替代

**总计删除**：7个重复/过时脚本

**保留的核心脚本**：
- ✅ `upload_to_gcs.py` - 主要使用的GCS上传脚本（包含所有修复）
- ✅ `update_static_calendars.py` - 本地/静态文件生成（包含修复）
- ✅ `ics_background_service.py` - Cloud Run服务（包含修复）
- ✅ `test_ics_fixes.py` - 最新的测试脚本

