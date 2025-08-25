#!/usr/bin/env python3
"""
项目清理脚本 - 删除不必要的复杂文件
Project Cleanup Script - Remove unnecessary complex files
"""
import os
import shutil
from pathlib import Path

def main():
    """执行项目清理"""
    project_root = Path(__file__).parent
    
    print("🧹 Grace Irvine Ministry Scheduler - 项目清理")
    print("=" * 50)
    
    # 要删除的文件和目录
    items_to_remove = [
        # 复杂的架构文件
        "app/",  # 整个 FastAPI 应用目录
        "infra/",  # 基础设施配置
        "deployment/",  # 部署配置
        "templates/",  # 复杂模板系统
        
        # 复杂的脚本
        "clean_sheets_data.py",
        "generate_notifications.py",
        "check_data.py",
        "modify_template.py",
        "template_examples.py",
        "test_simple.py",
        
        # 批处理和shell脚本
        "run_notifications.bat",
        "run_notifications.sh",
        
        # 复杂的文档
        "ARCHITECTURE.md",
        "IMPLEMENTATION_SUMMARY.md",
        "QUICK_START.md",
        "SIMPLE_SETUP.md",
        "TEMPLATE_CUSTOMIZATION.md",
        "DATA_CLEANING_GUIDE.md",
        
        # 复杂的配置
        "configs/README.md",
        "env.example",
        "simple_env_example",
        "simple_requirements.txt",
        "simple_scheduler.py",
        
        # 缓存和临时文件
        "__pycache__/",
        "*.pyc",
        ".DS_Store",
    ]
    
    removed_count = 0
    kept_important = []
    
    for item in items_to_remove:
        item_path = project_root / item
        
        if item_path.exists():
            try:
                if item_path.is_file():
                    item_path.unlink()
                    print(f"  ❌ 删除文件: {item}")
                    removed_count += 1
                elif item_path.is_dir():
                    shutil.rmtree(item_path)
                    print(f"  ❌ 删除目录: {item}")
                    removed_count += 1
            except Exception as e:
                print(f"  ⚠️  无法删除 {item}: {e}")
        else:
            print(f"  ℹ️  不存在: {item}")
    
    # 保留的重要文件
    important_files = [
        "streamlit_app.py",
        "simple_data_cleaner.py", 
        "run_streamlit.py",
        "run_data_cleaning.py",
        "requirements.txt",
        "README_SIMPLIFIED.md",
        "LICENSE",
        "data/",
        "configs/service_account.json"
    ]
    
    print(f"\n✅ 清理完成，删除了 {removed_count} 个项目")
    print("\n📋 保留的核心文件:")
    
    for file in important_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"  ✅ {file}")
            kept_important.append(file)
        else:
            print(f"  ❓ {file} (不存在)")
    
    print(f"\n🎯 简化后的项目结构:")
    print("```")
    print("Grace-Irvine-Ministry-Scheduler/")
    print("├── streamlit_app.py          # 📱 Web 界面主应用")
    print("├── simple_data_cleaner.py    # 🧹 数据清洗核心")
    print("├── run_streamlit.py          # 🚀 Web 应用启动脚本")
    print("├── run_data_cleaning.py      # 🔧 数据清洗启动脚本")
    print("├── requirements.txt          # 📦 依赖包列表")
    print("├── README_SIMPLIFIED.md      # 📖 简化版文档")
    print("├── LICENSE                   # ⚖️  开源许可")
    print("├── data/                     # 💾 数据存储目录")
    print("│   ├── *.xlsx               # 清洗后的数据文件")
    print("│   └── *.json               # 清洗报告文件")
    print("└── configs/                  # ⚙️  配置文件")
    print("    └── service_account.json  # 🔑 Google API 密钥")
    print("```")
    
    print(f"\n🎉 项目简化完成！")
    print("现在您可以使用以下命令启动应用:")
    print("  python3 run_streamlit.py")
    print("\n或者直接运行数据清洗:")
    print("  python3 run_data_cleaning.py")

if __name__ == "__main__":
    main()
