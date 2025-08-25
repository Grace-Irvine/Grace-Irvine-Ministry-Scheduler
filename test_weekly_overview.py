#!/usr/bin/env python3
"""
测试周程概览功能
Test Weekly Schedule Overview Feature
"""
from focused_data_cleaner import FocusedDataCleaner
from datetime import date, timedelta

def get_sunday_of_week(target_date):
    """获取指定日期所在周的周日日期"""
    days_since_sunday = target_date.weekday() + 1  # Monday=0 -> 1, Sunday=6 -> 0
    if days_since_sunday == 7:  # 如果是周日
        days_since_sunday = 0
    return target_date - timedelta(days=days_since_sunday)

def get_week_label(sunday, today):
    """获取周次标签"""
    current_sunday = get_sunday_of_week(today)
    week_diff = (sunday - current_sunday).days // 7
    
    if week_diff == -2:
        return "前两周"
    elif week_diff == -1:
        return "上周"
    elif week_diff == 0:
        return "本周"
    elif week_diff == 1:
        return "下周"
    elif week_diff == 2:
        return "下下周"
    elif week_diff > 2:
        return f"未来第{week_diff}周"
    else:
        return f"过去第{abs(week_diff)}周"

def test_weekly_overview():
    """测试周程概览功能"""
    print("🧪 测试周程概览功能")
    print("=" * 50)
    
    # 创建数据清洗器并获取数据
    cleaner = FocusedDataCleaner()
    raw_df = cleaner.download_data()
    focused_df = cleaner.extract_focused_columns(raw_df)
    schedules = cleaner.clean_focused_data(focused_df)
    
    print(f"✅ 获取了 {len(schedules)} 个排程记录")
    
    # 获取当前日期和相关周日
    today = date.today()
    current_sunday = get_sunday_of_week(today)
    
    print(f"📅 今天: {today}")
    print(f"📅 本周周日: {current_sunday}")
    
    # 计算目标周日期（前两周到未来几周）
    target_sundays = []
    for i in range(-2, 8):  # 前2周 + 当前周 + 未来7周 = 10周
        sunday = current_sunday + timedelta(weeks=i)
        target_sundays.append(sunday)
    
    print(f"\n📋 目标周日期范围: {target_sundays[0]} 到 {target_sundays[-1]}")
    
    # 按周日分组排程数据
    schedule_by_sunday = {}
    for schedule in schedules:
        sunday = get_sunday_of_week(schedule.date)
        if sunday in target_sundays:
            schedule_by_sunday[sunday] = schedule
    
    print(f"✅ 找到 {len(schedule_by_sunday)} 个相关周的排程")
    
    # 显示周程概览
    print(f"\n📅 周程概览:")
    print("-" * 80)
    print(f"{'周次':<12} {'日期':<12} {'音控':<10} {'导播/摄影':<12} {'PP播放':<12} {'PP更新':<12}")
    print("-" * 80)
    
    arranged_count = 0
    for sunday in target_sundays:
        week_label = get_week_label(sunday, today)
        schedule = schedule_by_sunday.get(sunday)
        
        if schedule:
            assignments = schedule.get_all_assignments()
            audio = assignments.get('音控', '')[:8]  # 截断长名字
            video = assignments.get('导播/摄影', '')[:10]
            pp_play = assignments.get('ProPresenter播放', '')[:10]
            pp_update = assignments.get('ProPresenter更新', '')[:10]
            
            print(f"{week_label:<12} {sunday.strftime('%Y-%m-%d'):<12} {audio:<10} {video:<12} {pp_play:<12} {pp_update:<12}")
            
            if any([audio, video, pp_play, pp_update]):
                arranged_count += 1
        else:
            print(f"{week_label:<12} {sunday.strftime('%Y-%m-%d'):<12} {'':10} {'':12} {'':12} {'':12}")
    
    print("-" * 80)
    print(f"📊 统计: {arranged_count}/{len(target_sundays)} 周已安排")
    
    # 检查重点提醒
    print(f"\n🔔 重点提醒:")
    
    # 检查本周和下周
    this_sunday = current_sunday
    next_sunday = current_sunday + timedelta(weeks=1)
    
    this_week_schedule = schedule_by_sunday.get(this_sunday)
    next_week_schedule = schedule_by_sunday.get(next_sunday)
    
    if this_week_schedule:
        assignments = this_week_schedule.get_all_assignments()
        if not any([assignments.get('音控'), assignments.get('导播/摄影'), assignments.get('ProPresenter播放')]):
            print("🚨 本周主日暂无完整安排，请尽快确认！")
        else:
            print("✅ 本周主日安排完整")
    else:
        print("⚠️ 本周主日暂无安排")
    
    if next_week_schedule:
        assignments = next_week_schedule.get_all_assignments()
        if not any([assignments.get('音控'), assignments.get('导播/摄影'), assignments.get('ProPresenter播放')]):
            print("⏰ 下周主日安排不完整，建议提前准备")
        else:
            print("✅ 下周主日安排完整")
    else:
        print("⚠️ 下周主日暂无安排")
    
    # 显示即将到来的安排
    print(f"\n📅 即将到来的安排:")
    future_schedules = [(sunday, schedule) for sunday, schedule in schedule_by_sunday.items() 
                       if sunday >= today and sunday <= today + timedelta(weeks=4)]
    future_schedules.sort(key=lambda x: x[0])
    
    for sunday, schedule in future_schedules[:3]:  # 只显示前3个
        week_label = get_week_label(sunday, today)
        assignments = schedule.get_all_assignments()
        print(f"  • {week_label} ({sunday.strftime('%m/%d')}): ", end="")
        
        assignment_list = []
        if assignments.get('音控'):
            assignment_list.append(f"音控:{assignments['音控']}")
        if assignments.get('导播/摄影'):
            assignment_list.append(f"导播:{assignments['导播/摄影']}")
        if assignments.get('ProPresenter播放'):
            assignment_list.append(f"PP:{assignments['ProPresenter播放']}")
        
        if assignment_list:
            print(", ".join(assignment_list))
        else:
            print("暂无安排")

def main():
    """主函数"""
    try:
        test_weekly_overview()
        print(f"\n🎉 周程概览功能测试完成！")
        print(f"💡 现在可以运行 python3 run_streamlit.py 查看完整的 Web 界面")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
