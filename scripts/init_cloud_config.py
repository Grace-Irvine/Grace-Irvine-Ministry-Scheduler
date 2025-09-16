#!/usr/bin/env python3
"""
云端配置初始化脚本
Cloud Configuration Initialization Script

在部署后首次运行时，将默认配置同步到云端存储
"""

import os
import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_cloud_configs():
    """初始化云端配置"""
    print("🚀 初始化云端配置...")
    print("=" * 50)
    
    try:
        # 导入必要的模块
        from src.reminder_config_manager import get_reminder_manager
        from src.cloud_storage_manager import get_storage_manager
        
        # 获取管理器
        storage_manager = get_storage_manager()
        reminder_manager = get_reminder_manager()
        
        print(f"📊 环境信息:")
        print(f"  云端模式: {'✅' if storage_manager.is_cloud_mode else '❌'}")
        print(f"  Bucket: {storage_manager.config.bucket_name}")
        print(f"  项目ID: {storage_manager.config.project_id}")
        
        if not storage_manager.is_cloud_mode:
            print("💡 当前为本地模式，跳过云端初始化")
            return True
        
        # 检查云端配置是否已存在
        storage_status = reminder_manager.get_storage_status()
        
        if storage_status['cloud_file_exists']:
            print("✅ 云端配置已存在，无需初始化")
            print(f"  最后更新: {storage_status['last_sync_time']}")
            return True
        
        print("📁 云端配置不存在，开始初始化...")
        
        # 从默认配置文件加载
        default_config_path = PROJECT_ROOT / "configs" / "default_reminder_settings.json"
        
        if default_config_path.exists():
            print(f"📋 从默认配置加载: {default_config_path}")
            
            with open(default_config_path, 'r', encoding='utf-8') as f:
                default_config = json.load(f)
            
            # 更新时间戳
            from datetime import datetime
            default_config['last_updated'] = datetime.now().isoformat()
            default_config['description'] = 'Grace Irvine Ministry Scheduler - 云端初始化配置'
            
            # 直接写入云端
            success = storage_manager.write_file(
                "configs/reminder_settings.json",
                default_config,
                sync_to_cloud=True,
                backup=True
            )
            
            if success:
                print("✅ 默认配置已成功同步到云端")
                
                # 重新加载配置以验证
                reminder_manager.load_configs()
                configs = reminder_manager.get_all_configs()
                print(f"📋 验证完成，加载了 {len(configs)} 个配置")
                
                return True
            else:
                print("❌ 云端同步失败")
                return False
                
        else:
            print("⚠️ 默认配置文件不存在，使用代码中的默认配置")
            
            # 使用代码中的默认配置并保存
            if reminder_manager.force_sync_to_cloud():
                print("✅ 代码默认配置已同步到云端")
                return True
            else:
                print("❌ 同步代码默认配置失败")
                return False
    
    except Exception as e:
        logger.error(f"初始化云端配置失败: {e}")
        return False

def check_cloud_connectivity():
    """检查云端连接性"""
    print("\n🌐 检查云端连接性...")
    print("-" * 30)
    
    try:
        from src.cloud_storage_manager import get_storage_manager
        
        storage_manager = get_storage_manager()
        
        if not storage_manager.is_cloud_mode:
            print("ℹ️ 本地模式，跳过云端连接检查")
            return True
        
        # 测试写入一个小文件
        test_data = {
            "test": True,
            "timestamp": storage_manager._get_current_time_str() if hasattr(storage_manager, '_get_current_time_str') else "test"
        }
        
        test_path = "test/connectivity_test.json"
        
        if storage_manager.write_file(test_path, test_data, sync_to_cloud=True, backup=False):
            print("✅ 云端写入测试成功")
            
            # 尝试读取
            read_data = storage_manager.read_file(test_path, "json")
            if read_data and read_data.get("test") == True:
                print("✅ 云端读取测试成功")
                
                # 清理测试文件
                try:
                    if hasattr(storage_manager, 'bucket') and storage_manager.bucket:
                        blob = storage_manager.bucket.blob(test_path)
                        if blob.exists():
                            blob.delete()
                            print("🗑️ 测试文件已清理")
                except:
                    pass  # 清理失败不影响主要功能
                
                return True
            else:
                print("❌ 云端读取测试失败")
                return False
        else:
            print("❌ 云端写入测试失败")
            return False
            
    except Exception as e:
        logger.error(f"云端连接检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 Grace Irvine Ministry Scheduler - 云端配置初始化")
    print("=" * 70)
    
    # 检查环境变量
    required_vars = ['GCP_STORAGE_BUCKET', 'GOOGLE_CLOUD_PROJECT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        print("💡 如果在本地开发，这是正常的")
    else:
        print("✅ 环境变量检查通过")
    
    # 检查云端连接
    connectivity_ok = check_cloud_connectivity()
    
    # 初始化配置
    config_ok = init_cloud_configs()
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 初始化结果:")
    print(f"  云端连接: {'✅ 正常' if connectivity_ok else '❌ 异常'}")
    print(f"  配置初始化: {'✅ 成功' if config_ok else '❌ 失败'}")
    
    if connectivity_ok and config_ok:
        print("\n🎉 云端配置初始化完成！")
        print("\n📋 后续步骤:")
        print("  1. 用户可以通过前端界面修改提醒配置")
        print("  2. 配置会自动保存到云端存储")
        print("  3. 生成ICS文件时会读取最新配置")
        
        return True
    else:
        print("\n⚠️ 初始化过程中遇到问题，但不影响基本功能")
        print("💡 系统会自动回退到本地配置或默认配置")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
