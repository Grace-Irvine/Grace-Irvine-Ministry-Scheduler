#!/usr/bin/env python3
"""
本地开发配置
Local Development Configuration

用于本地开发时的环境配置和选项
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

def setup_local_environment():
    """设置本地开发环境"""
    print("🔧 设置本地开发环境")
    print("=" * 50)
    
    # 备份云端配置
    env_file = PROJECT_ROOT / ".env"
    env_cloud = PROJECT_ROOT / ".env.cloud"
    env_local = PROJECT_ROOT / ".env.local"
    
    if env_file.exists() and not env_cloud.exists():
        # 备份当前.env为云端配置
        import shutil
        shutil.copy(env_file, env_cloud)
        print("📄 备份云端配置到 .env.cloud")
    
    # 创建本地配置
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换STORAGE_MODE为local
        content = content.replace('STORAGE_MODE=cloud', 'STORAGE_MODE=local')
        
        with open(env_local, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 使用本地配置
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("📄 创建本地配置 .env.local")
        print("📄 切换到本地环境配置")
    
    # 设置环境变量
    os.environ["STORAGE_MODE"] = "local"
    os.environ["PYTHONPATH"] = str(PROJECT_ROOT)
    
    # 确保必要目录存在
    for dir_name in ['calendars', 'data', 'logs', 'templates']:
        (PROJECT_ROOT / dir_name).mkdir(exist_ok=True)
    
    print("✅ 本地环境设置完成")
    print()
    print("📝 本地开发说明:")
    print("- UI服务: 运行 streamlit run app_unified.py")
    print("- 手动更新: 通过Web界面点击'生成/更新日历文件'按钮")
    print("- 直接生成: 运行 python -m src.calendar_generator")
    print()
    print("⚠️ 注意:")
    print("- 本地环境不需要启动API服务")
    print("- 本地更新直接调用calendar_generator模块")
    print("- 云端环境会自动调用API服务")
    print()
    print("🔄 环境切换:")
    print("- 本地开发: cp .env.local .env")
    print("- 云端部署: cp .env.cloud .env")

def check_local_requirements():
    """检查本地开发所需的文件和配置"""
    print("🔍 检查本地开发环境")
    print("=" * 50)
    
    required_files = [
        ".env",
        "src/calendar_generator.py",
        "src/data_cleaner.py",
        "src/dynamic_template_manager.py",
        "templates/dynamic_templates.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (PROJECT_ROOT / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少以下文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ 所有必需文件都存在")
        return True

if __name__ == "__main__":
    setup_local_environment()
    check_local_requirements()
