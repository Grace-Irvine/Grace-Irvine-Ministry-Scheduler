#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 端到端测试
End-to-End Test

完整测试从数据获取到模板生成到ICS文件的整个流程
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_environment_setup():
    """测试环境设置"""
    print("🔧 测试环境设置...")
    
    # 检查必要目录
    required_dirs = ['calendars', 'data', 'logs', 'templates', 'configs', 'src']
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        else:
            print(f"✅ 目录存在: {dir_name}")
    
    if missing_dirs:
        print(f"❌ 缺少目录: {', '.join(missing_dirs)}")
        return False
    
    # 检查配置文件
    config_files = [
        'configs/config.yaml',
        'templates/dynamic_templates.json'
    ]
    
    missing_configs = []
    for config_file in config_files:
        if not Path(config_file).exists():
            missing_configs.append(config_file)
        else:
            print(f"✅ 配置文件存在: {config_file}")
    
    if missing_configs:
        print(f"❌ 缺少配置文件: {', '.join(missing_configs)}")
        return False
    
    # 检查环境变量
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    if spreadsheet_id:
        print(f"✅ GOOGLE_SPREADSHEET_ID 已设置: {spreadsheet_id[:10]}...")
    else:
        print("⚠️ GOOGLE_SPREADSHEET_ID 未设置，将使用默认值")
    
    return True

def test_data_pipeline():
    """测试数据管道"""
    print("📊 测试数据管道...")
    
    try:
        from src.data_cleaner import FocusedDataCleaner
        from src.models import MinistryAssignment
        
        # 1. 数据下载
        print("  1️⃣ 测试数据下载...")
        cleaner = FocusedDataCleaner()
        raw_df = cleaner.download_data()
        
        if raw_df.empty:
            print("❌ 数据下载失败或为空")
            return False
        else:
            print(f"✅ 成功下载 {len(raw_df)} 行原始数据")
        
        # 2. 列提取
        print("  2️⃣ 测试列提取...")
        focused_df = cleaner.extract_focused_columns(raw_df)
        
        if focused_df.empty:
            print("❌ 列提取失败")
            return False
        else:
            print(f"✅ 成功提取 {len(focused_df.columns)} 列数据")
        
        # 3. 数据清洗
        print("  3️⃣ 测试数据清洗...")
        schedules = cleaner.clean_focused_data(focused_df)
        
        if not schedules:
            print("❌ 数据清洗失败或无有效数据")
            return False
        else:
            print(f"✅ 成功清洗出 {len(schedules)} 个有效排程")
        
        # 4. 数据验证
        print("  4️⃣ 测试数据验证...")
        valid_schedules = 0
        for schedule in schedules[:5]:  # 检查前5个
            if isinstance(schedule, MinistryAssignment):
                valid_schedules += 1
        
        if valid_schedules > 0:
            print(f"✅ 数据类型正确，验证了 {valid_schedules} 个排程")
        else:
            print("❌ 数据类型验证失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 数据管道测试失败: {e}")
        return False

