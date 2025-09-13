#!/usr/bin/env python3
"""
清理本地API相关文件
Clean up local API-related files

移除本地开发不需要的API服务相关文件
"""

import os
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 需要清理的文件和目录
FILES_TO_REMOVE = [
    "api_service.py",  # API服务主文件
    "run_services.py",  # 双服务启动脚本
    "test_api_endpoints.py",  # API测试脚本
    "test_dual_services.py",  # 双服务测试脚本
    "Dockerfile.api",  # API服务Dockerfile
    "cloudbuild-api.yaml",  # API服务构建配置
]

# 保留但说明的文件
FILES_TO_KEEP = [
    "deploy_dual_services.py",  # 云端部署脚本（云端需要）
    "cloud_scheduler_setup.sh",  # Cloud Scheduler设置（云端需要）
    "Dockerfile.ui",  # UI服务Dockerfile（云端需要）
    "cloudbuild-ui.yaml",  # UI服务构建配置（云端需要）
    "deployment_config.json",  # 部署配置记录
]

def cleanup_local_api_files():
    """清理本地API相关文件"""
    print("🧹 清理本地API相关文件")
    print("=" * 50)
    
    removed_files = []
    
    for file_name in FILES_TO_REMOVE:
        file_path = PROJECT_ROOT / file_name
        if file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()
                    removed_files.append(file_name)
                    print(f"✅ 删除文件: {file_name}")
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    removed_files.append(file_name)
                    print(f"✅ 删除目录: {file_name}")
            except Exception as e:
                print(f"❌ 删除失败 {file_name}: {e}")
        else:
            print(f"⏭️ 文件不存在: {file_name}")
    
    print()
    print("📋 保留的云端部署相关文件:")
    for file_name in FILES_TO_KEEP:
        file_path = PROJECT_ROOT / file_name
        if file_path.exists():
            print(f"   📄 {file_name} (云端部署需要)")
        else:
            print(f"   ❓ {file_name} (文件不存在)")
    
    print()
    if removed_files:
        print(f"🎉 清理完成！删除了 {len(removed_files)} 个文件")
        print("📝 本地开发说明:")
        print("- 本地只需要运行 streamlit run app_unified.py")
        print("- 手动更新通过Web界面调用本地calendar_generator")
        print("- 云端环境会自动调用API服务")
    else:
        print("ℹ️ 没有需要清理的文件")

def create_local_readme():
    """创建本地开发说明文件"""
    readme_content = """# 本地开发说明

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
"""
    
    readme_path = PROJECT_ROOT / "LOCAL_DEV_README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"📄 创建本地开发说明: {readme_path}")

if __name__ == "__main__":
    cleanup_local_api_files()
    create_local_readme()
    print()
    print("🎯 下一步:")
    print("1. 运行 python local_dev_config.py 设置本地环境")
    print("2. 运行 streamlit run app_unified.py 启动本地UI")
    print("3. 查看 LOCAL_DEV_README.md 了解详细说明")
