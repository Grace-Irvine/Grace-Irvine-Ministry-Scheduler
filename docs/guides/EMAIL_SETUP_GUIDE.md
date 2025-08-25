# 📧 邮件通知功能设置指南

## 概述

Grace Irvine 事工管理系统现已支持邮件通知功能，可以自动发送事工安排确认和提醒邮件给相关同工。

## 功能特点

- ✅ 支持HTML格式的精美邮件模板
- ✅ 自动生成周三确认通知和周六提醒通知
- ✅ 支持批量发送给多个收件人
- ✅ 集成Google Sheets数据，实时获取最新安排
- ✅ 支持Gmail和其他SMTP邮件服务器

## 快速开始

### 1. 环境配置

创建 `.env` 文件并添加以下配置：

```bash
# 发件人邮箱（默认）
SENDER_EMAIL=jonathanjing@graceirvine.org

# 发件人名称
SENDER_NAME=Grace Irvine 事工协调

# 邮箱密码或应用专用密码（必需）
EMAIL_PASSWORD=your_app_password_here

# SMTP服务器配置（可选，默认为Gmail）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 2. Gmail应用专用密码设置

由于Gmail的安全策略，需要使用应用专用密码而不是账户密码：

1. 访问 [Google账户安全设置](https://myaccount.google.com/security)
2. 启用两步验证（如果尚未启用）
3. 访问 [应用专用密码页面](https://myaccount.google.com/apppasswords)
4. 选择"邮件"和"其他（自定义名称）"
5. 输入"Grace Irvine Ministry Scheduler"
6. 点击"生成"获取16位密码
7. 将此密码复制到 `.env` 文件的 `EMAIL_PASSWORD` 字段

### 3. 测试邮件功能

运行测试脚本验证配置：

```bash
python test_email_notifications.py
```

测试选项：
1. 测试SMTP连接
2. 发送简单测试邮件
3. 发送周三确认通知
4. 发送周六提醒通知
5. 使用真实数据测试
6. 运行所有测试

## 邮件模板

系统提供两个主要邮件模板：

### 1. 周三确认通知 (`weekly_confirmation.html`)

- **发送时间**: 每周三晚上
- **内容**: 本周所有服事安排的确认
- **包含信息**:
  - 服事日期和时间
  - 各岗位人员安排
  - 重要提醒事项
  - 确认和调换按钮

### 2. 周六提醒通知 (`sunday_reminder.html`)

- **发送时间**: 每周六晚上
- **内容**: 明日主日服事的最终提醒
- **包含信息**:
  - 明日服事详情
  - 建议到达时间
  - 准备清单
  - 紧急联系方式

## 集成到主系统

### 方法1: 手动发送

```python
from src.email_sender import EmailSender, EmailRecipient
from src.scheduler import GoogleSheetsExtractor, MinistryAssignment

# 初始化
sender = EmailSender()
extractor = GoogleSheetsExtractor(spreadsheet_id)

# 获取本周安排
assignment = extractor.get_current_week_assignment()

# 创建收件人列表
recipients = [
    EmailRecipient(email="person1@example.com", name="张三", role="音控"),
    EmailRecipient(email="person2@example.com", name="李四", role="屏幕")
]

# 发送周三确认通知
schedule_data = {
    'date': assignment.date,
    'time': '10:00',
    'location': 'Grace Irvine 教会',
    'roles': {
        '音控': assignment.audio_tech,
        '屏幕': assignment.screen_operator,
        # ... 其他角色
    }
}

sender.send_weekly_confirmation(recipients, [schedule_data])
```

### 方法2: 定时任务

创建定时任务脚本 `scripts/send_notifications.py`:

```python
#!/usr/bin/env python3
"""定时发送邮件通知"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.email_sender import EmailSender, EmailRecipient
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator

def send_weekly_notifications():
    """每周三晚上8点发送确认通知"""
    # 实现逻辑
    pass

def send_sunday_reminders():
    """每周六晚上8点发送提醒通知"""
    # 实现逻辑
    pass

if __name__ == "__main__":
    day = datetime.now().weekday()
    if day == 2:  # 周三
        send_weekly_notifications()
    elif day == 5:  # 周六
        send_sunday_reminders()
```

然后使用cron (Linux/Mac) 或任务计划程序 (Windows) 设置定时运行。

## 收件人管理

### 从配置文件读取

在 `configs/recipients.yaml` 中管理收件人列表：

```yaml
recipients:
  - email: person1@example.com
    name: 张三
    roles: [音控, 屏幕]
  - email: person2@example.com
    name: 李四
    roles: [摄像, 导播]
```

### 从Google Sheets读取

可以在Google Sheets中添加一个"联系人"工作表，包含：
- 姓名
- 邮箱
- 服事岗位
- 是否接收通知

## 故障排除

### 常见问题

1. **连接失败**
   - 检查 EMAIL_PASSWORD 是否正确
   - 确认使用的是应用专用密码而非账户密码
   - 检查网络连接

2. **邮件未收到**
   - 检查垃圾邮件文件夹
   - 确认收件人邮箱地址正确
   - 查看发送日志中的错误信息

3. **模板显示异常**
   - 确保模板文件存在于 `templates/email/` 目录
   - 检查模板语法是否正确
   - 验证传入的数据格式

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 安全建议

1. **永远不要**将密码硬编码在代码中
2. **使用**环境变量或密钥管理服务存储敏感信息
3. **定期**更换应用专用密码
4. **限制**发送频率，避免被标记为垃圾邮件
5. **验证**收件人邮箱地址的有效性

## 扩展功能

### 计划中的功能

- [ ] 支持短信通知（通过Twilio）
- [ ] 邮件发送历史记录
- [ ] 收件人偏好设置（选择接收哪些通知）
- [ ] 自动重试失败的发送
- [ ] 邮件打开和点击跟踪
- [ ] 多语言支持（中英文切换）

### 自定义模板

要创建新的邮件模板：

1. 在 `templates/email/` 创建新的HTML文件
2. 使用Jinja2模板语法
3. 在 `EmailSender` 类中添加对应的发送方法

示例模板结构：
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ subject }}</title>
</head>
<body>
    <h1>{{ church_name }}</h1>
    <p>{{ content }}</p>
    <footer>
        生成时间: {{ generated_at.strftime('%Y年%m月%d日 %H:%M') }}
    </footer>
</body>
</html>
```

## 联系支持

如有问题或需要帮助，请联系：
- 技术支持：jonathanjing@graceirvine.org
- 项目仓库：[GitHub Repository](https://github.com/your-repo)

---

*最后更新：2024年*
