#!/usr/bin/env python3
"""
云端部署检查脚本
Cloud Deployment Check Script

验证云端部署是否包含所有经文分享功能的组件
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    path = Path(file_path)
    if path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} 缺失: {file_path}")
        return False

def check_bucket_files(bucket_name):
    """检查bucket中的文件"""
    print(f"🔍 检查存储桶文件: gs://{bucket_name}/")
    
    files_to_check = [
        ("templates/dynamic_templates.json", "动态模板配置"),
        ("templates/scripture_sharing.json", "经文分享配置"),
        ("calendars/README.txt", "日历目录"),
        ("data/cache/README.txt", "数据缓存目录"),
        ("backups/README.txt", "备份目录")
    ]
    
    success_count = 0
    for file_path, description in files_to_check:
        try:
            result = subprocess.run(
                f"gsutil ls gs://{bucket_name}/{file_path}",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ {description}: gs://{bucket_name}/{file_path}")
                success_count += 1
            else:
                print(f"❌ {description} 缺失: gs://{bucket_name}/{file_path}")
        except Exception as e:
            print(f"❌ 检查 {description} 失败: {e}")
    
    return success_count, len(files_to_check)

def check_local_files():
    """检查本地文件"""
    print("🔍 检查本地文件...")
    
    files_to_check = [
        ("src/scripture_manager.py", "经文管理器"),
        ("templates/scripture_sharing.json", "经文分享配置"),
        ("templates/dynamic_templates.json", "动态模板配置"),
        ("src/cloud_storage_manager.py", "云端存储管理器"),
        ("app_unified.py", "统一应用入口"),
        ("Dockerfile", "Docker配置"),
        ("requirements.txt", "Python依赖"),
        ("start.py", "启动脚本")
    ]
    
    success_count = 0
    for file_path, description in files_to_check:
        if check_file_exists(file_path, description):
            success_count += 1
    
    return success_count, len(files_to_check)

def check_scripture_config():
    """检查经文配置完整性"""
    print("🔍 检查经文配置完整性...")
    
    config_file = Path("templates/scripture_sharing.json")
    if not config_file.exists():
        print("❌ 经文配置文件不存在")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查基本结构
        if 'metadata' not in config:
            print("❌ 缺少metadata配置")
            return False
        
        if 'scriptures' not in config:
            print("❌ 缺少scriptures配置")
            return False
        
        scriptures = config['scriptures']
        metadata = config['metadata']
        
        print(f"✅ 经文总数: {len(scriptures)}")
        print(f"✅ 当前索引: {metadata.get('current_index', 0)}")
        print(f"✅ 版本信息: {metadata.get('version', 'Unknown')}")
        
        # 检查经文格式
        for i, scripture in enumerate(scriptures[:3]):  # 检查前3个
            if 'id' not in scripture or 'content' not in scripture:
                print(f"❌ 第{i+1}段经文格式错误")
                return False
        
        print("✅ 经文配置格式正确")
        return True
        
    except Exception as e:
        print(f"❌ 经文配置检查失败: {e}")
        return False

def check_deployment_config():
    """检查部署配置"""
    print("🔍 检查部署配置...")
    
    config_file = Path("configs/cloud_deployment.json")
    if not config_file.exists():
        print("❌ 部署配置文件不存在")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_fields = [
            "service_name",
            "image", 
            "region",
            "environment_variables"
        ]
        
        for field in required_fields:
            if field not in config:
                print(f"❌ 缺少配置字段: {field}")
                return False
        
        env_vars = config['environment_variables']
        required_env_vars = [
            "GCP_STORAGE_BUCKET",
            "GOOGLE_CLOUD_PROJECT",
            "STORAGE_MODE",
            "PORT"
        ]
        
        for var in required_env_vars:
            if var not in env_vars:
                print(f"❌ 缺少环境变量: {var}")
                return False
        
        print(f"✅ 服务名称: {config['service_name']}")
        print(f"✅ 存储桶: {env_vars['GCP_STORAGE_BUCKET']}")
        print(f"✅ 项目ID: {env_vars['GOOGLE_CLOUD_PROJECT']}")
        print(f"✅ 存储模式: {env_vars['STORAGE_MODE']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 部署配置检查失败: {e}")
        return False

def check_dockerfile():
    """检查Dockerfile"""
    print("🔍 检查Dockerfile...")
    
    dockerfile = Path("Dockerfile")
    if not dockerfile.exists():
        print("❌ Dockerfile不存在")
        return False
    
    try:
        with open(dockerfile, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("COPY . .", "应用代码复制"),
            ("/app/templates", "模板目录创建"),
            ("scripture_sharing.json", "经文配置检查"),
            ("start.py", "启动脚本"),
            ("PORT=8080", "端口配置")
        ]
        
        success_count = 0
        for check_text, description in checks:
            if check_text in content:
                print(f"✅ {description}")
                success_count += 1
            else:
                print(f"❌ {description} 缺失")
        
        return success_count == len(checks)
        
    except Exception as e:
        print(f"❌ Dockerfile检查失败: {e}")
        return False

def main():
    """主检查函数"""
    print("🔍 Grace Irvine Ministry Scheduler - 云端部署检查")
    print("=" * 70)
    print()
    
    # 获取配置
    bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
    
    print(f"📋 检查配置:")
    print(f"   存储桶: {bucket_name}")
    print(f"   项目ID: {project_id}")
    print()
    
    checks = [
        ("本地文件检查", check_local_files),
        ("经文配置检查", check_scripture_config),
        ("部署配置检查", check_deployment_config),
        ("Dockerfile检查", check_dockerfile),
    ]
    
    success_checks = 0
    total_checks = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            if callable(check_func):
                if check_func():
                    success_checks += 1
                    print(f"✅ {check_name} 通过")
                else:
                    print(f"❌ {check_name} 失败")
            else:
                # 对于返回元组的函数
                success_count, total_count = check_func()
                if success_count == total_count:
                    success_checks += 1
                    print(f"✅ {check_name} 通过 ({success_count}/{total_count})")
                else:
                    print(f"❌ {check_name} 部分失败 ({success_count}/{total_count})")
        except Exception as e:
            print(f"❌ {check_name} 异常: {e}")
    
    # 检查bucket文件（可选）
    print(f"\n{'='*20} 存储桶文件检查 {'='*20}")
    try:
        bucket_success, bucket_total = check_bucket_files(bucket_name)
        if bucket_success > 0:
            print(f"ℹ️ 存储桶文件: {bucket_success}/{bucket_total} 存在")
        else:
            print("⚠️ 存储桶可能未初始化，运行 python3 setup_cloud_storage.py")
    except Exception as e:
        print(f"⚠️ 存储桶检查跳过: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 检查结果: {success_checks}/{total_checks} 通过")
    
    if success_checks == total_checks:
        print("🎉 云端部署就绪！所有检查通过。")
        print("\n📋 部署步骤:")
        print("1. 运行: python3 setup_cloud_storage.py  (初始化存储)")
        print("2. 运行: python3 deploy_to_cloud_run.py  (部署应用)")
        print("3. 访问应用URL验证功能")
        print("\n🔗 关键功能:")
        print("  • 经文分享: 周三通知自动包含经文")
        print("  • 云端存储: 配置自动同步到GCP Storage")
        print("  • 模板管理: 在线编辑并保存到云端")
        print("  • 日历订阅: 自动生成ICS文件")
    else:
        print("⚠️ 部分检查失败，请修复后再部署")
        print("\n🔧 常见修复方法:")
        print("  • 确保所有必要文件存在")
        print("  • 检查JSON配置文件格式")
        print("  • 验证环境变量设置")
        print("  • 更新Dockerfile和部署配置")
    
    return success_checks == total_checks

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
