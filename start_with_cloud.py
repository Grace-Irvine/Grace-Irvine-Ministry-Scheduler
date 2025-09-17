#!/usr/bin/env python3
"""
带云端存储的应用启动脚本
Start Application with Cloud Storage

自动配置云端存储环境并启动Streamlit应用
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_cloud_environment():
    """设置云端环境变量"""
    # 设置云端存储环境变量
    os.environ['STORAGE_MODE'] = 'cloud'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'ai-for-god'
    os.environ['GCP_STORAGE_BUCKET'] = 'grace-irvine-ministry-scheduler'
    
    # 设置服务账号认证
    service_account_path = Path(__file__).parent / "configs" / "service_account.json"
    if service_account_path.exists():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)
        print(f"✅ 云端模式已启用，使用服务账号: {service_account_path}")
    else:
        print(f"⚠️ 服务账号文件不存在: {service_account_path}")
        print("💡 将尝试使用默认凭据...")
    
    print("🔧 云端存储环境变量:")
    print(f"   STORAGE_MODE={os.getenv('STORAGE_MODE')}")
    print(f"   GOOGLE_CLOUD_PROJECT={os.getenv('GOOGLE_CLOUD_PROJECT')}")
    print(f"   GCP_STORAGE_BUCKET={os.getenv('GCP_STORAGE_BUCKET')}")

def verify_cloud_connection():
    """验证云端连接"""
    print("\n☁️ 验证云端存储连接...")
    
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket('grace-irvine-ministry-scheduler')
        
        if bucket.exists():
            print("✅ 云端存储连接正常")
            
            # 快速检查ICS文件
            ics_count = 0
            for blob in bucket.list_blobs(prefix="calendars/"):
                if blob.name.endswith('.ics'):
                    ics_count += 1
            
            print(f"📄 发现 {ics_count} 个云端ICS文件")
            return True
        else:
            print("❌ Bucket不存在")
            return False
    except Exception as e:
        print(f"⚠️ 云端连接检查失败: {e}")
        print("💡 应用仍可启动，但可能只能访问本地文件")
        return False

def start_streamlit():
    """启动Streamlit应用"""
    print("\n🚀 启动Streamlit应用...")
    print("💡 ICS查看器现在支持云端文件查看")
    print("=" * 50)
    
    try:
        # 使用subprocess启动streamlit，保持环境变量
        cmd = [sys.executable, "-m", "streamlit", "run", "app_unified.py", "--server.port=8501"]
        subprocess.run(cmd, env=os.environ.copy())
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    print("🌟 Grace Irvine Ministry Scheduler (云端模式)")
    print("=" * 60)
    
    # 1. 设置云端环境
    setup_cloud_environment()
    
    # 2. 验证连接
    verify_cloud_connection()
    
    # 3. 启动应用
    start_streamlit()

if __name__ == "__main__":
    main()
