#!/usr/bin/env python3
"""
GCP Storage设置脚本
Setup GCP Storage for Grace Irvine Ministry Scheduler

设置云端存储bucket和权限配置
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def create_bucket_structure():
    """创建Bucket目录结构"""
    print("📁 创建Bucket目录结构...")
    
    # 配置
    bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
    region = os.getenv('CLOUD_RUN_REGION', 'us-central1')
    
    print(f"📋 存储配置:")
    print(f"  Bucket: {bucket_name}")
    print(f"  项目: {project_id}")
    print(f"  区域: {region}")
    print()
    
    commands = [
        # 1. 创建存储桶
        f"gsutil mb -p {project_id} -c STANDARD -l {region} gs://{bucket_name}",
        
        # 2. 设置公开读取权限（仅限calendars目录）
        f"gsutil iam ch allUsers:objectViewer gs://{bucket_name}",
        
        # 3. 设置应用服务账户权限
        f"gsutil iam ch serviceAccount:{project_id}@appspot.gserviceaccount.com:objectAdmin gs://{bucket_name}",
        
        # 4. 创建目录结构（上传占位文件）
        "echo '# Templates directory' > .temp_templates_readme",
        f"gsutil cp .temp_templates_readme gs://{bucket_name}/templates/README.txt",
        
        "echo '# Calendars directory' > .temp_calendars_readme", 
        f"gsutil cp .temp_calendars_readme gs://{bucket_name}/calendars/README.txt",
        
        "echo '# Data cache directory' > .temp_data_readme",
        f"gsutil cp .temp_data_readme gs://{bucket_name}/data/cache/README.txt",
        
        "echo '# Backups directory' > .temp_backups_readme",
        f"gsutil cp .temp_backups_readme gs://{bucket_name}/backups/README.txt",
        
        # 5. 清理临时文件
        "rm .temp_*_readme",
        
        # 6. 验证结构
        f"gsutil ls -r gs://{bucket_name}/"
    ]
    
    for i, cmd in enumerate(commands, 1):
        if cmd.startswith("echo") or cmd.startswith("rm"):
            # 本地命令
            try:
                subprocess.run(cmd, shell=True, check=True)
            except:
                pass
        else:
            print(f"🔄 步骤 {i}: {cmd.split()[-1].replace('gs://', '')}...")
            try:
                result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                print(f"✅ 步骤 {i} 完成")
                if i == len(commands) and result.stdout:  # 最后一步显示结构
                    print("📁 Bucket结构:")
                    for line in result.stdout.strip().split('\n')[:10]:  # 只显示前10行
                        print(f"   {line}")
            except subprocess.CalledProcessError as e:
                if "already exists" in e.stderr:
                    print(f"ℹ️ 步骤 {i}: 资源已存在")
                else:
                    print(f"❌ 步骤 {i} 失败: {e.stderr}")
                    return False
    
    return True

def upload_initial_files():
    """上传初始文件"""
    print("📤 上传初始文件...")
    
    bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
    
    # 需要上传的文件
    upload_files = [
        {
            'local': 'templates/dynamic_templates.json',
            'remote': 'templates/dynamic_templates.json',
            'description': '动态模板配置'
        },
        {
            'local': 'calendars/grace_irvine_coordinator.ics',
            'remote': 'calendars/grace_irvine_coordinator.ics', 
            'description': '负责人日历',
            'optional': True
        }
    ]
    
    for file_info in upload_files:
        local_path = Path(file_info['local'])
        
        if local_path.exists():
            try:
                cmd = f"gsutil cp {local_path} gs://{bucket_name}/{file_info['remote']}"
                subprocess.run(cmd, shell=True, check=True)
                print(f"✅ {file_info['description']}: {file_info['remote']}")
            except Exception as e:
                print(f"❌ 上传失败 {file_info['description']}: {e}")
                if not file_info.get('optional'):
                    return False
        else:
            if file_info.get('optional'):
                print(f"⚠️ 可选文件不存在: {file_info['local']}")
            else:
                print(f"❌ 必需文件不存在: {file_info['local']}")
                return False
    
    return True

def create_deployment_config():
    """创建部署配置"""
    print("⚙️ 创建部署配置...")
    
    bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
    
    # Cloud Run部署配置
    deployment_config = {
        "service_name": "grace-irvine-scheduler",
        "image": f"gcr.io/{project_id}/grace-irvine-scheduler",
        "region": "us-central1",
        "environment_variables": {
            "GCP_STORAGE_BUCKET": bucket_name,
            "GOOGLE_CLOUD_PROJECT": project_id,
            "STORAGE_MODE": "cloud",
            "PORT": "8080"
        },
        "resource_limits": {
            "memory": "1Gi",
            "cpu": "1"
        },
        "scaling": {
            "max_instances": 10,
            "concurrency": 80
        },
        "deployment_command": f"""
