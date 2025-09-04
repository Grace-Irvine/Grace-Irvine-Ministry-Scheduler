# Streamlit + 静态文件服务集成指南

## 🎯 概述

本指南说明如何将静态文件服务集成到Streamlit应用中，提供ICS日历文件的订阅服务，无需额外的Cloud Storage bucket。

## 🏗️ 架构设计

### 集成架构
```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit + Flask 集成                   │
├─────────────────────────────────────────────────────────────┤
│  Streamlit Web App (端口 8080)                              │
│  ├── 📊 数据概览                                            │
│  ├── 📝 模板生成器                                          │
│  ├── 📅 ICS日历管理 (新增)                                  │
│  └── ⚙️ 系统设置                                            │
│                                                             │
│  Flask 静态文件服务 (端口 5000)                              │
│  ├── /calendars/*.ics - ICS文件服务                         │
│  ├── /api/update-calendars - 更新API                        │
│  ├── /api/status - 状态API                                  │
│  └── /health - 健康检查                                     │
└─────────────────────────────────────────────────────────────┘
```

### 文件结构
```
/calendars/
├── grace_irvine_coordinator.ics  # 负责人日历订阅
└── grace_irvine_workers.ics      # 同工日历订阅
```

## 🚀 部署步骤

### 1. 安装依赖

```bash
# 安装新增的依赖
pip install flask==3.0.0 requests==2.31.0
```

### 2. 启动应用

```bash
# 启动Streamlit应用（会自动启动Flask服务器）
streamlit run streamlit_app.py
```

### 3. 验证服务

```bash
# 运行测试脚本
python3 test_static_service.py
```

## 📱 用户订阅指南

### 订阅URL格式
```
负责人日历: https://your-app-url.run.app/calendars/grace_irvine_coordinator.ics
同工日历: https://your-app-url.run.app/calendars/grace_irvine_workers.ics
```

### 订阅方法

#### Google Calendar
1. 打开Google Calendar
2. 左侧点击"+"号
3. 选择"从URL添加"
4. 粘贴订阅URL
5. 点击"添加日历"

#### Apple Calendar
1. 打开Calendar应用
2. "文件" → "新建日历订阅"
3. 输入订阅URL
4. 点击"订阅"

#### Outlook
1. 打开Outlook
2. "日历" → "添加日历"
3. "从Internet订阅"
4. 输入订阅URL

## 🔧 技术实现

### Flask静态文件服务

```python
# 创建Flask应用
flask_app = Flask(__name__)

@flask_app.route('/calendars/<filename>')
def serve_calendar(filename):
    """提供ICS日历文件下载"""
    return send_from_directory(
        'calendars', 
        filename, 
        mimetype='text/calendar; charset=utf-8'
    )
```

### 后台服务启动

```python
def ensure_flask_server():
    """确保Flask服务器正在运行"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    
    # 启动Flask服务器
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    return True
```

### API端点

#### 健康检查
```
GET /health
```

#### 系统状态
```
GET /api/status
```

#### 更新日历
```
POST /api/update-calendars
```

## 📊 管理界面

### ICS日历管理页面

在Streamlit应用中访问"📅 ICS日历管理"页面：

1. **📋 日历生成**
   - 生成负责人日历
   - 生成同工日历
   - 下载ICS文件

2. **🔗 订阅管理**
   - 显示订阅URL
   - 提供订阅指导
   - API端点信息

3. **⚙️ 自动更新**
   - 手动触发更新
   - 查看服务状态
   - 监控更新状态

4. **📊 系统状态**
   - 文件状态监控
   - 组件状态检查
   - 系统健康状态

## 🔄 自动更新机制

### 更新流程
```
Google Sheets数据变化 → 手动触发更新 → 生成新ICS文件 → 用户日历自动刷新
```

### 更新方式
1. **手动更新**: 在Web界面点击"生成日历"按钮
2. **API更新**: 调用 `/api/update-calendars` 端点
3. **定时更新**: 通过Cloud Scheduler定时触发

## 🛠️ 故障排除

### 常见问题

#### 1. Flask服务器未启动
```bash
# 检查Flask服务器状态
curl http://localhost:5000/health

# 重启Streamlit应用
streamlit run streamlit_app.py
```

#### 2. 日历文件无法访问
```bash
# 检查文件是否存在
ls -la calendars/

# 检查文件权限
chmod 644 calendars/*.ics
```

#### 3. 订阅URL无效
- 确认Cloud Run服务正在运行
- 检查URL格式是否正确
- 验证文件路径是否存在

### 调试命令

```bash
# 测试静态文件服务
python3 test_static_service.py

# 检查Flask服务器日志
# 在Streamlit应用运行时查看控制台输出

# 手动测试API端点
curl http://localhost:5000/api/status
curl -X POST http://localhost:5000/api/update-calendars
```

## 🎯 优势

### 1. **简化架构**
- ✅ 无需额外的Cloud Storage服务
- ✅ 统一管理所有功能
- ✅ 减少部署复杂度

### 2. **成本效益**
- ✅ 避免Cloud Storage费用
- ✅ 减少网络传输成本
- ✅ 最小化资源消耗

### 3. **性能优化**
- ✅ 本地文件访问更快
- ✅ 减少网络延迟
- ✅ 更好的用户体验

### 4. **易于维护**
- ✅ 单一应用管理
- ✅ 统一的日志和监控
- ✅ 简化的故障排除

## 📋 部署清单

### ✅ 已完成
1. **Flask静态文件服务集成**
2. **ICS日历管理页面**
3. **API端点实现**
4. **测试脚本创建**
5. **依赖包更新**

### 🔧 需要执行
1. **安装新依赖**:
   ```bash
   pip install flask==3.0.0 requests==2.31.0
   ```

2. **启动应用**:
   ```bash
   streamlit run streamlit_app.py
   ```

3. **测试服务**:
   ```bash
   python3 test_static_service.py
   ```

4. **生成日历文件**:
   - 访问"📅 ICS日历管理"页面
   - 点击"生成负责人日历"和"生成同工日历"

## 🎉 最终效果

### 管理员体验
- **统一界面**: 在Streamlit中管理所有功能
- **实时监控**: 查看系统状态和文件状态
- **一键操作**: 生成和更新日历文件

### 用户体验
- **简单订阅**: 使用固定URL订阅日历
- **自动更新**: 日历内容自动同步
- **多平台支持**: 支持主流日历应用

---

**集成完成时间**: 2024年12月
**状态**: ✅ 已完成静态文件服务集成
