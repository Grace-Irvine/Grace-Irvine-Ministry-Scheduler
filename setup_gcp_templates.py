#!/usr/bin/env python3
"""
GCP模板存储设置脚本
GCP Template Storage Setup Script

用于在GCP环境中设置模板存储
"""

import os
import json
import subprocess
from pathlib import Path

def setup_gcp_storage_bucket():
    """设置GCP Storage Bucket"""
    print("🚀 设置GCP Storage Bucket...")
    
    # 配置变量
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
    BUCKET_NAME = os.getenv('GCP_TEMPLATE_BUCKET', 'grace-irvine-templates')
    REGION = os.getenv('CLOUD_RUN_REGION', 'us-central1')
    
    print(f"📋 配置信息:")
    print(f"  项目ID: {PROJECT_ID}")
    print(f"  Bucket名称: {BUCKET_NAME}")
    print(f"  区域: {REGION}")
    print()
    
    commands = [
        # 1. 创建Bucket
        f"gsutil mb -p {PROJECT_ID} -c STANDARD -l {REGION} gs://{BUCKET_NAME}",
        
        # 2. 设置Bucket权限（允许服务读取）
        f"gsutil iam ch serviceAccount:{PROJECT_ID}@appspot.gserviceaccount.com:objectAdmin gs://{BUCKET_NAME}",
        
        # 3. 上传初始模板文件
        f"gsutil cp templates/dynamic_templates.json gs://{BUCKET_NAME}/templates/",
        
        # 4. 验证上传
        f"gsutil ls gs://{BUCKET_NAME}/templates/"
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"🔄 步骤 {i}: {cmd.split()[1]} ...")
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ 步骤 {i} 完成")
            if result.stdout.strip():
                print(f"   输出: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 步骤 {i} 失败: {e}")
            print(f"   错误: {e.stderr}")
            return False
    
    print("\n✅ GCP Storage Bucket设置完成！")
    return True

def create_cloud_run_env_config():
    """创建Cloud Run环境变量配置"""
    print("📝 创建Cloud Run环境变量配置...")
    
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
    BUCKET_NAME = os.getenv('GCP_TEMPLATE_BUCKET', 'grace-irvine-templates')
    
    env_config = {
        "env_vars": {
            "GCP_TEMPLATE_BUCKET": BUCKET_NAME,
            "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
            "TEMPLATE_STORAGE_MODE": "cloud"
        },
        "deployment_command": f"""
gcloud run deploy grace-irvine-scheduler \\
    --image=gcr.io/{PROJECT_ID}/grace-irvine-scheduler \\
    --platform=managed \\
    --region=us-central1 \\
    --allow-unauthenticated \\
    --memory=1Gi \\
    --set-env-vars=GCP_TEMPLATE_BUCKET={BUCKET_NAME},GOOGLE_CLOUD_PROJECT={PROJECT_ID},TEMPLATE_STORAGE_MODE=cloud
        """.strip()
    }
    
    config_file = Path("configs/cloud_run_template_env.json")
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(env_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 环境变量配置已保存到: {config_file}")
    print("\n📋 部署命令:")
    print(env_config["deployment_command"])
    
    return True

def verify_template_access():
    """验证模板访问"""
    print("🔍 验证模板访问...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        
        # 测试本地模式
        print("📍 测试本地模式...")
        local_manager = DynamicTemplateManager()
        if local_manager.templates_data:
            print("✅ 本地模板加载成功")
        else:
            print("❌ 本地模板加载失败")
            return False
        
        # 测试云端模式（如果配置了）
        bucket_name = os.getenv('GCP_TEMPLATE_BUCKET')
        if bucket_name:
            print(f"📍 测试云端模式 (Bucket: {bucket_name})...")
            try:
                cloud_manager = DynamicTemplateManager(gcp_bucket_name=bucket_name)
                if cloud_manager.templates_data:
                    print("✅ 云端模板访问成功")
                else:
                    print("⚠️ 云端模板访问失败，但不影响本地使用")
            except Exception as e:
                print(f"⚠️ 云端模板测试失败: {e}")
                print("💡 这在本地环境是正常的")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板访问验证失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 Grace Irvine Ministry Scheduler - GCP模板存储设置")
    print("=" * 60)
    
    # 检查是否在GCP环境
    if 'K_SERVICE' in os.environ:
        print("✅ 检测到Cloud Run环境")
    else:
        print("ℹ️ 本地开发环境")
    
    # 检查必要的工具
    try:
        subprocess.run(['gsutil', 'version'], capture_output=True, check=True)
        print("✅ gsutil工具可用")
    except:
        print("❌ gsutil工具不可用，请安装Google Cloud SDK")
        return False
    
    steps = [
        ("验证模板访问", verify_template_access),
        ("设置GCP Storage", setup_gcp_storage_bucket),
        ("创建环境配置", create_cloud_run_env_config),
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
        print("🎉 GCP模板存储设置完成！")
        print("\n📋 后续步骤:")
        print("1. 使用configs/cloud_run_template_env.json中的命令部署")
        print("2. 在Web界面的'🛠️ 模板编辑器'中编辑模板")
        print("3. 模板会自动保存到GCP Storage")
        
    else:
        print("⚠️ 部分设置失败，请检查错误信息")
    
    return success_count == len(steps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
