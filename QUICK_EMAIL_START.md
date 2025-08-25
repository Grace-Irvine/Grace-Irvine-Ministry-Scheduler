# 📧 邮件通知功能 - 快速开始

## 🎯 功能简介

新的邮件通知功能专为事工负责人设计，自动生成包含微信群通知模板的邮件，让负责人可以：

✅ **一键复制** 微信群通知内容  
✅ **直接粘贴** 到微信群发送  
✅ **节省时间** 不需要手动编写通知  
✅ **确保准确** 自动从Google Sheets获取最新数据  

## 🚀 立即使用

### 1. 配置Gmail应用密码

由于已经有 `.env` 文件，您只需要：

1. 访问 [Google应用密码页面](https://myaccount.google.com/apppasswords)
2. 生成新的应用密码（选择"邮件"和"其他"）
3. 复制16位密码（不包含空格）
4. 在项目根目录编辑 `.env` 文件，将密码填入：
   ```
   EMAIL_PASSWORD=your_16_digit_password_here
   ```

### 2. 测试邮件发送

```bash
python3 test_email_notifications.py
```

选择选项3（周三确认通知）或选项4（周六提醒通知）进行测试。

### 3. 发送真实通知

```bash
# 发送周三确认通知
python3 scripts/send_email_notifications.py weekly

# 发送周六提醒通知  
python3 scripts/send_email_notifications.py sunday

# 测试模式（不发送邮件，只显示内容）
python3 scripts/send_email_notifications.py test
```

### 4. 使用便捷脚本

```bash
# Mac/Linux
./scripts/send_email_notifications.sh

# Windows
scripts\send_email_notifications.bat
```

## 📧 邮件内容

收到的邮件包含：

1. **使用说明** - 如何复制和发送到微信群
2. **一键复制按钮** - 点击即可复制微信群通知内容
3. **完整的微信群消息** - 包含所有服事安排信息
4. **发送时间建议** - 最佳发送时间提醒
5. **统计信息** - 本周服事人数和安排概览

## 📱 典型工作流程

### 周三确认流程：
1. **周三晚上8点** 运行周三确认脚本
2. **检查邮件** 确认收到微信群通知模板
3. **复制内容** 点击邮件中的"复制"按钮
4. **发送到微信群** 粘贴到相关微信群
5. **等待确认** 确保所有同工看到并回复

### 周六提醒流程：
1. **周六晚上8点** 运行周六提醒脚本
2. **立即发送** 确保明日服事同工及时收到提醒
3. **确认回复** 关注同工的回复确认
4. **紧急处理** 如有同工临时无法参加，及时安排替补

## ⚙️ 自定义配置

### 添加更多收件人

编辑 `.env` 文件中的 `RECIPIENT_EMAILS`：
```
RECIPIENT_EMAILS=email1@example.com,email2@example.com,email3@example.com
```

### 修改发件人信息

```
SENDER_EMAIL=your_email@graceirvine.org
SENDER_NAME=您的名字
```

## 🔧 故障排除

### 常见问题：

1. **邮件发送失败**
   - 检查 `EMAIL_PASSWORD` 是否正确设置
   - 确认使用的是应用专用密码，不是账户密码
   - 检查网络连接

2. **无法复制内容**
   - 在邮件中手动选择文本复制
   - 确保浏览器支持剪贴板功能

3. **微信群消息格式问题**
   - 可以在微信中手动调整格式
   - 检查原始数据是否正确

## 📞 技术支持

如有问题，请联系：
- 技术支持：jonathanjing@graceirvine.org
- 或在项目中提交Issue

---

**愿神祝福我们的服事！**
