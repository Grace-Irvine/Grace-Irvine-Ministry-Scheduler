# Grace Irvine Ministry Scheduler

# 恩典尔湾长老教会事工排班管理系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个简洁高效的教会事工排班管理系统，专为恩典尔湾长老教会设计。

## 🎯 主要功能

- **📊 数据管理**: 从 Google Sheets 自动提取和清洗排班数据
- **📝 通知生成**: 自动生成微信群通知模板（周三确认、周六提醒、月度总览）
- **📧 邮件通知**: 支持自动发送HTML格式的邮件通知给服事同工
- **🔍 数据分析**: 实时数据质量监控和统计分析
- **📅 排程预览**: 查看近期排班安排，智能识别冲突和空缺
- **📥 数据导出**: 支持 Excel 和 CSV 格式导出

## 📁 项目结构

```
Grace-Irvine-Ministry-Scheduler/
├── src/                      # 核心模块
│   ├── data_cleaner.py      # 数据清洗模块
│   ├── scheduler.py         # 排班调度模块
│   ├── notification_generator.py  # 通知生成模块
│   ├── email_sender.py      # 邮件发送模块
│   └── data_validator.py    # 数据验证模块
├── scripts/                  # 执行脚本
│   ├── run_streamlit.py     # Web应用启动脚本
│   ├── run_notifications.sh # 通知生成脚本(Mac/Linux)
│   ├── run_notifications.bat # 通知生成脚本(Windows)
│   ├── send_email_notifications.py # 邮件发送脚本
│   ├── send_email_notifications.sh # 邮件发送脚本(Mac/Linux)
│   └── send_email_notifications.bat # 邮件发送脚本(Windows)
├── tests/                    # 测试文件
│   ├── test_simple.py       # 基础功能测试
│   ├── test_nearby_preview.py # 预览功能测试
│   └── test_weekly_overview.py # 周程概览测试
├── utils/                    # 工具和示例
│   ├── demo_focused_system.py # 系统演示
│   ├── modify_template.py   # 模板修改工具
│   └── template_examples.py # 模板示例
├── configs/                  # 配置文件
│   ├── config.yaml          # 主配置文件
│   └── service_account.json # Google API密钥(需自行添加)
├── data/                     # 数据文件
├── templates/                # 通知模板
├── docs/                     # 文档
│   └── guides/              # 使用指南
└── streamlit_app.py         # Web应用主文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖包
pip install -r requirements.txt
```

### 2. 配置 Google Sheets API

1. 在 [Google Cloud Console](https://console.cloud.google.com/) 创建项目
2. 启用 Google Sheets API
3. 创建服务账号并下载 JSON 密钥文件
4. 将密钥文件重命名为 `service_account.json` 并放在 `configs/` 目录下
5. 将服务账号邮箱添加到您的 Google Sheets 共享列表

### 3. 设置环境变量

创建 `.env` 文件并配置：

```env
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
```

### 4. 启动应用

#### Web界面（推荐）

```bash
# Mac/Linux
python scripts/run_streamlit.py

# 或直接运行
streamlit run streamlit_app.py
```

应用将在浏览器中自动打开：http://localhost:8501

#### 命令行工具

```bash
# 生成通知（Mac/Linux）
./scripts/run_notifications.sh

# 生成通知（Windows）
scripts\run_notifications.bat
```

## 📱 通知模板

系统提供三种通知模板：

### 1. 周三确认通知

提前确认本周主日事工安排

### 2. 周六提醒通知

提醒明天主日的服事时间和注意事项

### 3. 月度总览通知

月初发送当月完整排班表

## 📧 邮件通知功能

邮件通知专为事工负责人设计，包含完整的微信群通知模板，方便直接复制粘贴到微信群。

### 配置邮件发送

1. **设置环境变量**

在项目根目录创建 `.env` 文件：

```bash
# 发件人邮箱
SENDER_EMAIL=jonathanjing@graceirvine.org
SENDER_NAME=Grace Irvine 事工协调

# Gmail应用专用密码
EMAIL_PASSWORD=your_app_password_here

# 收件人列表（可选）
RECIPIENT_EMAILS=email1@example.com,email2@example.com
```

2. **获取Gmail应用专用密码**

- 访问 [Google账户安全设置](https://myaccount.google.com/security)
- 启用两步验证
- 生成应用专用密码：[https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

3. **测试邮件功能**

```bash
# 测试邮件发送
python test_email_notifications.py

# 发送测试通知
python scripts/send_email_notifications.py test
```

### 发送邮件通知

```bash
# Mac/Linux
./scripts/send_email_notifications.sh

# Windows
scripts\send_email_notifications.bat

# 或直接使用Python
python scripts/send_email_notifications.py weekly  # 周三确认
python scripts/send_email_notifications.py sunday  # 周六提醒
```

### 邮件模板

系统提供专门的微信群通知邮件模板：
- `templates/email/weekly_confirmation_wechat.html` - 周三确认通知（含微信群模板）
- `templates/email/sunday_reminder_wechat.html` - 周六提醒通知（含微信群模板）

**主要功能：**
- 📱 一键复制微信群通知内容
- 📋 详细的发送指导说明
- 📊 服事安排统计信息
- ⏰ 最佳发送时间提醒

详细配置说明请参考 [邮件设置指南](docs/guides/EMAIL_SETUP_GUIDE.md)

## 🛠️ 开发指南

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python tests/test_simple.py
```

### 添加新功能

1. 在 `src/` 目录下创建新模块
2. 在 `tests/` 目录下添加相应测试
3. 更新文档说明

## 📋 数据格式要求

Google Sheets 表格应包含以下列：

- 日期
- 音控
- 屏幕/导播
- 摄像
- ProPresenter制作
- 其他事工角色...

## 🔧 故障排除

### 常见问题

1. **无法连接 Google Sheets**

   - 确保服务账号已正确配置
   - 检查表格共享权限
2. **数据质量低**

   - 检查原始表格数据格式
   - 确认日期格式正确
3. **模板生成失败**

   - 确认表格中有对应日期的数据
   - 检查列名是否正确

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

感谢所有为这个项目做出贡献的同工们，愿神祝福我们的服事！

---

**项目目标**: 通过技术手段提升事工管理效率，让同工们能够更专注于属灵的服事。

*最后更新: 2025年*