def test_template_system():
    """测试模板系统"""
    print("📝 测试模板系统...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        from src.models import MinistryAssignment
        
        # 1. 模板加载
        print("  1️⃣ 测试模板加载...")
        manager = DynamicTemplateManager()
        
        templates = manager.get_all_templates()
        if not templates or 'templates' not in templates:
            print("❌ 模板加载失败")
            return False
        else:
            template_count = len(templates['templates'])
            print(f"✅ 成功加载 {template_count} 个模板")
        
        # 2. 创建测试数据
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        # 3. 周三模板渲染
        print("  2️⃣ 测试周三模板渲染...")
        wed_result = manager.render_weekly_confirmation(test_date, test_schedule)
        
        if "Jimmy" in wed_result and "事工安排提醒" in wed_result:
            print("✅ 周三模板渲染正常")
        else:
            print("❌ 周三模板渲染失败")
            return False
        
        # 4. 周六模板渲染
        print("  3️⃣ 测试周六模板渲染...")
        sat_result = manager.render_saturday_reminder(test_date, test_schedule)
        
        if "Jimmy 9:00到" in sat_result and "主日服事提醒" in sat_result:
            print("✅ 周六模板渲染正常")
        else:
            print("❌ 周六模板渲染失败")
            return False
        
        # 5. 月度模板渲染
        print("  4️⃣ 测试月度模板渲染...")
        monthly_result = manager.render_monthly_overview([test_schedule], test_date.year, test_date.month)
        
        if "事工排班一览" in monthly_result:
            print("✅ 月度模板渲染正常")
        else:
            print("❌ 月度模板渲染失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模板系统测试失败: {e}")
        return False

def test_frontend_integration():
    """测试前端集成"""
    print("🌐 测试前端集成...")
    
    try:
        from app_unified import (
            load_ministry_data, 
            generate_wednesday_template, 
            generate_saturday_template,
            generate_monthly_template
        )
        from src.models import MinistryAssignment
        
        # 1. 数据加载
        print("  1️⃣ 测试前端数据加载...")
        data_result = load_ministry_data()
        
        if not data_result['success']:
            print(f"❌ 前端数据加载失败: {data_result.get('error', '未知错误')}")
            return False
        else:
            schedule_count = len(data_result['schedules'])
            print(f"✅ 前端数据加载成功，{schedule_count} 个排程")
        
        # 2. 前端模板生成
        schedules = data_result['schedules']
        if schedules:
            # 找到一个有安排的排程
            test_schedule = None
            for schedule in schedules:
                if schedule.has_assignments():
                    test_schedule = schedule
                    break
            
            if test_schedule:
                print("  2️⃣ 测试前端模板生成...")
                
                # 测试周三模板
                wed_template = generate_wednesday_template(test_schedule.date, test_schedule)
                if "事工安排提醒" in wed_template:
                    print("✅ 前端周三模板生成正常")
                else:
                    print("❌ 前端周三模板生成失败")
                    return False
                
                # 测试周六模板
                sat_template = generate_saturday_template(test_schedule.date, test_schedule)
                if "主日服事提醒" in sat_template:
                    print("✅ 前端周六模板生成正常")
                else:
                    print("❌ 前端周六模板生成失败")
                    return False
                
                # 测试月度模板
                monthly_template = generate_monthly_template(schedules)
                if "事工排班一览" in monthly_template:
                    print("✅ 前端月度模板生成正常")
                else:
                    print("❌ 前端月度模板生成失败")
                    return False
            else:
                print("⚠️ 未找到有安排的排程，跳过模板生成测试")
        
        return True
        
    except Exception as e:
        print(f"❌ 前端集成测试失败: {e}")
        return False

def test_calendar_generation():
    """测试日历生成"""
    print("📅 测试日历生成...")
    
    try:
        # 1. 清理旧文件
        print("  1️⃣ 清理旧的日历文件...")
        calendar_dir = Path("calendars")
        for ics_file in calendar_dir.glob("*.ics"):
            ics_file.unlink()
            print(f"✅ 删除旧文件: {ics_file.name}")
        
        # 2. 生成新日历
        print("  2️⃣ 生成新的日历文件...")
        result = subprocess.run([
            sys.executable, 'generate_calendars.py'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"❌ 日历生成失败: {result.stderr}")
            return False
        
        print("✅ 日历生成命令执行成功")
        
        # 3. 验证生成的文件
        print("  3️⃣ 验证生成的日历文件...")
        coordinator_ics = calendar_dir / "grace_irvine_coordinator.ics"
        
        if not coordinator_ics.exists():
            print("❌ 负责人日历文件未生成")
            return False
        
        # 检查文件内容
        with open(coordinator_ics, 'r', encoding='utf-8') as f:
            content = f.read()
        
        event_count = content.count("BEGIN:VEVENT")
        if event_count > 0:
            print(f"✅ 负责人日历包含 {event_count} 个事件")
        else:
            print("❌ 负责人日历没有事件")
            return False
        
        # 检查模板内容是否正确
        if "事工安排提醒" in content and "主日服事提醒" in content:
            print("✅ 日历事件包含正确的模板内容")
        else:
            print("❌ 日历事件不包含预期的模板内容")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 日历生成测试失败: {e}")
        return False

def test_ics_parsing():
    """测试ICS解析"""
    print("🔍 测试ICS解析...")
    
    try:
        from app_unified import parse_ics_events, StaticFileServer
        
        # 1. 检查文件服务
        print("  1️⃣ 测试ICS文件服务...")
        content, error = StaticFileServer.serve_calendar_file("grace_irvine_coordinator.ics")
        
        if error:
            print(f"❌ ICS文件服务失败: {error}")
            return False
        else:
            print("✅ ICS文件服务正常")
        
        # 2. 解析事件
        print("  2️⃣ 测试事件解析...")
        events = parse_ics_events(content)
        
        if not events:
            print("❌ 事件解析失败或无事件")
            return False
        else:
            print(f"✅ 成功解析 {len(events)} 个事件")
        
        # 3. 验证事件内容
        print("  3️⃣ 验证事件内容...")
        notification_events = 0
        for event in events:
            description = event.get('description', '')
            if "事工安排提醒" in description or "主日服事提醒" in description:
                notification_events += 1
        
        if notification_events > 0:
            print(f"✅ 找到 {notification_events} 个通知事件")
        else:
            print("❌ 未找到通知事件")
            return False
        
        # 4. 检查细化变量内容
        print("  4️⃣ 检查细化变量内容...")
        sample_event = events[0]
        description = sample_event.get('description', '')
        
        # 检查是否包含具体的人员信息
        if "音控：" in description and "导播/摄影：" in description:
            print("✅ 事件包含细化的角色信息")
        else:
            print("❌ 事件不包含细化的角色信息")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ICS解析测试失败: {e}")
        return False

def test_email_system():
    """测试邮件系统"""
    print("📧 测试邮件系统...")
    
    try:
        from src.email_sender import EmailSender, EmailRecipient
        
        # 1. 邮件发送器初始化
        print("  1️⃣ 测试邮件发送器初始化...")
        email_sender = EmailSender()
        
        if email_sender.config:
            print("✅ 邮件发送器初始化成功")
        else:
            print("❌ 邮件发送器初始化失败")
            return False
        
        # 2. 模板邮件内容生成
        print("  2️⃣ 测试邮件内容生成...")
        from src.dynamic_template_manager import DynamicTemplateManager
        from src.models import MinistryAssignment
        
        manager = DynamicTemplateManager()
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇"
        )
        
        wed_content = manager.render_weekly_confirmation(test_date, test_schedule)
        sat_content = manager.render_saturday_reminder(test_date, test_schedule)
        
        if wed_content and sat_content:
            print("✅ 邮件模板内容生成正常")
        else:
            print("❌ 邮件模板内容生成失败")
            return False
        
        # 3. 邮件配置检查
        print("  3️⃣ 检查邮件配置...")
        sender_email = os.getenv("SENDER_EMAIL")
        if sender_email:
            print(f"✅ 发件人邮箱已配置: {sender_email}")
        else:
            print("⚠️ 发件人邮箱未配置，邮件发送功能可能无法使用")
        
        return True
        
    except Exception as e:
        print(f"❌ 邮件系统测试失败: {e}")
        return False

def test_web_interface():
    """测试Web界面启动"""
    print("🌐 测试Web界面启动...")
    
    try:
        # 检查启动脚本
        print("  1️⃣ 检查启动脚本...")
        start_script = Path("start.py")
        if not start_script.exists():
            print("❌ 启动脚本不存在")
            return False
        else:
            print("✅ 启动脚本存在")
        
        # 检查统一应用
        print("  2️⃣ 检查统一应用...")
        app_unified = Path("app_unified.py")
        if not app_unified.exists():
            print("❌ 统一应用文件不存在")
            return False
        else:
            print("✅ 统一应用文件存在")
        
        # 测试应用导入
        print("  3️⃣ 测试应用导入...")
        try:
            import app_unified
            print("✅ 统一应用导入成功")
        except Exception as e:
            print(f"❌ 统一应用导入失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Web界面测试失败: {e}")
        return False

def test_complete_workflow():
    """测试完整工作流"""
    print("🔄 测试完整工作流...")
    
    try:
        # 1. 数据获取 → 模板生成 → 保存
        print("  1️⃣ 完整工作流: 数据 → 模板 → 保存...")
        
        from src.data_cleaner import FocusedDataCleaner
        from src.dynamic_template_manager import DynamicTemplateManager
        
        # 获取真实数据
        cleaner = FocusedDataCleaner()
        raw_df = cleaner.download_data()
        focused_df = cleaner.extract_focused_columns(raw_df)
        schedules = cleaner.clean_focused_data(focused_df)
        
        if not schedules:
            print("❌ 无法获取排程数据")
            return False
        
        # 找到下周的排程
        today = date.today()
        next_sunday = today + timedelta(days=(6 - today.weekday()) % 7 + 7)
        
        next_week_schedule = None
        for schedule in schedules:
            if schedule.date == next_sunday:
                next_week_schedule = schedule
                break
        
        if next_week_schedule:
            print(f"✅ 找到下周排程: {next_sunday}")
            
            # 生成模板
            manager = DynamicTemplateManager()
            
            wed_template = manager.render_weekly_confirmation(next_sunday, next_week_schedule)
            sat_template = manager.render_saturday_reminder(next_sunday, next_week_schedule)
            
            # 保存模板到文件
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            data_dir = Path("data")
            
            wed_file = data_dir / f"test_wednesday_template_{timestamp}.txt"
            sat_file = data_dir / f"test_saturday_template_{timestamp}.txt"
            
            with open(wed_file, 'w', encoding='utf-8') as f:
                f.write(wed_template)
            
            with open(sat_file, 'w', encoding='utf-8') as f:
                f.write(sat_template)
            
            print(f"✅ 模板已保存到: {wed_file.name}, {sat_file.name}")
            
        else:
            print(f"⚠️ 未找到下周({next_sunday})的排程，使用测试数据")
            
            # 使用测试数据
            from src.models import MinistryAssignment
            test_schedule = MinistryAssignment(
                date=next_sunday,
                audio_tech="Jimmy",
                video_director="靖铮",
                propresenter_play="张宇"
            )
            
            manager = DynamicTemplateManager()
            wed_template = manager.render_weekly_confirmation(next_sunday, test_schedule)
            sat_template = manager.render_saturday_reminder(next_sunday, test_schedule)
            
            if wed_template and sat_template:
                print("✅ 使用测试数据生成模板成功")
            else:
                print("❌ 测试数据模板生成失败")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 完整工作流测试失败: {e}")
        return False

def test_system_health():
    """测试系统健康状态"""
    print("❤️ 测试系统健康状态...")
    
    try:
        from app_unified import StaticFileServer
        
        # 1. 静态文件服务状态
        print("  1️⃣ 检查静态文件服务状态...")
        status = StaticFileServer.get_calendar_status()
        
        if status['status'] == 'healthy':
            print("✅ 静态文件服务健康")
            
            calendars = status.get('calendars', {})
            if calendars:
                print(f"✅ 找到 {len(calendars)} 个日历文件")
                for filename, info in calendars.items():
                    if 'events' in info:
                        print(f"   • {filename}: {info['events']} 个事件")
            else:
                print("⚠️ 未找到日历文件")
        else:
            print(f"❌ 静态文件服务异常: {status.get('error', '未知错误')}")
            return False
        
        # 2. 模板系统状态
        print("  2️⃣ 检查模板系统状态...")
        from src.dynamic_template_manager import DynamicTemplateManager
        
        manager = DynamicTemplateManager()
        if manager.templates_data:
            metadata = manager.templates_data.get('metadata', {})
            print(f"✅ 模板系统正常，版本: {metadata.get('version', '未知')}")
        else:
            print("❌ 模板系统异常")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 系统健康检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 端到端测试")
    print("=" * 60)
    print("测试整个系统的完整功能流程")
    print()
    
    tests = [
        ("环境设置", test_environment_setup),
        ("数据管道", test_data_pipeline),
        ("模板系统", test_template_system),
        ("前端集成", test_frontend_integration),
        ("日历生成", test_calendar_generation),
        ("ICS解析", test_ics_parsing),
        ("邮件系统", test_email_system),
        ("系统健康", test_system_health),
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            failed_tests.append(test_name)
        print()
    
    print("=" * 60)
    print(f"📊 端到端测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统端到端功能正常")
        
        print("\n✅ 验证完成的功能:")
        print("  • Google Sheets数据获取和清洗")
        print("  • 统一数据模型和类型安全")
        print("  • 动态模板系统（JSON配置）")
        print("  • 细化模板变量（周三、周六）")
        print("  • ICS日历生成和事件解析")
        print("  • Web界面集成")
        print("  • 邮件系统准备")
        print("  • 静态文件服务")
        
        print("\n🚀 系统已准备就绪！")
        print("  启动命令: python3 start.py")
        print("  访问地址: http://localhost:8501")
        print("  日历生成: python3 generate_calendars.py")
        
    else:
        print(f"⚠️ {len(failed_tests)} 个测试失败:")
        for test in failed_tests:
            print(f"  • {test}")
        
        if passed >= total * 0.8:  # 80%以上通过
            print("\n💡 大部分功能正常，系统基本可用")
            print("  可以尝试启动: python3 start.py")
        else:
            print("\n❌ 关键功能存在问题，建议先修复")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎉 端到端测试完全通过！' if success else '⚠️ 端到端测试部分失败'}")
    sys.exit(0 if success else 1)
