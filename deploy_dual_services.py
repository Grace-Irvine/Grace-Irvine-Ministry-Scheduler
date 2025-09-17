#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 双服务部署脚本
部署两个独立的Cloud Run服务：UI服务和API服务
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def run_command(cmd, description):
    """运行命令并处理错误"""
    print(f"{chr(10)}🔧 {description}")
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} 成功")
        if result.stdout:
            print(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败")
        print(f"错误: {e.stderr}")
        return False

def main():
    """主部署函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 双服务部署")
    print("=" * 60)
    
    # 配置变量
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "ai-for-god")
    REGION = os.getenv("REGION", "us-central1")
    STORAGE_BUCKET = os.getenv("GCP_STORAGE_BUCKET", "grace-irvine-ministry-scheduler")
    
    print(f"项目ID: {PROJECT_ID}")
    print(f"区域: {REGION}")
    print(f"存储桶: {STORAGE_BUCKET}")
    
    # 1. 启用必要的API
    apis = [
        "cloudbuild.googleapis.com",
        "run.googleapis.com",
        "containerregistry.googleapis.com",
        "storage.googleapis.com",
        "cloudscheduler.googleapis.com"
    ]
    
    for api in apis:
        if not run_command(
            ["gcloud", "services", "enable", api, f"--project={PROJECT_ID}"],
            f"启用 {api}"
        ):
            return False
    
    # 2. 配置Docker认证
    if not run_command(
        ["gcloud", "auth", "configure-docker"],
        "配置Docker认证"
    ):
        return False
    
    # 3. 构建API服务镜像
    api_image = f"gcr.io/{PROJECT_ID}/grace-irvine-api"
    if not run_command(
        ["gcloud", "builds", "submit", "--config", "cloudbuild-api.yaml", "."],
        "构建API服务镜像"
    ):
        return False
    
    # 4. 构建UI服务镜像
    ui_image = f"gcr.io/{PROJECT_ID}/grace-irvine-ui"
    if not run_command(
        ["gcloud", "builds", "submit", "--config", "cloudbuild-ui.yaml", "."],
        "构建UI服务镜像"
    ):
        return False
    
    # 5. 部署API服务
    api_service_name = "grace-irvine-api"
    api_env_vars = [
        f"GCP_STORAGE_BUCKET={STORAGE_BUCKET}",
        f"GOOGLE_CLOUD_PROJECT={PROJECT_ID}",
        "STORAGE_MODE=cloud",
        "SCHEDULER_AUTH_TOKEN=grace-irvine-scheduler-2025"
    ]
    
    api_deploy_cmd = [
        "gcloud", "run", "deploy", api_service_name,
        f"--image={api_image}",
        "--platform=managed",
        f"--region={REGION}",
        "--allow-unauthenticated",
        "--memory=1Gi",
        "--cpu=1",
        "--timeout=3600",
        "--concurrency=80",
        "--max-instances=10",
        "--port=8080",
        f"--set-env-vars={','.join(api_env_vars)}"
    ]
    
    if not run_command(api_deploy_cmd, "部署API服务"):
        return False
    
    # 6. 部署UI服务
    ui_service_name = "grace-irvine-ui"
    ui_env_vars = [
        f"GCP_STORAGE_BUCKET={STORAGE_BUCKET}",
        f"GOOGLE_CLOUD_PROJECT={PROJECT_ID}",
        "STORAGE_MODE=cloud"
    ]
    
    ui_deploy_cmd = [
        "gcloud", "run", "deploy", ui_service_name,
        f"--image={ui_image}",
        "--platform=managed",
        f"--region={REGION}",
        "--allow-unauthenticated",
        "--memory=1Gi",
        "--cpu=1",
        "--timeout=3600",
        "--concurrency=80",
        "--max-instances=10",
        "--port=8080",
        f"--set-env-vars={','.join(ui_env_vars)}"
    ]
    
    if not run_command(ui_deploy_cmd, "部署UI服务"):
        return False
    
    # 7. 获取服务URL
    try:
        # 获取API服务URL
        api_result = subprocess.run([
            "gcloud", "run", "services", "describe", api_service_name,
            f"--region={REGION}",
            f"--project={PROJECT_ID}",
            "--format=value(status.url)"
        ], capture_output=True, text=True, check=True)
        api_url = api_result.stdout.strip()
        
        # 获取UI服务URL
        ui_result = subprocess.run([
            "gcloud", "run", "services", "describe", ui_service_name,
            f"--region={REGION}",
            f"--project={PROJECT_ID}",
            "--format=value(status.url)"
        ], capture_output=True, text=True, check=True)
        ui_url = ui_result.stdout.strip()
        
        print("\n🎉 部署完成！")
        print("=" * 60)
        print(f"📱 UI服务URL:  {ui_url}")
        print(f"🔌 API服务URL: {api_url}")
        print(f"📋 API文档:    {api_url}/docs")
        print(f"💚 健康检查:   {api_url}/health")
        
        # 8. 更新Cloud Scheduler配置
        print(f"\n🕐 更新Cloud Scheduler配置...")
        scheduler_script = "./cloud_scheduler_setup.sh"
        if os.path.exists(scheduler_script):
            # 设置环境变量供脚本使用
            env = os.environ.copy()
            env["API_SERVICE_URL"] = api_url
            
            result = subprocess.run([scheduler_script], env=env, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Cloud Scheduler配置成功")
            else:
                print(f"⚠️ Cloud Scheduler配置失败: {result.stderr}")
        
        # 保存配置信息
        config = {
            "deployment_time": datetime.now().isoformat(),
            "project_id": PROJECT_ID,
            "region": REGION,
            "storage_bucket": STORAGE_BUCKET,
            "services": {
                "ui": {
                    "name": ui_service_name,
                    "url": ui_url,
                    "image": ui_image
                },
                "api": {
                    "name": api_service_name,
                    "url": api_url,
                    "image": api_image
                }
            }
        }
        
        with open("deployment_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 部署配置已保存到: deployment_config.json")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 获取服务URL失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
