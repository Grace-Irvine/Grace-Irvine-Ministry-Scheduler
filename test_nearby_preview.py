#!/usr/bin/env python3
"""
测试近期排程预览功能
Test Nearby Schedule Preview Feature
"""
from focused_data_cleaner import FocusedDataCleaner
from datetime import date, timedelta

def test_nearby_preview():
    """测试近期排程预览功能"""
    print("🧪 测试近期排程预览功能")
    print("=" * 50)
    
    # 创建数据清洗器并获取数据
    cleaner = FocusedDataCleaner()
    raw_df = cleaner.download_data()
    focused_df = cleaner.extract_focused_columns(raw_df)
    schedules = cleaner.clean_focused_data(focused_df)
    
    print(f"✅ 获取了 {len(schedules)} 个排程记录")
    
    today = date.today()
    print(f"📅 今天: {today}")
    
    # 获取当前日期前后的数据（前2周，后6周）
    start_date = today - timedelta(weeks=2)
    end_date = today + timedelta(weeks=6)
    
    print(f"📋 预览范围: {start_date} 到 {end_date}")
    
    # 过滤近期数据
    nearby_schedules = [
        s for s in schedules 
        if start_date <= s.date <= end_date
    ]
    
    print(f"✅ 找到 {len(nearby_schedules)} 个近期排程")
    
    if not nearby_schedules:
        print("⚠️ 未找到近期的排程数据")
        return
    
    # 转换为显示格式并显示
    print(f"\n📅 近期排程预览:")
    print("-" * 90)
    print(f"{'状态':<10} {'日期':<12} {'星期':<6} {'音控':<10} {'导播/摄影':<12} {'PP播放':<12} {'PP更新':<12}")
    print("-" * 90)
    
    preview_data = []
    for schedule in sorted(nearby_schedules, key=lambda x: x.date):
        # 确定状态和样式
        if schedule.date < today:
            status = "✅已完成"
        elif schedule.date == today:
            status = "📍今天"
        elif schedule.date <= today + timedelta(days=7):
            status = "🔥本周"
        elif schedule.date <= today + timedelta(days=14):
            status = "⏰下周"
        else:
            status = "📅未来"
        
        weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][schedule.date.weekday()]
        assignments = schedule.get_all_assignments()
        
        audio = assignments.get('音控', '')[:8]
        video = assignments.get('导播/摄影', '')[:10]
        pp_play = assignments.get('ProPresenter播放', '')[:10]
        pp_update = assignments.get('ProPresenter更新', '')[:10]
        
        print(f"{status:<10} {schedule.date.strftime('%Y-%m-%d'):<12} {weekday:<6} {audio:<10} {video:<12} {pp_play:<12} {pp_update:<12}")
        
        preview_data.append({
            'status': status,
            'date': schedule.date,
            'assignments': assignments
        })
    
    print("-" * 90)
    
    # 统计信息
    completed_count = sum(1 for item in preview_data if '已完成' in item['status'])
    current_count = sum(1 for item in preview_data if '今天' in item['status'] or '本周' in item['status'])
    upcoming_count = sum(1 for item in preview_data if '下周' in item['status'])
    future_count = sum(1 for item in preview_data if '未来' in item['status'])
    
    print(f"\n📊 统计信息:")
    print(f"  ✅ 已完成: {completed_count}")
    print(f"  🔥 当前: {current_count}")
    print(f"  ⏰ 下周: {upcoming_count}")
    print(f"  📅 未来: {future_count}")
    
    # 重点关注信息
    print(f"\n🔔 重点关注:")
    highlights = []
    
    # 检查今天和本周的安排
    today_items = [item for item in preview_data if '今天' in item['status']]
    this_week_items = [item for item in preview_data if '本周' in item['status']]
    next_week_items = [item for item in preview_data if '下周' in item['status']]
    
    if today_items:
        for item in today_items:
            assignments = item['assignments']
            if any([assignments.get('音控'), assignments.get('导播/摄影'), assignments.get('ProPresenter播放')]):
                highlights.append(f"📍 今天主日: {assignments.get('音控', '待定')} (音控), {assignments.get('导播/摄影', '待定')} (导播)")
            else:
                highlights.append("🚨 今天主日暂无完整安排")
    
    if this_week_items:
        for item in this_week_items:
            assignments = item['assignments']
            if not any([assignments.get('音控'), assignments.get('导播/摄影'), assignments.get('ProPresenter播放')]):
                highlights.append(f"⚠️ {item['date'].strftime('%Y-%m-%d')} 本周主日安排不完整")
    
    if next_week_items:
        incomplete_next_week = []
        for item in next_week_items:
            assignments = item['assignments']
            if not any([assignments.get('音控'), assignments.get('导播/摄影'), assignments.get('ProPresenter播放')]):
                incomplete_next_week.append(item['date'].strftime('%Y-%m-%d'))
        
        if incomplete_next_week:
            highlights.append(f"⏰ 下周需要关注: {', '.join(incomplete_next_week)}")
    
    # 检查人员重复
    for item in preview_data:
        if '已完成' not in item['status']:  # 只检查未完成的
            assignments = item['assignments']
            assignment_list = [assignments.get('音控'), assignments.get('导播/摄影'), 
                             assignments.get('ProPresenter播放'), assignments.get('ProPresenter更新')]
            assignment_list = [a for a in assignment_list if a]  # 移除空值
            if len(assignment_list) != len(set(assignment_list)):  # 有重复
                duplicates = [a for a in set(assignment_list) if assignment_list.count(a) > 1]
                highlights.append(f"👥 {item['date'].strftime('%Y-%m-%d')} 重复安排: {', '.join(duplicates)}")
    
    # 显示重点信息
    if highlights:
        for highlight in highlights[:5]:  # 最多显示5个重点
            print(f"  {highlight}")
    else:
        print("  ✅ 近期排程安排良好")
    
    print(f"\n💡 功能特点:")
    print(f"  • 显示前2周到后6周的排程数据")
    print(f"  • 智能状态标识（已完成/今天/本周/下周/未来）")
    print(f"  • 自动检测安排完整性和人员冲突")
    print(f"  • 重点关注信息提醒")

def main():
    """主函数"""
    try:
        test_nearby_preview()
        print(f"\n🎉 近期排程预览功能测试完成！")
        print(f"💡 现在可以运行 python3 run_streamlit.py 在Web界面中查看此功能")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
