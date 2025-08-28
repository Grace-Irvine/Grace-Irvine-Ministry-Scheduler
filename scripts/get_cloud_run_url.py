#!/usr/bin/env python3
"""
获取Cloud Run服务URL的辅助脚本
帮助用户获取正确的ICS订阅URL
"""

import subprocess
import sys
import os

def get_cloud_run_url(service_name="grace-irvine-scheduler", region="us-central1"):
    """获取Cloud Run服务URL"""
    try:
        # 使用gcloud命令获取服务URL
        cmd = [
            "gcloud", "run", "services", "describe", 
            service_name, 
            "--region", region,
            "--format", "value(status.url)"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        
        if url:
            return url
        else:
            print(f"❌ 未找到服务 {service_name} 的URL")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 获取Cloud Run URL失败: {e}")
        print(f"请确保服务 {service_name} 已部署到区域 {region}")
        return None
    except FileNotFoundError:
        print("❌ 未找到 gcloud CLI，请先安装 Google Cloud CLI")
        return None

def main():
    """主函数"""
    print("🔗 Grace Irvine Cloud Run URL 获取工具")
    print("=" * 50)
    
    # 获取Cloud Run URL
    cloud_run_url = get_cloud_run_url()
    
    if cloud_run_url:
        print(f"✅ Cloud Run 服务URL: {cloud_run_url}")
        print()
        
        # 显示ICS订阅URL
        print("📅 ICS日历订阅URL:")
        print("=" * 50)
        coordinator_url = f"{cloud_run_url}/calendars/grace_irvine_coordinator.ics"
        workers_url = f"{cloud_run_url}/calendars/grace_irvine_workers.ics"
        
        print(f"负责人日历: {coordinator_url}")
        print(f"同工日历: {workers_url}")
        print()
        
        # 显示使用方法
        print("📱 订阅方法:")
        print("=" * 50)
        print("1. **Google Calendar**:")
        print("   - 左侧点击'+'")
        print("   - 选择'从URL添加'")
        print("   - 粘贴上面的URL")
        print("   - 点击'添加日历'")
        print()
        print("2. **Apple Calendar**:")
        print("   - 打开Calendar应用")
        print("   - '文件' → '新建日历订阅'")
        print("   - 输入上面的URL")
        print("   - 点击'订阅'")
        print()
        print("3. **Outlook**:")
        print("   - 打开Outlook")
        print("   - '日历' → '添加日历'")
        print("   - '从Internet订阅'")
        print("   - 输入上面的URL")
        print()
        print("⚠️  重要提醒:")
        print("- 请使用'订阅URL'而不是'导入文件'")
        print("- 订阅后日历会自动更新")
        print("- 无需手动重新导入")
        
    else:
        print("❌ 无法获取Cloud Run URL")
        print()
        print("请检查:")
        print("1. 是否已部署Cloud Run服务")
        print("2. 服务名称是否正确 (grace-irvine-scheduler)")
        print("3. 区域是否正确 (us-central1)")
        print("4. 是否已登录gcloud CLI")
        print()
        print("手动检查命令:")
        print(f"gcloud run services describe grace-irvine-scheduler --region=us-central1")

if __name__ == "__main__":
    main()
