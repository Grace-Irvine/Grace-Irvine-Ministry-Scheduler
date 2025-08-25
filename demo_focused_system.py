#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 专注系统演示
演示新的专注数据处理和模板生成功能
"""
from focused_data_cleaner import FocusedDataCleaner
from datetime import date, timedelta

def demo_data_extraction():
    """演示数据提取功能"""
    print("🎯 数据提取演示")
    print("=" * 50)
    
    # 创建清洗器
    cleaner = FocusedDataCleaner()
    
    # 下载和处理数据
    raw_df = cleaner.download_data()
    print(f"✅ 下载了 {len(raw_df)} 行原始数据")
    
    # 提取指定列
    focused_df = cleaner.extract_focused_columns(raw_df)
    print(f"✅ 提取了 {len(focused_df)} 行，{len(focused_df.columns)} 列专注数据")
    print(f"📋 列名: {list(focused_df.columns)}")
    
    # 清洗数据
    schedules = cleaner.clean_focused_data(focused_df)
    print(f"✅ 生成了 {len(schedules)} 个有效排程记录")
    
    return schedules

def demo_template_generation(schedules):
    """演示模板生成功能"""
    print("\n📝 模板生成演示")
    print("=" * 50)
    
    # 查找下周主日
    today = date.today()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    next_sunday = today + timedelta(days=days_until_sunday)
    
    print(f"📅 下周主日日期: {next_sunday.strftime('%Y年%m月%d日')}")
    
    # 查找对应的排程
    next_week_schedule = None
    for schedule in schedules:
        if schedule.date == next_sunday:
            next_week_schedule = schedule
            break
    
    if next_week_schedule:
        print("✅ 找到下周主日的排程数据")
        assignments = next_week_schedule.get_all_assignments()
        if assignments:
            print("👥 事工安排:")
            for role, person in assignments.items():
                print(f"  • {role}: {person}")
        else:
            print("⚠️  暂无事工安排")
        
        # 生成周三确认通知模板
        print("\n📋 周三确认通知模板:")
        print("-" * 30)
        wednesday_template = generate_wednesday_template(next_sunday, next_week_schedule)
        print(wednesday_template)
        
        # 生成周六提醒通知模板
        print("\n📋 周六提醒通知模板:")
        print("-" * 30)
        saturday_template = generate_saturday_template(next_sunday, next_week_schedule)
        print(saturday_template)
        
    else:
        print("⚠️  未找到下周主日的排程数据")
        print("📋 可用的日期:")
        available_dates = sorted([s.date for s in schedules if s.date >= today])
        for d in available_dates[:5]:
            print(f"  • {d.strftime('%Y年%m月%d日')}")

def generate_wednesday_template(sunday_date, schedule):
    """生成周三确认通知模板"""
    template = f"""【本周{sunday_date.month}月{sunday_date.day}日主日事工安排提醒】🕊️

"""
    
    assignments = schedule.get_all_assignments()
    if assignments:
        for role, person in assignments.items():
            template += f"• {role}：{person}\n"
    else:
        template += "• 音控：待安排\n• 导播/摄影：待安排\n• ProPresenter播放：待安排\n• ProPresenter更新：待安排\n"
    
    template += """• 视频剪辑：靖铮

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
    
    return template

def generate_saturday_template(sunday_date, schedule):
    """生成周六提醒通知模板"""
    template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  

"""
    
    assignments = schedule.get_all_assignments()
    
    if assignments.get('音控'):
        template += f"- 音控：{assignments['音控']} 9:00到，随敬拜团排练\n"
    else:
        template += "- 音控：待确认 9:00到，随敬拜团排练\n"
    
    if assignments.get('导播/摄影'):
        template += f"- 导播/摄影: {assignments['导播/摄影']} 9:30到，检查预设机位\n"
    else:
        template += "- 导播/摄影: 待确认 9:30到，检查预设机位\n"
    
    if assignments.get('ProPresenter播放'):
        template += f"- ProPresenter播放：{assignments['ProPresenter播放']} 9:00到，随敬拜团排练\n"
    else:
        template += "- ProPresenter播放：待确认 9:00到，随敬拜团排练\n"
    
    if assignments.get('ProPresenter更新'):
        template += f"- ProPresenter更新：{assignments['ProPresenter更新']} 提前准备内容\n"
    
    template += "\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌"
    
    return template

def demo_summary_statistics(schedules):
    """演示汇总统计功能"""
    print("\n📊 汇总统计演示")
    print("=" * 50)
    
    # 使用清洗器生成汇总报告
    cleaner = FocusedDataCleaner()
    summary = cleaner.generate_summary_report(schedules)
    
    print(f"📋 总排程数: {summary['total_schedules']}")
    print(f"📅 日期范围: {summary['date_range']}")
    print(f"👥 志愿者总数: {summary['volunteer_statistics']['total_volunteers']}")
    
    print("\n🎯 角色统计:")
    for role, count in summary['role_statistics'].items():
        print(f"  • {role}: {count} 次")
    
    print(f"\n👥 志愿者名单:")
    volunteers = summary['volunteer_statistics']['volunteer_list']
    for i, volunteer in enumerate(volunteers, 1):
        print(f"  {i:2d}. {volunteer}")

def main():
    """主演示函数"""
    print("🎯 Grace Irvine Ministry Scheduler - 专注系统演示")
    print("📋 专门提取列: A(日期), Q(音控), S(导播/摄影), T(ProPresenter播放), U(ProPresenter更新)")
    print("=" * 80)
    
    try:
        # 1. 数据提取演示
        schedules = demo_data_extraction()
        
        # 2. 模板生成演示
        demo_template_generation(schedules)
        
        # 3. 汇总统计演示
        demo_summary_statistics(schedules)
        
        print("\n🎉 演示完成！")
        print("\n💡 下一步您可以:")
        print("  1. 运行 python3 run_streamlit.py 启动 Web 界面")
        print("  2. 运行 python3 focused_data_cleaner.py 进行完整数据处理")
        print("  3. 查看 data/ 目录中的输出文件")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
