#!/usr/bin/env python3
"""
调试Cloud Run中的日历文件生成情况
Debug calendar file generation in Cloud Run
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    print("=" * 50)
    
    # 检查是否在Cloud Run中
    if 'K_SERVICE' in os.environ:
        print("✅ 运行在Cloud Run环境中")
        print(f"   服务名称: {os.getenv('K_SERVICE')}")
        print(f"   修订版本: {os.getenv('K_REVISION', '未知')}")
        print(f"   配置: {os.getenv('K_CONFIGURATION', '未知')}")
    else:
        print("ℹ️ 运行在本地环境中")
    
    # 检查工作目录
    print(f"📁 当前工作目录: {os.getcwd()}")
    
    # 检查Python路径
    print(f"🐍 Python路径: {sys.executable}")
    
    # 检查环境变量
    env_vars = [
        'GOOGLE_SPREADSHEET_ID',
        'STREAMLIT_SERVER_PORT',
        'STREAMLIT_SERVER_ADDRESS',
        'PYTHONPATH'
    ]
    
    print("\n🔧 环境变量:")
    for var in env_vars:
        value = os.getenv(var, '未设置')
        print(f"   {var}: {value}")

def check_calendar_directory():
    """检查日历目录"""
    print("\n📁 检查日历目录...")
    print("=" * 50)
    
    calendar_dir = Path("calendars")
    
    if calendar_dir.exists():
        print(f"✅ 日历目录存在: {calendar_dir.absolute()}")
        
        # 列出所有ICS文件
        ics_files = list(calendar_dir.glob("*.ics"))
        if ics_files:
            print(f"📄 找到 {len(ics_files)} 个ICS文件:")
            
            for ics_file in ics_files:
                try:
                    stat = ics_file.stat()
                    with open(ics_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    event_count = content.count('BEGIN:VEVENT')
                    size_kb = stat.st_size / 1024
                    last_modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    print(f"   📄 {ics_file.name}:")
                    print(f"      大小: {size_kb:.1f} KB")
                    print(f"      事件数: {event_count}")
                    print(f"      修改时间: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # 显示文件内容的前几行
                    lines = content.split('\n')[:10]
                    print(f"      内容预览:")
                    for i, line in enumerate(lines):
                        print(f"        {i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
                    print()
                    
                except Exception as e:
                    print(f"   ❌ {ics_file.name}: 读取失败 - {e}")
        else:
            print("❌ 未找到ICS文件")
    else:
        print(f"❌ 日历目录不存在: {calendar_dir.absolute()}")
        
        # 尝试创建目录
        try:
            calendar_dir.mkdir(exist_ok=True)
            print(f"✅ 已创建日历目录: {calendar_dir.absolute()}")
        except Exception as e:
            print(f"❌ 创建日历目录失败: {e}")

def generate_test_calendar():
    """生成测试日历文件"""
    print("\n🔄 生成测试日历文件...")
    print("=" * 50)
    
    try:
        calendar_dir = Path("calendars")
        calendar_dir.mkdir(exist_ok=True)
        
        # 生成简单的测试日历
        test_ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Grace Irvine Ministry Scheduler//Test Calendar//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Grace Irvine 测试日历
X-WR-CALDESC:测试用日历文件（调试生成）
X-WR-TIMEZONE:America/Los_Angeles
X-WR-CALDESC:生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
BEGIN:VEVENT
UID:test_event_{datetime.now().strftime('%Y%m%d_%H%M%S')}@graceirvine.org
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%S')}
DTSTART:{datetime.now().strftime('%Y%m%dT%H%M%S')}
DTEND:{datetime.now().strftime('%Y%m%dT%H%M%S')}
SUMMARY:测试事件
DESCRIPTION:这是一个测试事件，用于验证日历文件生成功能
LOCATION:Grace Irvine 教会
END:VEVENT
END:VCALENDAR"""
        
        # 保存测试文件
        test_files = [
            "grace_irvine_coordinator.ics",
            "grace_irvine_workers.ics",
            "test_calendar.ics"
        ]
        
        for filename in test_files:
            file_path = calendar_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(test_ics_content)
            print(f"✅ 已生成测试文件: {file_path}")
        
        print(f"✅ 成功生成 {len(test_files)} 个测试日历文件")
        
    except Exception as e:
        print(f"❌ 生成测试日历失败: {e}")

