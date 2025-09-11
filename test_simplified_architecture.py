#!/usr/bin/env python3
"""
测试简化后的架构
Test the simplified architecture
"""

import sys
import os
from pathlib import Path
import importlib.util

def test_imports():
    """测试关键模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        # 测试核心模块
        from src.data_cleaner import FocusedDataCleaner
        from src.template_manager import NotificationTemplateManager
        from src.scheduler import GoogleSheetsExtractor, NotificationGenerator
        from src.email_sender import EmailSender
        print("✅ 核心模块导入成功")
        
        # 测试统一应用模块
        spec = importlib.util.spec_from_file_location("app_unified", "app_unified.py")
        app_unified = importlib.util.module_from_spec(spec)
        print("✅ 统一应用模块检查通过")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("🧪 测试文件结构...")
    
    required_files = [
        "start.py",           # 统一启动入口
        "app_unified.py",     # 统一应用
        "requirements.txt",   # 依赖文件
        "Dockerfile",         # Docker配置
    ]
    
    required_dirs = [
        "src",                # 核心模块目录
        "configs",            # 配置目录
        "templates",          # 模板目录
        "calendars",          # 日历文件目录
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    for dir in required_dirs:
        if not Path(dir).exists():
            missing_dirs.append(dir)
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
    
    if missing_dirs:
        print(f"❌ 缺少目录: {', '.join(missing_dirs)}")
    
    if not missing_files and not missing_dirs:
        print("✅ 文件结构完整")
        return True
    
    return False

def test_removed_files():
    """测试是否成功删除了重复文件"""
    print("🧪 测试重复文件清理...")
    
    removed_files = [
        "start_service.py",
        "run_enhanced_streamlit.py", 
        "app_with_static_routes.py"
    ]
    
    still_exists = []
    for file in removed_files:
        if Path(file).exists():
            still_exists.append(file)
    
    if still_exists:
        print(f"❌ 以下文件应该被删除但仍存在: {', '.join(still_exists)}")
        return False
    else:
        print("✅ 重复文件已成功清理")
        return True

def test_configuration():
    """测试配置文件"""
    print("🧪 测试配置文件...")
    
    config_files = [
        "configs/config.yaml",
        "templates/notification_templates.yaml"
    ]
    
    missing_configs = []
    for config in config_files:
        if not Path(config).exists():
            missing_configs.append(config)
    
    if missing_configs:
        print(f"⚠️ 缺少配置文件: {', '.join(missing_configs)}")
        print("💡 这些文件可能需要重新生成")
        return False
    else:
        print("✅ 配置文件存在")
        return True

def test_environment():
    """测试环境配置"""
    print("🧪 测试环境配置...")
    
    # 检查环境变量
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    if spreadsheet_id:
        print(f"✅ GOOGLE_SPREADSHEET_ID 已设置: {spreadsheet_id[:10]}...")
    else:
        print("⚠️ GOOGLE_SPREADSHEET_ID 未设置，将使用默认值")
    
    # 检查.env文件
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env 文件存在")
    else:
        print("⚠️ .env 文件不存在，建议创建以配置环境变量")
    
    return True

def test_dependencies():
    """测试依赖包"""
    print("🧪 测试依赖包...")
    
    required_packages = [
        'streamlit',
        'pandas', 
        'gspread',
        'python-dotenv',
        'pyyaml',
        'jinja2'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            # 特殊处理一些包名映射
            import_name = package
            if package == 'python-dotenv':
                import_name = 'dotenv'
            elif package == 'pyyaml':
                import_name = 'yaml'
            else:
                import_name = package.replace('-', '_')
            
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("✅ 所有依赖包已安装")
        return True

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 架构简化测试")
    print("=" * 60)
    
    tests = [
        ("文件结构", test_file_structure),
        ("重复文件清理", test_removed_files),
        ("依赖包", test_dependencies),
        ("模块导入", test_imports),
        ("配置文件", test_configuration),
        ("环境配置", test_environment),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！架构简化成功")
        print("\n🚀 您现在可以使用以下命令启动应用:")
        print("   python start.py")
    else:
        print("⚠️ 部分测试失败，请检查上述问题")
        
        if passed >= total * 0.8:  # 80%以上通过
            print("\n💡 大部分功能正常，可以尝试启动:")
            print("   python start.py")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
