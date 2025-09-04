#!/usr/bin/env python3
"""
Cloud Run 部署脚本 - 支持静态文件服务
Deploy to Cloud Run with static file serving support
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """运行命令并处理错误"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 完成")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)

def main():
    """主部署函数"""
    print("🚀 Grace Irvine Ministry Scheduler - Cloud Run 部署")
    print("=" * 60)
    
    # 配置变量
    PROJECT_ID = "ai-for-god"
    REGION = "us-central1"
    SERVICE_NAME = "grace-irvine-scheduler"
    IMAGE_NAME = f"gcr.io/{PROJECT_ID}/{SERVICE_NAME}"
    
    print(f"📋 部署配置:")
    print(f"   项目ID: {PROJECT_ID}")
    print(f"   区域: {REGION}")
    print(f"   服务名称: {SERVICE_NAME}")
    print(f"   镜像名称: {IMAGE_NAME}")
    print()
    
    # 1. 设置项目
    run_command(f"gcloud config set project {PROJECT_ID}", "设置Google Cloud项目")
    
    # 2. 启用必需的API
    print("🔧 启用必需的API服务...")
    apis = [
        "cloudbuild.googleapis.com",
        "run.googleapis.com",
        "containerregistry.googleapis.com",
        "cloudfunctions.googleapis.com",
        "cloudscheduler.googleapis.com"
    ]
    
    for api in apis:
        run_command(f"gcloud services enable {api}", f"启用 {api}")
    
    # 3. 配置Docker认证
    run_command("gcloud auth configure-docker", "配置Docker认证")
    
    # 4. 构建Docker镜像
    print("🏗️ 构建Docker镜像...")
    run_command(f"gcloud builds submit --tag {IMAGE_NAME} .", "构建Docker镜像")
    
    # 5. 部署到Cloud Run
    print("☁️ 部署到Cloud Run...")
    deploy_command = f"""
    gcloud run deploy {SERVICE_NAME} \
        --image={IMAGE_NAME} \
        --platform=managed \
        --region={REGION} \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --timeout=3600 \
        --concurrency=80 \
        --max-instances=10 \
        --port=8080
    """
    run_command(deploy_command, "部署Cloud Run服务")
    
    # 6. 获取服务URL
    print("🔗 获取服务URL...")
    service_url = run_command(
        f"gcloud run services describe {SERVICE_NAME} --region={REGION} --format='value(status.url)'",
        "获取Cloud Run服务URL"
    )
    
    print()
    print("🎉 部署完成！")
    print("=" * 60)
    print(f"🌐 FastAPI主服务: {service_url}")
    print(f"📅 负责人日历订阅: {service_url}/calendars/grace_irvine_coordinator.ics")
    print(f"📅 同工日历订阅: {service_url}/calendars/grace_irvine_workers.ics")
    print(f"📊 系统状态API: {service_url}/api/status")
    print(f"❤️ 健康检查: {service_url}/health")
    print(f"🔍 调试信息: {service_url}/debug")
    print()
    
    print("📱 用户订阅指南:")
    print("1. 复制上面的日历订阅URL")
    print("2. 在日历应用中订阅URL（Google Calendar、Apple Calendar、Outlook等）")
    print("3. 日历将自动更新，无需手动操作")
    print()
    
    print("🔧 部署后操作:")
    print("1. 访问主服务URL验证部署成功")
    print("2. 测试日历订阅URL是否可以下载")
    print("3. 在Cloud Run中生成真实日历文件")
    print("4. 提供订阅URL给用户")
    print()
    
    print("🛠️ 管理命令:")
    print(f"   查看服务: gcloud run services describe {SERVICE_NAME} --region={REGION}")
    print(f"   查看日志: gcloud run services logs read {SERVICE_NAME} --region={REGION}")
    print(f"   更新服务: gcloud run services update {SERVICE_NAME} --region={REGION}")
    print(f"   删除服务: gcloud run services delete {SERVICE_NAME} --region={REGION}")
    print()
    
    print("📋 生成日历文件:")
    print(f"   手动生成: curl -X POST {service_url}/api/update-calendars")
    print(f"   检查状态: curl {service_url}/api/status")
    print(f"   调试信息: curl {service_url}/debug")

if __name__ == "__main__":
    main()
