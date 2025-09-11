# Grace Irvine Ministry Scheduler v2.0 - 简化版

恩典尔湾长老教会事工排程管理系统 - 简化架构版本

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
创建 `.env` 文件：
```bash
# Google Sheets配置
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here

# 邮件配置（可选）
SENDER_EMAIL=your_email@example.com
EMAIL_PASSWORD=your_app_password
```

### 3. 启动应用
```bash
# 使用默认设置启动
python start.py

# 或指定端口
python start.py --port 8080
```

## 📋 主要功能

### ✅ 已实现的功能
- ✅ **数据获取**: 从Google Sheets读取排班数据
- ✅ **数据清洗**: 自动清理和验证数据
- ✅ **模板生成**: 生成微信群通知模板
  - 周三确认通知
  - 周六提醒通知  
  - 月度总览通知
- ✅ **邮件发送**: 发送通知模板到邮箱
- ✅ **ICS日历**: 生成可订阅的日历文件
- ✅ **Web界面**: 直观的管理界面
- ✅ **云端部署**: 支持Google Cloud Run部署

### 🔧 架构改进
- ✅ **统一入口点**: 只需运行 `python start.py`
- ✅ **简化部署**: 单一应用，易于维护
- ✅ **内置服务**: 集成静态文件服务
- ✅ **清晰结构**: 删除重复代码

## 🌐 Web界面功能

访问 `http://localhost:8501` 使用以下功能：

### 📊 数据概览
- 查看排程数据统计
- 显示近期排程安排
- 数据质量监控

### 📝 模板生成器
- 生成三种通知模板
- 保存模板到文件
- 发送模板到邮箱

### 📅 日历管理
- 生成ICS日历文件
- 查看日历状态
- 获取订阅链接

### ⚙️ 系统设置
- 查看配置信息
- 清除缓存
- 文件状态监控

## 📅 ICS日历订阅

生成的日历文件：
- `grace_irvine_coordinator.ics` - 负责人日历（包含通知提醒）
- `grace_irvine_workers.ics` - 同工日历（包含服事安排）

### 订阅方法：
1. **Google Calendar**: 左侧"+" → "从URL添加" → 粘贴链接
2. **Apple Calendar**: "文件" → "新建日历订阅" → 输入URL  
3. **Outlook**: "添加日历" → "从Internet订阅" → 输入URL

## 🔧 开发和部署

### 本地开发
```bash
# 启动开发环境
python start.py

# 启动时跳过环境检查
python start.py --skip-checks
```

### Docker部署
```bash
# 构建镜像
docker build -t grace-scheduler .

# 运行容器
docker run -p 8080:8080 grace-scheduler
```

### Google Cloud Run部署
```bash
# 部署到Cloud Run
python deploy_cloud_run_with_static.py
```

## 📁 项目结构

```
Grace-Irvine-Ministry-Scheduler/
├── start.py                    # 🚀 统一启动入口
├── app_unified.py             # 📱 统一Web应用
├── src/                       # 📦 核心模块
│   ├── data_cleaner.py       # 🧹 数据清洗
│   ├── scheduler.py          # 📅 排程处理
│   ├── template_manager.py   # 📝 模板管理
│   └── email_sender.py       # 📧 邮件发送
├── configs/                   # ⚙️ 配置文件
├── templates/                 # 📄 模板文件
├── calendars/                 # 📅 ICS文件
├── data/                      # 📊 数据文件
└── requirements.txt           # 📋 依赖包
```

## ❓ 常见问题

### Q: 如何更新日历文件？
A: 在Web界面的"日历管理"页面点击"生成/更新日历文件"按钮

### Q: 邮件发送失败怎么办？
A: 检查 `.env` 文件中的邮件配置，确保使用应用专用密码

### Q: 如何添加新的通知模板？
A: 修改 `templates/notification_templates.yaml` 文件

### Q: 数据加载失败怎么办？
A: 检查Google Sheets是否公开访问，确认Spreadsheet ID正确

## 📞 技术支持

如有问题，请检查：
1. 环境变量配置是否正确
2. 网络连接是否正常
3. Google Sheets是否可访问
4. 依赖包是否完整安装

---

**Grace Irvine Ministry Scheduler v2.0** - 简化版本
Made with ❤️ for Grace Irvine Presbyterian Church
