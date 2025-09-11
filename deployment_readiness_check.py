#!/usr/bin/env python3
"""
部署就绪检查
Deployment Readiness Check

检查应用是否已准备好部署到GCP
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_core_files():
    """检查核心文件"""
    print("📁 检查核心文件...")
    
    required_files = {
        # 应用核心
        "start.py": "统一启动入口",
        "app_unified.py": "统一Web应用",
        "Dockerfile": "Docker配置",
        "requirements.txt": "依赖包列表",
        
        # 核心模块
        "src/models.py": "统一数据模型",
        "src/data_cleaner.py": "数据清洗器",
        "src/dynamic_template_manager.py": "动态模板管理器",
        "src/cloud_storage_manager.py": "云端存储管理器",
        "src/calendar_generator.py": "日历生成器",
        "src/email_sender.py": "邮件发送器",
        
        # 配置文件
        "configs/config.yaml": "基础配置",
        "templates/dynamic_templates.json": "动态模板配置",
    }
    
    missing_files = []
    for file_path, description in required_files.items():
        if not Path(file_path).exists():
            missing_files.append(f"{file_path} ({description})")
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ 缺少核心文件:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    return True

def check_dependencies():
    """检查依赖包"""
    print("📦 检查依赖包...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'gspread', 
        'google-cloud-storage',
        'python-dotenv',
        'pyyaml',
        'jinja2'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            elif package == 'pyyaml':
                import yaml
            elif package == 'google-cloud-storage':
                try:
                    import google.cloud.storage
                    print(f"✅ {package}")
                except ImportError:
                    missing_packages.append(package)
                    print(f"❌ {package}")
                continue
            else:
                __import__(package.replace('-', '_'))
            
            print(f"✅ {package}")
            
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n💡 安装缺失包: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_configuration():
    """检查配置"""
    print("⚙️ 检查配置...")
    
    # 检查环境变量
    env_vars = {
        'GOOGLE_SPREADSHEET_ID': '必需 - Google Sheets ID',
        'SENDER_EMAIL': '可选 - 发件人邮箱',
        'EMAIL_PASSWORD': '可选 - 邮箱密码',
        'GCP_STORAGE_BUCKET': '云端部署必需 - 存储桶名称',
        'GOOGLE_CLOUD_PROJECT': '云端部署必需 - 项目ID'
    }
    
    missing_required = []
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            if var in ['EMAIL_PASSWORD']:
                print(f"✅ {var}: ***已设置***")
            elif var in ['GOOGLE_SPREADSHEET_ID']:
                print(f"✅ {var}: {value[:10]}...")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: 未设置 ({description})")
            if '必需' in description:
                missing_required.append(var)
    
    # 检查配置文件内容
    print("\n📋 检查配置文件内容...")
    
    try:
        import yaml
        with open('configs/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if config.get('spreadsheet_id'):
            print("✅ config.yaml 包含spreadsheet_id")
        else:
            print("⚠️ config.yaml 缺少spreadsheet_id")
        
        import json
        with open('templates/dynamic_templates.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        if templates.get('templates'):
            template_count = len(templates['templates'])
            print(f"✅ dynamic_templates.json 包含 {template_count} 个模板")
        else:
            print("❌ dynamic_templates.json 格式错误")
            return False
            
    except Exception as e:
        print(f"❌ 配置文件检查失败: {e}")
        return False
    
    return len(missing_required) == 0

def check_functionality():
    """检查核心功能"""
    print("🔧 检查核心功能...")
    
    try:
        # 1. 数据模型
        from src.models import MinistryAssignment, ServiceRole
        print("✅ 统一数据模型导入成功")
        
        # 2. 存储管理器
        from src.cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        print(f"✅ 存储管理器初始化成功 ({storage_manager.storage_client is not None and '可用' or '本地模式'})")
        
        # 3. 模板管理器
        from src.dynamic_template_manager import DynamicTemplateManager
        template_manager = DynamicTemplateManager()
        print("✅ 动态模板管理器初始化成功")
        
        # 4. 数据清洗器
        from src.data_cleaner import FocusedDataCleaner
        cleaner = FocusedDataCleaner()
        print("✅ 数据清洗器初始化成功")
        
        # 5. 日历生成器
        from src.calendar_generator import get_template_manager
        calendar_template_manager = get_template_manager()
        print("✅ 日历生成器初始化成功")
        
        # 6. 统一应用
        import app_unified
        print("✅ 统一应用导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 核心功能检查失败: {e}")
        return False

def check_deployment_files():
    """检查部署文件"""
    print("🚀 检查部署文件...")
    
    deployment_files = [
        "Dockerfile",
        "setup_cloud_storage.py",
        "deploy_cloud_run_with_static.py"
    ]
    
    for file in deployment_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            return False
    
    # 检查Dockerfile内容
    try:
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        if 'start.py' in dockerfile_content:
            print("✅ Dockerfile 使用统一启动脚本")
        else:
            print("❌ Dockerfile 未使用统一启动脚本")
            return False
            
    except Exception as e:
        print(f"❌ Dockerfile检查失败: {e}")
        return False
    
    return True

def main():
    """主检查函数"""
    print("🎯 Grace Irvine Ministry Scheduler - 部署就绪检查")
    print("=" * 60)
    
    checks = [
        ("核心文件", check_core_files),
        ("依赖包", check_dependencies),
        ("配置", check_configuration),
        ("核心功能", check_functionality),
        ("部署文件", check_deployment_files),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        if check_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 部署就绪检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 应用完全准备就绪，可以部署到GCP！")
        
        print("\n✅ 就绪的功能:")
        print("  • 统一的应用架构")
        print("  • 完整的数据处理流程")
        print("  • 动态模板系统")
        print("  • 云端存储支持")
        print("  • ICS日历生成和订阅")
        print("  • Web界面管理")
        
        print("\n🚀 部署步骤:")
        print("  1. 本地测试: python3 start.py")
        print("  2. 设置存储: python3 setup_cloud_storage.py")
        print("  3. 部署应用: python3 deploy_cloud_run_with_static.py")
        print("  4. 访问应用并测试云端功能")
        
        print("\n📋 部署后可用功能:")
        print("  • 在线编辑模板（保存到云端）")
        print("  • 公开日历订阅URL")
        print("  • 自动数据同步和备份")
        print("  • 多环境支持（本地/云端）")
        
    else:
        failed_count = total - passed
        print(f"⚠️ {failed_count} 个检查失败，建议先解决这些问题")
        
        if passed >= total * 0.8:  # 80%以上通过
            print("\n💡 核心功能基本就绪，可以尝试部署")
            print("   但建议先解决上述问题以获得最佳体验")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎊 部署完全就绪！' if success else '⚠️ 需要进一步准备'}")
    sys.exit(0 if success else 1)