def test_file_access():
    """测试文件访问"""
    print("\n🔍 测试文件访问...")
    print("=" * 50)
    
    calendar_dir = Path("calendars")
    test_files = ["grace_irvine_coordinator.ics", "grace_irvine_workers.ics"]
    
    for filename in test_files:
        file_path = calendar_dir / filename
        
        if file_path.exists():
            try:
                # 测试读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"✅ {filename}: 可以读取 ({len(content)} 字符)")
                
                # 验证ICS格式
                if content.startswith('BEGIN:VCALENDAR') and content.endswith('END:VCALENDAR'):
                    print(f"   ✅ ICS格式正确")
                else:
                    print(f"   ❌ ICS格式可能有问题")
                
                # 检查事件数量
                event_count = content.count('BEGIN:VEVENT')
                print(f"   📊 包含 {event_count} 个事件")
                
            except Exception as e:
                print(f"❌ {filename}: 读取失败 - {e}")
        else:
            print(f"❌ {filename}: 文件不存在")

def check_permissions():
    """检查文件权限"""
    print("\n🔐 检查文件权限...")
    print("=" * 50)
    
    calendar_dir = Path("calendars")
    
    try:
        # 检查目录权限
        if calendar_dir.exists():
            print(f"✅ 目录存在且可访问: {calendar_dir.absolute()}")
            
            # 尝试创建测试文件
            test_file = calendar_dir / "permission_test.txt"
            test_content = f"Permission test at {datetime.now()}"
            
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            print("✅ 具有写权限")
            
            # 清理测试文件
            test_file.unlink()
            print("✅ 具有删除权限")
            
        else:
            print(f"❌ 目录不存在: {calendar_dir.absolute()}")
            
    except Exception as e:
        print(f"❌ 权限检查失败: {e}")

def generate_debug_report():
    """生成调试报告"""
    print("\n📋 生成调试报告...")
    print("=" * 50)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'is_cloud_run': 'K_SERVICE' in os.environ,
            'working_directory': os.getcwd(),
            'python_path': sys.executable
        },
        'calendar_directory': {},
        'files': {}
    }
    
    # 检查日历目录
    calendar_dir = Path("calendars")
    if calendar_dir.exists():
        report['calendar_directory'] = {
            'exists': True,
            'path': str(calendar_dir.absolute()),
            'file_count': len(list(calendar_dir.glob("*.ics")))
        }
        
        # 检查文件详情
        for ics_file in calendar_dir.glob("*.ics"):
            try:
                stat = ics_file.stat()
                with open(ics_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                report['files'][ics_file.name] = {
                    'size_bytes': stat.st_size,
                    'size_kb': round(stat.st_size / 1024, 1),
                    'events': content.count('BEGIN:VEVENT'),
                    'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'valid_ics': content.startswith('BEGIN:VCALENDAR') and content.endswith('END:VCALENDAR')
                }
            except Exception as e:
                report['files'][ics_file.name] = {'error': str(e)}
    else:
        report['calendar_directory'] = {
            'exists': False,
            'path': str(calendar_dir.absolute())
        }
    
    # 保存报告
    try:
        report_file = Path("debug_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ 调试报告已保存: {report_file.absolute()}")
    except Exception as e:
        print(f"❌ 保存调试报告失败: {e}")
    
    # 打印报告
    print("\n📊 调试报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

def main():
    """主函数"""
    print("🚀 Grace Irvine 日历文件调试工具")
    print("=" * 60)
    
    # 检查环境
    check_environment()
    
    # 检查日历目录
    check_calendar_directory()
    
    # 检查权限
    check_permissions()
    
    # 生成测试文件
    generate_test_calendar()
    
    # 测试文件访问
    test_file_access()
    
    # 生成调试报告
    generate_debug_report()
    
    print("\n🎯 调试完成!")
    print("=" * 60)
    print("📋 建议检查:")
    print("1. 日历目录是否存在且有正确权限")
    print("2. ICS文件是否已生成且格式正确")
    print("3. 在Streamlit应用中手动生成日历文件")
    print("4. 检查Cloud Run日志中的错误信息")

if __name__ == "__main__":
    main()
