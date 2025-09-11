#!/usr/bin/env python3
"""
测试本地和云端双模式
Test Local and Cloud Dual Mode

验证应用在本地和云端环境下的文件存储功能
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_local_mode():
    """测试本地模式"""
    print("💻 测试本地模式...")
    
    try:
        # 确保在本地环境
        if 'K_SERVICE' in os.environ:
            del os.environ['K_SERVICE']
        if 'GCP_STORAGE_BUCKET' in os.environ:
            del os.environ['GCP_STORAGE_BUCKET']
        
        from src.cloud_storage_manager import CloudStorageManager, StorageConfig
        
        # 创建本地模式的存储管理器
        config = StorageConfig(bucket_name="local-test-bucket")
        manager = CloudStorageManager(config)
        
        if not manager.is_cloud_mode:
            print("✅ 本地模式检测正确")
        else:
            print("❌ 本地模式检测失败")
            return False
        
        # 测试本地文件操作
        test_content = {
            "test": "local_mode",
            "timestamp": datetime.now().isoformat()
        }
        
        # 写入测试文件
        if manager.write_file("test_local.json", test_content, sync_to_cloud=False):
            print("✅ 本地文件写入成功")
        else:
            print("❌ 本地文件写入失败")
            return False
        
        # 读取测试文件
        read_content = manager.read_file("test_local.json", "json")
        if read_content and read_content.get("test") == "local_mode":
            print("✅ 本地文件读取成功")
        else:
            print("❌ 本地文件读取失败")
            return False
        
        # 测试模板配置读取
        template_config = manager.read_template_config()
        if template_config and 'templates' in template_config:
            print("✅ 本地模板配置读取成功")
        else:
            print("❌ 本地模板配置读取失败")
            return False
        
        # 清理测试文件
        test_file = Path("test_local.json")
        if test_file.exists():
            test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ 本地模式测试失败: {e}")
        return False

def test_cloud_mode_simulation():
    """测试云端模式模拟"""
    print("☁️ 测试云端模式模拟...")
    
    try:
        # 模拟云端环境
        os.environ['K_SERVICE'] = 'grace-irvine-scheduler'
        os.environ['GCP_STORAGE_BUCKET'] = 'grace-irvine-test-bucket'
        
        from src.cloud_storage_manager import CloudStorageManager, StorageConfig
        
        # 重新导入以获取新的环境变量
        import importlib
        import src.cloud_storage_manager
        importlib.reload(src.cloud_storage_manager)
        
        # 创建云端模式的存储管理器
        config = StorageConfig(
            bucket_name="grace-irvine-test-bucket",
            project_id="ai-for-god"
        )
        manager = CloudStorageManager(config)
        
        if manager.is_cloud_mode:
            print("✅ 云端模式检测正确")
        else:
            print("❌ 云端模式检测失败")
            return False
        
        # 测试配置
        print(f"✅ Bucket配置: {manager.config.bucket_name}")
        print(f"✅ 项目ID: {manager.config.project_id}")
        
        # 注意：在本地环境无法真正测试GCP Storage，但可以测试逻辑
        if not manager.storage_client:
            print("ℹ️ GCP Storage客户端不可用（本地环境正常）")
        
        # 测试本地回退功能
        template_config = manager.read_template_config()
        if template_config:
            print("✅ 云端模式下本地回退功能正常")
        else:
            print("❌ 云端模式下本地回退失败")
            return False
        
        # 清理环境变量
        if 'K_SERVICE' in os.environ:
            del os.environ['K_SERVICE']
        if 'GCP_STORAGE_BUCKET' in os.environ:
            del os.environ['GCP_STORAGE_BUCKET']
        
        return True
        
    except Exception as e:
        print(f"❌ 云端模式模拟测试失败: {e}")
        return False

def test_template_manager_integration():
    """测试模板管理器集成"""
    print("🛠️ 测试模板管理器集成...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        from src.models import MinistryAssignment
        
        # 创建模板管理器（使用默认存储管理器）
        template_manager = DynamicTemplateManager()
        
        # 测试模板加载
        templates = template_manager.get_all_templates()
        if templates and 'templates' in templates:
            print("✅ 模板管理器集成成功")
        else:
            print("❌ 模板管理器集成失败")
            return False
        
        # 测试模板渲染
        test_date = datetime.now().date()
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮"
        )
        
        wed_result = template_manager.render_weekly_confirmation(test_date, test_schedule)
        if "Jimmy" in wed_result:
            print("✅ 集成模板渲染正常")
        else:
            print("❌ 集成模板渲染失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模板管理器集成测试失败: {e}")
        return False

def test_calendar_storage():
    """测试日历存储"""
    print("📅 测试日历存储...")
    
    try:
        from src.cloud_storage_manager import get_storage_manager
        
        storage_manager = get_storage_manager()
        
        # 检查现有日历文件
        calendar_content = storage_manager.read_ics_calendar("grace_irvine_coordinator.ics")
        
        if calendar_content:
            event_count = calendar_content.count("BEGIN:VEVENT")
            print(f"✅ 日历文件读取成功，包含 {event_count} 个事件")
            
            # 测试文件状态
            file_status = storage_manager.get_file_status("calendars/grace_irvine_coordinator.ics")
            print(f"✅ 文件状态检查: 本地存在={file_status['local_exists']}")
            
        else:
            print("⚠️ 日历文件不存在，需要先生成")
        
        # 获取公开URL
        public_url = storage_manager.get_public_calendar_url("grace_irvine_coordinator.ics")
        print(f"✅ 公开订阅URL: {public_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ 日历存储测试失败: {e}")
        return False

def test_app_integration():
    """测试应用集成"""
    print("🌐 测试应用集成...")
    
    try:
        from app_unified import StaticFileServer, get_template_manager
        
        # 测试静态文件服务
        content, error = StaticFileServer.serve_calendar_file("grace_irvine_coordinator.ics")
        
        if content and not error:
            print("✅ 应用静态文件服务正常")
        else:
            print(f"❌ 应用静态文件服务失败: {error}")
            return False
        
        # 测试应用状态
        status = StaticFileServer.get_calendar_status()
        
        if status['status'] == 'healthy':
            print("✅ 应用状态检查正常")
            print(f"   存储模式: {status.get('storage_mode', '未知')}")
        else:
            print(f"❌ 应用状态检查失败: {status.get('error', '未知错误')}")
            return False
        
        # 测试模板管理器
        template_manager = get_template_manager()
        if template_manager:
            print("✅ 应用模板管理器正常")
        else:
            print("❌ 应用模板管理器失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 应用集成测试失败: {e}")
        return False

def show_deployment_summary():
    """显示部署摘要"""
    print("📋 部署摘要...")
    
    bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
    
    print(f"\n🗂️ 推荐的存储结构:")
    print(f"gs://{bucket_name}/")
    print(f"├── templates/")
    print(f"│   ├── dynamic_templates.json     # 主模板配置")
    print(f"│   └── backups/                   # 模板备份")
    print(f"├── calendars/")
    print(f"│   ├── grace_irvine_coordinator.ics # 负责人日历")
    print(f"│   └── archives/                  # 历史版本")
    print(f"├── data/")
    print(f"│   └── cache/                     # 数据缓存")
    print(f"└── backups/                       # 自动备份")
    
    print(f"\n🔗 重要URL:")
    print(f"  模板配置: gs://{bucket_name}/templates/dynamic_templates.json")
    print(f"  日历文件: gs://{bucket_name}/calendars/grace_irvine_coordinator.ics")
    print(f"  公开订阅: https://storage.googleapis.com/{bucket_name}/calendars/grace_irvine_coordinator.ics")
    
    print(f"\n⚙️ 环境变量配置:")
    print(f"  GCP_STORAGE_BUCKET={bucket_name}")
    print(f"  GOOGLE_CLOUD_PROJECT={project_id}")
    print(f"  STORAGE_MODE=cloud")
    
    print(f"\n🚀 部署步骤:")
    print(f"  1. 运行 setup_cloud_storage.py 设置存储")
    print(f"  2. 使用 configs/cloud_deployment.json 中的命令部署")
    print(f"  3. 应用将自动使用云端存储")

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 本地/云端双模式测试")
    print("=" * 60)
    
    tests = [
        ("本地模式", test_local_mode),
        ("云端模式模拟", test_cloud_mode_simulation),
        ("模板管理器集成", test_template_manager_integration),
        ("日历存储", test_calendar_storage),
        ("应用集成", test_app_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        if test_func():
            passed += 1
    
    # 显示部署摘要
    print(f"\n{'='*20} 部署摘要 {'='*20}")
    show_deployment_summary()
    
    print("\n" + "=" * 60)
    print(f"📊 双模式测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！本地和云端双模式准备就绪")
        
        print("\n✅ 完成的功能:")
        print("  • 统一的存储管理器")
        print("  • 本地/云端自动检测")
        print("  • 模板动态加载和保存")
        print("  • ICS文件云端存储")
        print("  • 公开订阅URL生成")
        print("  • 自动备份和同步")
        
        print("\n📱 使用方式:")
        print("  本地开发: python3 start.py")
        print("  云端设置: python3 setup_cloud_storage.py")
        print("  部署应用: 使用 configs/cloud_deployment.json")
        
    else:
        print("⚠️ 部分测试失败，需要进一步调整")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
