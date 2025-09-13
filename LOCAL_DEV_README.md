# 本地开发说明

## 🏠 本地开发环境

本项目采用**云端API + 本地UI**的架构：

- **云端**: API服务负责自动更新（每4小时）
- **本地**: UI服务负责手动管理和审查

## 🚀 本地启动

```bash
# 1. 设置环境
python local_dev_config.py

# 2. 启动UI服务
streamlit run app_unified.py
```

## 🔄 更新方式

### 本地环境
- 通过Web界面点击"生成/更新日历文件"按钮
- 直接调用本地calendar_generator模块
- 不需要启动API服务

### 云端环境
- 自动更新：每4小时通过Cloud Scheduler触发
- 手动更新：通过Web界面调用API服务

## 📁 文件说明

### 本地开发文件
- `app_unified.py` - Streamlit Web界面
- `src/` - 核心业务逻辑模块
- `templates/` - 模板文件
- `local_dev_config.py` - 本地环境配置

### 云端部署文件
- `deploy_dual_services.py` - 双服务部署脚本
- `cloud_scheduler_setup.sh` - 定时任务设置
- `Dockerfile.ui` - UI服务容器配置
- `deployment_config.json` - 部署配置记录

## 🌐 云端服务

- **UI服务**: https://grace-irvine-ui-760303847302.us-central1.run.app
- **API服务**: https://grace-irvine-api-760303847302.us-central1.run.app
- **自动更新**: 每4小时执行一次
