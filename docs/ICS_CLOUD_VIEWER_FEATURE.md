# ICS云端查看器功能

## 功能概述

ICS查看器现已支持查看云端bucket中的ICS文件，可以智能地从本地和云端读取日历文件。

## 主要特性

### 🌐 多数据源支持
- **智能读取（本地优先）**: 自动选择最佳数据源，云端优先
- **仅本地文件**: 只从本地 `calendars/` 目录读取
- **仅云端**: 只从GCP Storage bucket读取

### 📁 Bucket路径配置
在 `configs/config.yaml` 中配置bucket文件夹路径：

```yaml
storage:
  templates_path: "templates/"
  calendars_path: "calendars/"      # ICS文件存储路径
  data_cache_path: "data/cache/"
  backups_path: "backups/"
  logs_path: "logs/"
```

### 🏷️ 文件来源标识
- ☁️ 表示云端文件（强制从云端读取）
- 💻 表示本地文件（强制从本地读取）
- 无标识：智能读取（云端优先，云端失败时回退到本地）

## 使用方法

### 1. 配置设置

#### 快速启动（推荐）
使用提供的云端启动脚本：
```bash
python3 start_with_cloud.py
```

#### 手动配置
确保在环境变量中设置：
```bash
export STORAGE_MODE=cloud
export GOOGLE_CLOUD_PROJECT=ai-for-god
export GCP_STORAGE_BUCKET=grace-irvine-ministry-scheduler
export GOOGLE_APPLICATION_CREDENTIALS=configs/service_account.json
```

### 2. 访问ICS查看器
在主应用中选择 "ICS日历查看器" 页面

### 3. 选择数据源
- 根据需要选择合适的数据源
- 系统会自动显示可用的ICS文件

### 4. 查看文件内容
- 选择要查看的ICS文件
- 系统会显示文件来源（云端/本地）
- 提供事件列表、统计分析和原始数据视图

## 技术实现

### 云存储管理器增强
- 添加了 `list_ics_calendars()` 方法
- 支持从配置文件读取bucket路径
- 智能文件源检测和读取

### ICS查看器更新
- 更新 `get_available_ics_files()` 函数
- 增强 `read_ics_file_smart()` 函数
- 支持文件来源标识和智能读取

## 配置示例

参考 `configs/storage_config_example.yaml` 文件了解完整配置选项。

## 故障排除

### 云端文件无法访问

#### 快速解决方案
使用云端启动脚本：
```bash
python3 start_with_cloud.py
```

#### 手动排查步骤
1. 检查GCP认证配置
   - 确保 `configs/service_account.json` 文件存在
   - 或运行 `gcloud auth application-default login`
2. 确认bucket权限设置
3. 验证bucket名称和项目ID
4. 确保设置了 `STORAGE_MODE=cloud` 环境变量

### 文件列表为空
1. 确认bucket中存在 `.ics` 文件
2. 检查 `calendars_path` 配置
3. 验证本地 `calendars/` 目录
4. 检查文件权限

### 读取失败
1. 检查文件格式是否正确
2. 确认文件编码为UTF-8
3. 查看应用日志获取详细错误信息
4. 验证文件标识前缀是否正确（☁️ 或 💻）

### 变量作用域错误
如果遇到 `cannot access local variable 'force_cloud'` 错误：
- 这个问题已在最新版本中修复
- 确保使用了最新的代码版本

## 更新日志

### v1.1 (2025-09-16)
- 🐛 修复了变量作用域错误
- ✨ 改进了文件来源标识逻辑
- 🔧 增强了错误处理和日志记录
- ✅ 解决了云端文件检测问题
- 🚀 添加了云端启动脚本 `start_with_cloud.py`
- 🐛 修复了文件名清理时的前导空格问题
