# Cloud Run 静态文件服务部署指南

## 🎯 概述

本指南说明如何将支持静态文件服务的Grace Irvine Ministry Scheduler部署到Google Cloud Run，提供ICS日历文件的订阅服务。

## 🏗️ 架构设计

### Cloud Run 集成架构
```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Run                         │
├─────────────────────────────────────────────────────────────┤
│  Streamlit Web App (端口 8080)                              │
│  ├── 📊 数据概览                                            │
│  ├── 📝 模板生成器                                          │
│  ├── 📅 ICS日历管理                                         │
│  ├── ⚙️ 系统设置                                            │
│  └── 📁 静态文件服务                                        │
│     ├── /calendars/*.ics - ICS文件下载                      │
│     ├── /api/status - 系统状态                              │
│     └── /health - 健康检查                                  │
└─────────────────────────────────────────────────────────────┘
```

### 文件结构
```
/calendars/
├── grace_irvine_coordinator.ics  # 负责人日历订阅
└── grace_irvine_workers.ics      # 同工日历订阅
```

## 🚀 部署步骤

### 1. 准备环境

```bash
# 确保已安装gcloud CLI
gcloud auth login
gcloud config set project ai-for-god

# 安装依赖
pip install flask==3.0.0 requests==2.31.0
```

### 2. 使用部署脚本

```bash
# 运行部署脚本
python3 deploy_cloud_run_with_static.py
```

### 3. 手动部署

```bash
# 构建Docker镜像
gcloud builds submit --tag gcr.io/ai-for-god/grace-irvine-scheduler .

# 部署到Cloud Run
gcloud run deploy grace-irvine-scheduler \
    --image=gcr.io/ai-for-god/grace-irvine-scheduler \
    --platform=managed \
    --region=us-central1 \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --timeout=3600 \
    --concurrency=80 \
    --max-instances=10 \
    --set-env-vars="STREAMLIT_SERVER_HEADLESS=true,STREAMLIT_SERVER_ENABLE_CORS=false,STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false" \
    --port=8080
```

## 📱 用户订阅URL

### 部署后的URL结构
```
Streamlit Web界面: https://grace-irvine-scheduler-HASH-uc.a.run.app
负责人日历订阅: https://grace-irvine-scheduler-HASH-uc.a.run.app/calendars/grace_irvine_coordinator.ics
同工日历订阅: https://grace-irvine-scheduler-HASH-uc.a.run.app/calendars/grace_irvine_workers.ics
系统状态API: https://grace-irvine-scheduler-HASH-uc.a.run.app/api/status
健康检查: https://grace-irvine-scheduler-HASH-uc.a.run.app/health
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

### Dockerfile配置
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日历目录
RUN mkdir -p /app/calendars

# 设置环境变量
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
```

### 静态文件服务实现
```python
def serve_calendar_file(filename):
    """提供ICS日历文件下载"""
    try:
        calendar_dir = Path("calendars")
        file_path = calendar_dir / filename
        
        if not file_path.exists():
            return f"Calendar file {filename} not found", 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content, 200, {
            'Content-Type': 'text/calendar; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
        }
    except Exception as e:
        return f"Error serving calendar file: {str(e)}", 500
```

## 📊 管理界面

### ICS日历管理页面功能
1. **📋 日历生成** - 生成负责人和同工日历
2. **🔗 订阅管理** - 显示订阅URL和指导
3. **⚙️ 自动更新** - 手动触发更新和查看状态
4. **📊 系统状态** - 监控文件状态和系统健康

### API端点
- `GET /calendars/<filename>` - 下载ICS文件
- `GET /api/status` - 获取系统状态
- `POST /api/update-calendars` - 触发日历更新
- `GET /health` - 健康检查

## 🔄 自动更新机制

### 更新流程
```
Google Sheets数据变化 → 手动触发更新 → 生成新ICS文件 → 用户日历自动刷新
```

### 更新方式
1. **Web界面更新** - 在"📅 ICS日历管理"页面点击生成按钮
2. **API更新** - 调用 `/api/update-calendars` 端点
3. **Cloud Scheduler** - 定时触发更新（可选）

## 🛠️ 故障排除

### 常见问题

#### 1. 部署失败
```bash
# 检查项目配置
gcloud config list

# 检查API是否启用
gcloud services list --enabled

# 查看构建日志
gcloud builds log [BUILD_ID]
```

#### 2. 服务无法访问
```bash
# 检查服务状态
gcloud run services describe grace-irvine-scheduler --region=us-central1

# 查看服务日志
gcloud run services logs read grace-irvine-scheduler --region=us-central1
```

#### 3. 日历文件无法下载
```bash
# 检查文件是否存在
curl https://your-service-url.run.app/calendars/grace_irvine_coordinator.ics

# 检查健康状态
curl https://your-service-url.run.app/health
```

### 调试命令

```bash
# 本地测试
streamlit run streamlit_app.py

# 测试静态文件服务
curl http://localhost:8080/calendars/grace_irvine_coordinator.ics

# 检查服务状态
curl http://localhost:8080/api/status
```

## 🎯 关键优势

### 1. **简化架构**
- ✅ 单一Cloud Run实例包含所有功能
- ✅ 无需额外的Cloud Storage服务
- ✅ 统一的部署和管理

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
1. **Dockerfile创建** - 支持静态文件服务
2. **Streamlit应用更新** - 集成静态文件处理
3. **部署脚本创建** - 自动化部署流程
4. **配置文件创建** - Cloud Run配置
5. **文档更新** - 完整的部署指南

### 🔧 需要执行
1. **运行部署脚本**:
   ```bash
   python3 deploy_cloud_run_with_static.py
   ```

2. **验证部署**:
   ```bash
   # 获取服务URL
   gcloud run services describe grace-irvine-scheduler --region=us-central1 --format="value(status.url)"
   
   # 测试日历文件访问
   curl https://your-service-url.run.app/calendars/grace_irvine_coordinator.ics
   ```

3. **生成日历文件**:
   - 访问Web界面
   - 点击"📅 ICS日历管理"
   - 生成负责人和同工日历

## 🎉 最终效果

### 管理员体验
- **统一界面** - 在Streamlit中管理所有功能
- **实时监控** - 查看系统状态和文件状态
- **一键部署** - 自动化部署流程

### 用户体验
- **简单订阅** - 使用固定URL订阅日历
- **自动更新** - 日历内容自动同步
- **多平台支持** - 支持主流日历应用

---

**部署完成时间**: 2024年12月
**状态**: ✅ 已完成Cloud Run静态文件服务部署配置