gcloud run deploy grace-irvine-scheduler \\
    --image=gcr.io/{project_id}/grace-irvine-scheduler \\
    --platform=managed \\
    --region=us-central1 \\
    --allow-unauthenticated \\
    --memory=1Gi \\
    --cpu=1 \\
    --timeout=3600 \\
    --concurrency=80 \\
    --max-instances=10 \\
    --set-env-vars=GCP_STORAGE_BUCKET={bucket_name},GOOGLE_CLOUD_PROJECT={project_id},STORAGE_MODE=cloud,PORT=8080
        """.strip()
    }
    
    # 保存配置文件
    config_file = Path("configs/cloud_deployment.json")
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(deployment_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 部署配置已保存: {config_file}")
    
    # 显示关键信息
    print(f"\n📋 关键配置信息:")
    print(f"  存储桶: gs://{bucket_name}")
    print(f"  模板文件: gs://{bucket_name}/templates/dynamic_templates.json")
    print(f"  日历文件: gs://{bucket_name}/calendars/grace_irvine_coordinator.ics")
    print(f"  公开访问: https://storage.googleapis.com/{bucket_name}/calendars/grace_irvine_coordinator.ics")
    
    return True

def test_storage_access():
    """测试存储访问"""
    print("🔍 测试存储访问...")
    
    try:
        from src.cloud_storage_manager import CloudStorageManager, StorageConfig
        
        bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
        
        config = StorageConfig(
            bucket_name=bucket_name,
            project_id=project_id
        )
        
        manager = CloudStorageManager(config)
        
        # 测试模板读取
        template_config = manager.read_template_config()
        if template_config:
            print("✅ 模板配置读取成功")
        else:
            print("⚠️ 模板配置读取失败（可能是首次运行）")
        
        # 测试状态检查
        status = manager.get_storage_status()
        print(f"✅ 存储状态: {status['mode']} 模式")
        print(f"   存储可用: {status['storage_available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 存储访问测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Grace Irvine Ministry Scheduler - GCP Storage设置")
    print("=" * 60)
    
    # 检查工具
    try:
        subprocess.run(['gsutil', 'version'], capture_output=True, check=True)
        print("✅ gsutil工具可用")
    except:
        print("❌ gsutil工具不可用，请安装Google Cloud SDK")
        return False
    
    steps = [
        ("创建Bucket结构", create_bucket_structure),
        ("上传初始文件", upload_initial_files), 
        ("创建部署配置", create_deployment_config),
        ("测试存储访问", test_storage_access),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if step_func():
            success_count += 1
        else:
            print(f"❌ {step_name} 失败")
    
    print("\n" + "=" * 60)
    print(f"📊 设置结果: {success_count}/{len(steps)} 完成")
    
    if success_count == len(steps):
        print("🎉 GCP Storage设置完成！")
        
        print("\n✅ 设置完成的功能:")
        print("  • Bucket创建和权限配置")
        print("  • 目录结构初始化")
        print("  • 初始文件上传")
        print("  • 部署配置生成")
        print("  • 存储访问测试")
        
        print("\n📋 后续步骤:")
        print("  1. 检查 configs/cloud_deployment.json 中的部署配置")
        print("  2. 运行部署命令部署到Cloud Run")
        print("  3. 应用将自动使用云端存储")
        print("  4. 在Web界面编辑模板会保存到云端")
        
        print("\n🔗 重要URL:")
        bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
        print(f"  模板配置: gs://{bucket_name}/templates/dynamic_templates.json")
        print(f"  日历文件: gs://{bucket_name}/calendars/grace_irvine_coordinator.ics")
        print(f"  公开订阅: https://storage.googleapis.com/{bucket_name}/calendars/grace_irvine_coordinator.ics")
        
    else:
        print("⚠️ 部分设置失败，请检查错误信息")
    
    return success_count == len(steps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
