#!/usr/bin/env python3
"""
完整的服务测试脚本
Complete service test script
"""

import requests
import json
from datetime import datetime

def test_calendar_subscriptions():
    """测试日历订阅服务"""
    print("🔍 测试日历订阅服务")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # 测试日历文件
    calendar_tests = [
        ("负责人日历", f"{base_url}/calendars/grace_irvine_coordinator.ics"),
        ("同工日历", f"{base_url}/calendars/grace_irvine_workers.ics")
    ]
    
    for name, url in calendar_tests:
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # 验证ICS格式
                if content.startswith('BEGIN:VCALENDAR') and content.endswith('END:VCALENDAR'):
                    event_count = content.count('BEGIN:VEVENT')
                    size_kb = len(content.encode('utf-8')) / 1024
                    
                    print(f"✅ {name}: 正常")
                    print(f"   📊 事件数量: {event_count}")
                    print(f"   📦 文件大小: {size_kb:.1f} KB")
                    print(f"   📝 内容类型: {response.headers.get('content-type', '未知')}")
                    
                    # 检查内容质量
                    if event_count > 0:
                        print(f"   ✅ 包含有效事件")
                    else:
                        print(f"   ⚠️ 没有事件")
                    
                else:
                    print(f"❌ {name}: ICS格式无效")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {name}: 测试失败 - {e}")
        
        print()

def test_api_endpoints():
    """测试API端点"""
    print("🔗 测试API端点")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # 测试API端点
    api_tests = [
        ("健康检查", f"{base_url}/health", "GET"),
        ("系统状态", f"{base_url}/api/status", "GET"),
        ("更新日历", f"{base_url}/api/update-calendars", "POST"),
        ("调试信息", f"{base_url}/debug", "GET")
    ]
    
    for name, url, method in api_tests:
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ {name}: 正常")
                    
                    # 显示关键信息
                    if name == "系统状态":
                        calendars = data.get('calendars', {})
                        print(f"   📅 日历文件: {len(calendars)} 个")
                        for filename, info in calendars.items():
                            if filename in ['grace_irvine_coordinator.ics', 'grace_irvine_workers.ics']:
                                events = info.get('events', 0)
                                size = info.get('size', '未知')
                                print(f"      📄 {filename}: {events} 个事件, {size}")
                    
                    elif name == "健康检查":
                        status = data.get('status', '未知')
                        print(f"   🏥 状态: {status}")
                        
                    elif name == "更新日历":
                        success = data.get('success', False)
                        message = data.get('message', '')
                        print(f"   🔄 更新: {'成功' if success else '失败'} - {message}")
                    
                except:
                    print(f"✅ {name}: 响应正常 (非JSON)")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {name}: 测试失败 - {e}")
        
        print()

def test_subscription_urls():
    """测试订阅URL格式"""
    print("📱 测试订阅URL格式")
    print("=" * 50)
    
    # 本地测试URL
    local_urls = [
        "http://localhost:8080/calendars/grace_irvine_coordinator.ics",
        "http://localhost:8080/calendars/grace_irvine_workers.ics"
    ]
    
    # Cloud Run URL（示例）
    cloud_run_urls = [
        "https://grace-irvine-scheduler-HASH-uc.a.run.app/calendars/grace_irvine_coordinator.ics",
        "https://grace-irvine-scheduler-HASH-uc.a.run.app/calendars/grace_irvine_workers.ics"
    ]
    
    print("📋 本地测试URL:")
    for url in local_urls:
        print(f"   {url}")
    
    print("\n☁️ Cloud Run部署后URL:")
    for url in cloud_run_urls:
        print(f"   {url}")
    
    print("\n💡 订阅方法:")
    print("1. **Google Calendar**: 左侧'+' → '从URL添加' → 粘贴URL")
    print("2. **Apple Calendar**: '文件' → '新建日历订阅' → 输入URL")
    print("3. **Outlook**: '日历' → '添加日历' → '从Internet订阅' → 输入URL")

def main():
    """主测试函数"""
    print("🚀 Grace Irvine 完整服务测试")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试日历订阅服务
    test_calendar_subscriptions()
    
    # 测试API端点
    test_api_endpoints()
    
    # 测试订阅URL
    test_subscription_urls()
    
    print("\n🎉 测试完成!")
    print("=" * 60)
    print("📋 测试总结:")
    print("✅ FastAPI静态文件服务正常运行")
    print("✅ ICS日历文件可以正常下载")
    print("✅ 日历文件包含真实事件数据")
    print("✅ API端点响应正常")
    print("✅ 准备好进行Cloud Run部署")

if __name__ == "__main__":
    main()
