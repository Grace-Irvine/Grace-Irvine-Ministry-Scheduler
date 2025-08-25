# Grace Irvine Ministry Scheduler - 数据清洗指南

## 概述

本项目提供了强大的 Google Sheets 数据清洗工具，专门用于处理 Grace Irvine 长老会的主日崇拜事工排程数据。系统能够自动连接到 Google Sheets，提取数据，进行清洗和验证，并生成清洗报告。

## 功能特性

### 🔗 数据连接
- **Google Sheets 集成**: 直接连接到 Google Sheets 获取最新数据
- **无需认证**: 使用简化版本，无需复杂的 API 认证设置
- **SSL 问题自动处理**: 自动处理常见的 SSL 证书问题

### 🧹 数据清洗
- **人名标准化**: 自动清洗和标准化人员姓名
- **日期解析**: 支持多种日期格式的智能解析
- **角色标准化**: 统一事工角色名称
- **重复数据去除**: 自动识别和移除重复记录
- **空值处理**: 智能处理空白和无效数据

### 📊 数据验证
- **完整性检查**: 验证日期和事工安排的完整性
- **质量评分**: 提供数据质量评分（0-100分）
- **问题识别**: 自动识别数据中的潜在问题

### 📈 报告生成
- **清洗统计**: 详细的数据清洗统计信息
- **质量报告**: 数据质量分析报告
- **导出功能**: 支持 CSV 和 Excel 格式导出

## 快速开始

### 1. 环境准备

确保已安装必要的依赖：

```bash
pip3 install pandas openpyxl
```

### 2. 运行数据清洗

#### 基本用法

```bash
# 验证数据质量（不进行实际清洗）
python3 simple_data_cleaner.py --validate-only

# 完整数据清洗流程
python3 simple_data_cleaner.py

# 指定输出文件
python3 simple_data_cleaner.py --output data/my_cleaned_data.xlsx
```

#### 高级用法

```bash
# 使用自定义 Spreadsheet ID
python3 simple_data_cleaner.py --spreadsheet-id YOUR_SPREADSHEET_ID

# 导出为 CSV 格式
python3 simple_data_cleaner.py --output data/cleaned_data.csv
```

### 3. 查看结果

清洗完成后，系统会生成：
- 清洗后的数据文件（Excel 或 CSV）
- 详细的清洗报告（JSON 格式）

## 数据清洗规则

### 人名清洗规则

1. **移除无效模式**:
   - 空字符串
   - 只有短横线 (`-`, `--`)
   - 只有问号 (`?`, `？`)
   - 待定标记 (`待定`, `TBD`, `N/A`)
   - 纯数字

2. **标准化处理**:
   - 合并多个空格为单个空格
   - 移除开头和结尾的数字
   - 移除括号内容 `(内容)` 或 `（内容）`
   - 移除逗号后的内容

3. **长度验证**:
   - 最小长度: 1 个字符
   - 最大长度: 50 个字符

### 日期解析规则

支持以下日期格式：
- `MM/DD/YYYY` (例: 01/05/2025)
- `YYYY/MM/DD` (例: 2025/01/05)
- `YYYY-MM-DD` (例: 2025-01-05)
- `X月Y日` (例: 1月5日)

### 角色标准化

系统会自动标准化以下角色名称：
- 讲员相关: 讲员, 讲道, preacher, speaker
- 敬拜相关: 敬拜带领, 敬拜, worship, worship leader
- 技术相关: 音控, sound, 导播/摄影, ProPresenter播放
- 服事相关: 儿童部, 助教, 主日简餐, 打扫同工
- 管理相关: 财务, 场地协调, 外展协调

## 数据质量评估

### 质量指标

1. **日期完整性**: 有效日期的百分比
2. **事工安排完整性**: 已安排人员的事工岗位百分比
3. **总体质量分数**: 综合质量评分（0-100分）

### 质量阈值

