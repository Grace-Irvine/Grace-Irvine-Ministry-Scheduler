#!/usr/bin/env python3
"""
最终功能验证
Final Functionality Verification

验证所有核心功能是否按预期工作
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_data_model_unification():
    """验证数据模型统一化"""
    print("🔍 验证数据模型统一化...")
    
    try:
        from src.models import MinistryAssignment, ServiceRole
        from src.data_cleaner import MinistrySchedule  # 应该是别名
        
        # 验证别名
        if MinistrySchedule == MinistryAssignment:
            print("✅ 数据模型统一化成功")
        else:
            print("❌ 数据模型统一化失败")
            return False
        
        # 验证枚举
        roles = [role.value for role in ServiceRole]
        expected_roles = ["音控", "导播/摄影", "ProPresenter播放", "ProPresenter更新", "视频剪辑"]
        
        if set(roles) == set(expected_roles):
            print("✅ 服事角色枚举正确")
        else:
            print(f"❌ 服事角色枚举不完整: {roles}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 数据模型验证失败: {e}")
        return False

def verify_template_variables():
    """验证模板变量细化"""
    print("📝 验证模板变量细化...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        
        manager = DynamicTemplateManager()
        
        # 验证周三模板变量
        wed_variables = manager.get_template_variables('weekly_confirmation')
        expected_wed_vars = ['month', 'day', 'audio_tech', 'video_director', 'propresenter_play', 'propresenter_update', 'video_editor']
        
        missing_wed_vars = [var for var in expected_wed_vars if var not in wed_variables]
        if missing_wed_vars:
            print(f"❌ 周三模板缺少变量: {missing_wed_vars}")
            return False
        else:
            print(f"✅ 周三模板变量完整 ({len(wed_variables)} 个)")
        
        # 验证周六模板变量
        sat_variables = manager.get_template_variables('saturday_reminder')
        expected_sat_vars = ['audio_tech_detail', 'video_director_detail', 'propresenter_play_detail', 'propresenter_update_detail']
        
        missing_sat_vars = [var for var in expected_sat_vars if var not in sat_variables]
        if missing_sat_vars:
            print(f"❌ 周六模板缺少变量: {missing_sat_vars}")
            return False
        else:
            print(f"✅ 周六模板变量完整 ({len(sat_variables)} 个)")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板变量验证失败: {e}")
        return False

def verify_template_rendering():
    """验证模板渲染效果"""
    print("🎨 验证模板渲染效果...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        from src.models import MinistryAssignment
        
        manager = DynamicTemplateManager()
        
        # 创建测试数据
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        # 验证周三模板
        wed_result = manager.render_weekly_confirmation(test_date, test_schedule)
        
        wed_checks = [
            ("包含标题", "事工安排提醒" in wed_result),
            ("包含音控", "音控：Jimmy" in wed_result),
            ("包含导播", "导播/摄影：靖铮" in wed_result),
            ("包含播放", "ProPresenter播放：张宇" in wed_result),
            ("包含更新", "ProPresenter更新：Daniel" in wed_result),
            ("包含结尾", "感谢摆上" in wed_result)
        ]
        
        wed_passed = all(check[1] for check in wed_checks)
        if wed_passed:
            print("✅ 周三模板渲染验证通过")
        else:
            failed_checks = [check[0] for check in wed_checks if not check[1]]
            print(f"❌ 周三模板验证失败: {failed_checks}")
            return False
        
        # 验证周六模板
        sat_result = manager.render_saturday_reminder(test_date, test_schedule)
        
        sat_checks = [
            ("包含标题", "主日服事提醒" in sat_result),
            ("包含音控详情", "Jimmy 9:00到，随敬拜团排练" in sat_result),
            ("包含导播详情", "靖铮 9:30到，检查预设机位" in sat_result),
            ("包含播放详情", "张宇 9:00到，随敬拜团排练" in sat_result),
            ("包含祝福", "愿主同在" in sat_result)
        ]
        
        sat_passed = all(check[1] for check in sat_checks)
        if sat_passed:
            print("✅ 周六模板渲染验证通过")
        else:
            failed_checks = [check[0] for check in sat_checks if not check[1]]
            print(f"❌ 周六模板验证失败: {failed_checks}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模板渲染验证失败: {e}")
        return False

def verify_ics_content():
    """验证ICS文件内容"""
    print("📅 验证ICS文件内容...")
    
    try:
        from app_unified import parse_ics_events
        
        calendar_file = Path("calendars/grace_irvine_coordinator.ics")
        if not calendar_file.exists():
            print("❌ 日历文件不存在")
            return False
        
        with open(calendar_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析事件
        events = parse_ics_events(content)
        
        if not events:
            print("❌ 未解析到任何事件")
            return False
        
        print(f"✅ 成功解析 {len(events)} 个事件")
        
        # 验证事件内容
        wed_events = [e for e in events if "周末确认通知" in e.get('summary', '')]
        sat_events = [e for e in events if "主日提醒通知" in e.get('summary', '')]
        
        if wed_events:
            print(f"✅ 找到 {len(wed_events)} 个周三确认事件")
            
            # 检查第一个周三事件的内容
            sample_wed = wed_events[0]
            description = sample_wed.get('description', '')
            
            if "音控：" in description and "导播/摄影：" in description:
                print("✅ 周三事件包含细化的角色信息")
            else:
                print("❌ 周三事件不包含细化的角色信息")
                return False
        
        if sat_events:
            print(f"✅ 找到 {len(sat_events)} 个周六提醒事件")
            
            # 检查第一个周六事件的内容
            sample_sat = sat_events[0]
            description = sample_sat.get('description', '')
            
            if "9:00到，随敬拜团排练" in description and "9:30到，检查预设机位" in description:
                print("✅ 周六事件包含细化的详情信息")
            else:
                print("❌ 周六事件不包含细化的详情信息")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ ICS内容验证失败: {e}")
        return False

def verify_template_consistency():
    """验证模板一致性"""
    print("🔄 验证模板一致性...")
    
    try:
        from app_unified import generate_wednesday_template, generate_saturday_template
        from src.calendar_generator import generate_unified_wednesday_template, generate_unified_saturday_template
        from src.models import MinistryAssignment
        
        # 创建测试数据
        test_date = date.today() + timedelta(days=7)
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel"
        )
        
        # 比较周三模板
        frontend_wed = generate_wednesday_template(test_date, test_schedule)
        calendar_wed = generate_unified_wednesday_template(test_date, test_schedule)
        
        if frontend_wed.strip() == calendar_wed.strip():
            print("✅ 周三模板前端和日历完全一致")
        else:
            print("❌ 周三模板前端和日历不一致")
            print(f"   前端长度: {len(frontend_wed)}")
            print(f"   日历长度: {len(calendar_wed)}")
            return False
        
        # 比较周六模板
        frontend_sat = generate_saturday_template(test_date, test_schedule)
        calendar_sat = generate_unified_saturday_template(test_date, test_schedule)
        
        if frontend_sat.strip() == calendar_sat.strip():
            print("✅ 周六模板前端和日历完全一致")
        else:
            print("❌ 周六模板前端和日历不一致")
            print(f"   前端长度: {len(frontend_sat)}")
            print(f"   日历长度: {len(calendar_sat)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模板一致性验证失败: {e}")
        return False

def verify_real_data_workflow():
    """验证真实数据工作流"""
    print("📊 验证真实数据工作流...")
    
    try:
        from src.data_cleaner import FocusedDataCleaner
        from src.dynamic_template_manager import DynamicTemplateManager
        
        # 1. 获取真实数据
        print("  📥 获取真实Google Sheets数据...")
        cleaner = FocusedDataCleaner()
        schedules = cleaner.process_complete_workflow()
        
        if not schedules['success']:
            print(f"❌ 真实数据获取失败: {schedules.get('error', '未知错误')}")
            return False
        
        real_schedules = schedules['schedules']
        print(f"✅ 获取到 {len(real_schedules)} 个真实排程")
        
        # 2. 生成真实模板
        print("  📝 使用真实数据生成模板...")
        manager = DynamicTemplateManager()
        
        # 找到未来的排程
        today = date.today()
        future_schedules = [s for s in real_schedules if s.date > today][:3]
        
        if future_schedules:
            for i, schedule in enumerate(future_schedules, 1):
                wed_template = manager.render_weekly_confirmation(schedule.date, schedule)
                sat_template = manager.render_saturday_reminder(schedule.date, schedule)
                
                print(f"✅ 排程 {i} ({schedule.date}): 模板生成成功")
                
                # 验证模板内容
                assignments = schedule.get_all_assignments()
                if assignments:
                    for role, person in list(assignments.items())[:2]:  # 检查前两个角色
                        if person in wed_template and person in sat_template:
                            print(f"   ✅ {role}: {person} 在模板中正确显示")
                        else:
                            print(f"   ❌ {role}: {person} 在模板中缺失")
                            return False
        else:
            print("⚠️ 未找到未来的排程，使用测试数据验证")
            
            from src.models import MinistryAssignment
            test_schedule = MinistryAssignment(
                date=today + timedelta(days=7),
                audio_tech="测试音控",
                video_director="测试导播"
            )
            
            wed_template = manager.render_weekly_confirmation(test_schedule.date, test_schedule)
            if "测试音控" in wed_template:
                print("✅ 测试数据模板生成正常")
            else:
                print("❌ 测试数据模板生成失败")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 真实数据工作流验证失败: {e}")
        return False

def verify_architecture_improvements():
    """验证架构改进"""
    print("🏗️ 验证架构改进...")
    
    # 1. 验证文件简化
    print("  🧹 验证文件简化...")
    removed_files = [
        "start_service.py",
        "run_enhanced_streamlit.py",
        "app_with_static_routes.py",
        "generate_real_calendars.py"
    ]
    
    still_exists = []
    for file in removed_files:
        if Path(file).exists():
            still_exists.append(file)
    
    if still_exists:
        print(f"❌ 以下文件应该被删除: {still_exists}")
        return False
    else:
        print("✅ 重复文件已成功清理")
    
    # 2. 验证新文件结构
    print("  📁 验证新文件结构...")
    expected_files = {
        "start.py": "统一启动入口",
        "app_unified.py": "统一Web应用",
        "generate_calendars.py": "日历生成启动器",
        "src/models.py": "统一数据模型",
        "src/calendar_generator.py": "日历生成器",
        "src/dynamic_template_manager.py": "动态模板管理器",
        "templates/dynamic_templates.json": "动态模板配置"
    }
    
    missing_files = []
    for file, desc in expected_files.items():
        if not Path(file).exists():
            missing_files.append(f"{file} ({desc})")
        else:
            print(f"   ✅ {file}")
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    return True

def generate_sample_outputs():
    """生成示例输出"""
    print("📋 生成示例输出...")
    
    try:
        from src.dynamic_template_manager import DynamicTemplateManager
        from src.models import MinistryAssignment
        
        manager = DynamicTemplateManager()
        
        # 创建示例数据
        sample_date = date.today() + timedelta(days=7)
        sample_schedule = MinistryAssignment(
            date=sample_date,
            audio_tech="Jimmy",
            video_director="靖铮",
            propresenter_play="张宇",
            propresenter_update="Daniel",
            video_editor="靖铮"
        )
        
        # 生成示例模板
        wed_example = manager.render_weekly_confirmation(sample_date, sample_schedule)
        sat_example = manager.render_saturday_reminder(sample_date, sample_schedule)
        
        # 保存示例到文件
        examples_dir = Path("data/examples")
        examples_dir.mkdir(exist_ok=True)
        
        with open(examples_dir / "sample_wednesday_template.txt", 'w', encoding='utf-8') as f:
            f.write(wed_example)
        
        with open(examples_dir / "sample_saturday_template.txt", 'w', encoding='utf-8') as f:
            f.write(sat_example)
        
        print("✅ 示例输出已生成到 data/examples/ 目录")
        
        # 显示示例内容
        print("\n📋 周三确认通知示例:")
        print("-" * 40)
        print(wed_example)
        
        print("\n📋 周六提醒通知示例:")
        print("-" * 40)
        print(sat_example)
        
        return True
        
    except Exception as e:
        print(f"❌ 示例输出生成失败: {e}")
        return False

def main():
    """主验证函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 最终功能验证")
    print("=" * 60)
    print("验证所有架构改进和功能实现")
    print()
    
    verifications = [
        ("数据模型统一化", verify_data_model_unification),
        ("模板变量细化", verify_template_variables),
        ("模板渲染效果", verify_template_rendering),
        ("ICS文件内容", verify_ics_content),
        ("模板一致性", verify_template_consistency),
        ("架构改进", verify_architecture_improvements),
        ("真实数据工作流", verify_real_data_workflow),
        ("示例输出生成", generate_sample_outputs),
    ]
    
    passed = 0
    total = len(verifications)
    
    for verification_name, verification_func in verifications:
        print(f"{'='*15} {verification_name} {'='*15}")
        if verification_func():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 最终验证结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有验证通过！系统功能完全正常")
        
        print("\n✅ 完成的改进:")
        print("  🏗️ 架构简化: 统一入口点，删除重复文件")
        print("  📊 数据模型: 统一MinistryAssignment，类型安全")
        print("  📝 动态模板: JSON配置，支持云端存储")
        print("  🎨 细化变量: 周三、周六模板变量细化")
        print("  🔄 模板一致: 前端、邮件、ICS使用相同模板")
        print("  📅 ICS生成: 负责人日历，事件解析功能")
        
        print("\n🚀 系统已完全准备就绪！")
        print("  💻 本地启动: python3 start.py")
        print("  🌐 访问地址: http://localhost:8501")
        print("  📅 生成日历: python3 generate_calendars.py")
        print("  ☁️ 云端部署: python3 deploy_cloud_run_with_static.py")
        
        print("\n📱 主要功能:")
        print("  • 📊 数据概览: 查看排程数据和统计")
        print("  • 📝 模板生成: 生成微信群通知模板")
        print("  • 🛠️ 模板编辑: 在线编辑和自定义模板")
        print("  • 📅 日历管理: ICS文件生成和订阅")
        print("  • ⚙️ 系统设置: 配置管理和状态监控")
        
    else:
        failed_count = total - passed
        print(f"⚠️ {failed_count} 个验证失败，需要进一步检查")
        
        if passed >= total * 0.9:  # 90%以上通过
            print("\n💡 核心功能基本正常，可以开始使用")
            print("  启动命令: python3 start.py")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎊 最终验证完全成功！' if success else '⚠️ 最终验证部分失败'}")
    sys.exit(0 if success else 1)
