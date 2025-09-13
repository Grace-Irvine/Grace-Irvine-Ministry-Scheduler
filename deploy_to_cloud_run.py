#!/usr/bin/env python3
"""
部署到Cloud Run
Deploy to Cloud Run

使用新的统一架构和云端存储部署应用
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
        return None

def main():
    """主部署函数"""
    print("🚀 Grace Irvine Ministry Scheduler - Cloud Run 部署")
    print("=" * 60)
    
    # 配置变量
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "ai-for-god")
    REGION = "us-central1"
    SERVICE_NAME = "grace-irvine-scheduler"
    STORAGE_BUCKET = os.getenv("GCP_STORAGE_BUCKET", "grace-irvine-ministry-scheduler")
    IMAGE_NAME = f"gcr.io/{PROJECT_ID}/{SERVICE_NAME}"
    
    print(f"📋 部署配置:")
    print(f"   项目ID: {PROJECT_ID}")
    print(f"   区域: {REGION}")
    print(f"   服务名称: {SERVICE_NAME}")
    print(f"   存储桶: {STORAGE_BUCKET}")
    print(f"   镜像名称: {IMAGE_NAME}")
    print()
    
    # 1. 设置项目
    if not run_command(f"gcloud config set project {PROJECT_ID}", "设置Google Cloud项目"):
        sys.exit(1)
    
    # 2. 启用必需的API
    print("🔧 启用必需的API服务...")
    apis = [
        "cloudbuild.googleapis.com",
        "run.googleapis.com", 
        "containerregistry.googleapis.com",
        "storage.googleapis.com"
    ]
    
    for api in apis:
        if not run_command(f"gcloud services enable {api}", f"启用 {api}"):
            sys.exit(1)
    
    # 3. 配置Docker认证
    if not run_command("gcloud auth configure-docker", "配置Docker认证"):
        sys.exit(1)
    
    # 4. 构建Docker镜像
    print("🏗️ 构建Docker镜像...")
    if not run_command(f"gcloud builds submit --tag {IMAGE_NAME} .", "构建Docker镜像"):
        sys.exit(1)
    
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
        --port=8080 \
        --set-env-vars=GCP_STORAGE_BUCKET={STORAGE_BUCKET},GOOGLE_CLOUD_PROJECT={PROJECT_ID},STORAGE_MODE=cloud,PORT=8080,API_PORT=8000,SCHEDULER_AUTH_TOKEN=grace-irvine-scheduler-2025
    """.replace('\n    ', ' \\\n    ')
    
    service_url = run_command(deploy_command, "部署Cloud Run服务")
    if not service_url:
        sys.exit(1)
    
    # 6. 获取服务URL
    print("🔗 获取服务URL...")
    service_url = run_command(
        f"gcloud run services describe {SERVICE_NAME} --region={REGION} --format='value(status.url)'",
        "获取Cloud Run服务URL"
    )
    
    if not service_url:
        sys.exit(1)
    
    print()
    print("🎉 部署完成！")
    print("=" * 60)
    print(f"🌐 应用URL: {service_url}")
    print(f"📅 负责人日历订阅: https://storage.googleapis.com/{STORAGE_BUCKET}/calendars/grace_irvine_coordinator.ics")
    print(f"📊 系统状态API: {service_url}/api/status")
    print()
    
    print("📱 主要功能:")
    print("  • 📊 数据概览: 查看排程数据和统计")
    print("  • 📝 模板生成: 生成微信群通知模板（含经文分享）")
    print("  • 🛠️ 模板编辑: 在线编辑模板（保存到云端）")
    print("  • 📖 经文管理: 管理周三通知经文分享内容")
    print("  • 📅 日历管理: ICS文件生成和订阅")
    print("  • ⚙️ 系统设置: 配置管理和状态监控")
    print()
    
    print("🔧 部署后操作:")
    print("1. 访问应用URL验证部署成功")
    print("2. 在'📖 经文管理'中添加和管理经文内容")
    print("3. 在'🛠️ 模板编辑器'中编辑模板")
    print("4. 点击'保存到云端'将配置保存到GCP Storage")
    print("5. 在'📅 日历管理'中生成日历文件")
    print("6. 提供日历订阅URL给用户")
    print()
    
    print("🛠️ 管理命令:")
    print(f"   查看服务: gcloud run services describe {SERVICE_NAME} --region={REGION}")
    print(f"   查看日志: gcloud run services logs read {SERVICE_NAME} --region={REGION}")
    print(f"   更新服务: gcloud run services update {SERVICE_NAME} --region={REGION}")
    print(f"   删除服务: gcloud run services delete {SERVICE_NAME} --region={REGION}")

if __name__ == "__main__":
    main()