- **优秀** (90-100分): 数据质量很高，可以直接使用
- **良好** (70-89分): 数据质量较好，可能需要少量手动调整
- **一般** (50-69分): 数据质量中等，建议检查和修正
- **较差** (0-49分): 数据质量较低，需要大量清洗工作

## 文件结构

```
Grace-Irvine-Ministry-Scheduler/
├── simple_data_cleaner.py          # 简化版数据清洗工具
├── clean_sheets_data.py            # 完整版数据清洗工具（需要API认证）
├── app/
│   └── services/
│       └── sheets_data_cleaner.py  # 高级数据清洗服务
├── configs/
│   └── data_cleaning_config.yaml   # 数据清洗配置文件
├── data/                           # 输出目录
│   ├── cleaned_*.xlsx              # 清洗后的数据文件
│   └── cleaning_report_*.json      # 清洗报告文件
└── DATA_CLEANING_GUIDE.md          # 本指南文件
```

## 配置说明

### Google Sheets 设置

确保您的 Google Sheets 满足以下条件：
1. **公开访问**: 设置为"知道链接的任何人都可以查看"
2. **正确的 Spreadsheet ID**: 从 URL 中提取正确的 ID
3. **标准格式**: 第一行为列标题，数据从第二行开始

### 列映射配置

系统会自动识别以下列：
- **日期列**: 包含"日期"关键字的列
- **人名列**: 包含事工相关关键字的列（讲员、敬拜、司琴等）

## 故障排除

### 常见问题

1. **SSL 证书错误**
   - 系统会自动处理，使用不安全连接重试
   - 如果仍有问题，请检查网络连接

2. **无法访问 Google Sheets**
   - 确保表格设置为公开访问
   - 检查 Spreadsheet ID 是否正确
   - 验证网络连接

3. **数据质量低**
   - 检查原始数据格式
   - 确保日期格式正确
   - 验证人名数据的完整性

4. **导出失败**
   - 确保已安装 `openpyxl` 库
   - 检查输出目录是否存在
   - 验证文件权限

### 解决方案

```bash
# 安装缺失的依赖
pip3 install pandas openpyxl

# 创建输出目录
mkdir -p data

# 检查 Google Sheets 访问权限
curl -I "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/export?format=csv&gid=0"
```

## 高级功能

### 自定义清洗规则

可以通过修改 `configs/data_cleaning_config.yaml` 文件来自定义清洗规则：

```yaml
cleaning_rules:
  name_cleaning:
    min_length: 1
    max_length: 50
    invalid_patterns:
      - "^$"
      - "^-+$"
      - "^[?？]+$"
```

### API 集成

对于需要更高级功能的用户，可以使用完整版的 API 集成：

```python
from app.services.sheets_data_cleaner import SheetsDataCleaner

cleaner = SheetsDataCleaner(spreadsheet_url)
result = cleaner.clean_and_process_complete_workflow()
```

## 最佳实践

### 数据准备
1. **标准化列标题**: 使用清晰、一致的列标题
2. **日期格式**: 尽量使用 YYYY/MM/DD 格式
3. **人名规范**: 避免在人名中包含额外信息

### 定期维护
1. **定期清洗**: 建议每周运行一次数据清洗
2. **质量监控**: 关注数据质量分数的变化趋势
3. **备份数据**: 在清洗前备份原始数据

### 团队协作
1. **共享配置**: 团队成员使用相同的清洗配置
2. **版本控制**: 对清洗脚本进行版本控制
3. **文档更新**: 及时更新清洗规则和配置

## 支持和反馈

如果您在使用过程中遇到问题或有改进建议，请：

1. 检查本指南的故障排除部分
2. 查看生成的错误日志和报告
3. 联系技术支持团队

---

## 更新日志

### v1.0.0 (2024-08-24)
- 初始版本发布
- 支持基本的数据清洗功能
- 实现 Google Sheets 连接
- 添加数据质量验证
- 提供 Excel/CSV 导出功能
