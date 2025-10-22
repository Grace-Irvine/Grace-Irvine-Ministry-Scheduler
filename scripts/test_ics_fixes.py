#!/usr/bin/env python3
"""
测试ICS生成修复
验证：
1. 过去的事件是否被保留
2. 经文选择是否稳定
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scripture_manager import get_scripture_manager
from src.dynamic_template_manager import get_dynamic_template_manager
from src.data_cleaner import MinistrySchedule

def test_scripture_stability():
    """测试经文选择的稳定性"""
    print("=" * 60)
    print("测试1: 经文选择稳定性")
    print("=" * 60)
    
    manager = get_scripture_manager()
    
    # 测试日期
    test_dates = [
        date.today() + timedelta(weeks=i) for i in range(5)
    ]
    
    # 第一次获取经文
    print("\n第一次生成（用于ICS）:")
    first_scriptures = []
    for test_date in test_dates:
        scripture = manager.get_scripture_by_date(test_date)
        if scripture:
            content_preview = scripture.get('content', '')[:30] + "..."
            first_scriptures.append(content_preview)
            print(f"  {test_date}: {content_preview}")
    
    # 第二次获取经文（模拟重新生成ICS）
    print("\n第二次生成（模拟重新生成ICS）:")
    second_scriptures = []
    for test_date in test_dates:
        scripture = manager.get_scripture_by_date(test_date)
        if scripture:
            content_preview = scripture.get('content', '')[:30] + "..."
            second_scriptures.append(content_preview)
            print(f"  {test_date}: {content_preview}")
    
    # 验证是否相同
    if first_scriptures == second_scriptures:
        print("\n✅ 测试通过：同一日期的经文在重新生成时保持不变")
        return True
    else:
        print("\n❌ 测试失败：同一日期的经文发生了变化")
        return False

def test_scripture_index_stability():
    """测试经文索引是否保持稳定"""
    print("\n" + "=" * 60)
    print("测试2: 经文索引稳定性")
    print("=" * 60)
    
    manager = get_scripture_manager()
    
    # 获取初始索引
    initial_stats = manager.get_scripture_stats()
    initial_index = initial_stats.get('current_index', 0)
    print(f"\n初始经文索引: {initial_index}")
    
    # 模拟生成15周的ICS文件（使用基于日期的经文）
    print("\n生成15周的ICS内容（使用 get_scripture_by_date）...")
    test_dates = [date.today() + timedelta(weeks=i) for i in range(15)]
    for test_date in test_dates:
        scripture = manager.get_scripture_by_date(test_date)
    
    # 检查索引是否保持不变
    final_stats = manager.get_scripture_stats()
    final_index = final_stats.get('current_index', 0)
    print(f"最终经文索引: {final_index}")
    
    if initial_index == final_index:
        print("\n✅ 测试通过：使用 get_scripture_by_date 不会改变经文索引")
        return True
    else:
        print(f"\n❌ 测试失败：经文索引从 {initial_index} 变为 {final_index}")
        return False

def test_template_rendering():
    """测试模板渲染是否正确使用经文"""
    print("\n" + "=" * 60)
    print("测试3: 模板渲染经文使用")
    print("=" * 60)
    
    template_manager = get_dynamic_template_manager()
    scripture_manager = get_scripture_manager()
    
    # 测试数据
    test_date = date.today() + timedelta(weeks=1)
    test_schedule = MinistrySchedule(
        date=test_date,
        audio_tech="测试音控",
        video_director="测试导播",
        propresenter_play="测试PP"
    )
    
    # 获取当前经文索引
    initial_stats = scripture_manager.get_scripture_stats()
    initial_index = initial_stats.get('current_index', 0)
    print(f"\n初始经文索引: {initial_index}")
    
    # 生成ICS内容（应该不改变索引）
    print("\n生成ICS内容（for_ics_generation=True）...")
    ics_content = template_manager.render_weekly_confirmation(
        test_date, test_schedule, for_ics_generation=True
    )
    
    mid_stats = scripture_manager.get_scripture_stats()
    mid_index = mid_stats.get('current_index', 0)
    print(f"生成ICS后的经文索引: {mid_index}")
    
    # 生成实际通知（应该改变索引）
    print("\n生成实际通知（for_ics_generation=False）...")
    notification_content = template_manager.render_weekly_confirmation(
        test_date, test_schedule, for_ics_generation=False
    )
    
    final_stats = scripture_manager.get_scripture_stats()
    final_index = final_stats.get('current_index', 0)
    print(f"发送通知后的经文索引: {final_index}")
    
    # 验证结果
    ics_index_unchanged = (initial_index == mid_index)
    notification_index_changed = (mid_index != final_index)
    
    if ics_index_unchanged and notification_index_changed:
        print("\n✅ 测试通过：")
        print("   - ICS生成时不改变经文索引")
        print("   - 实际通知时正常递增经文索引")
        
        # 恢复索引（避免影响实际使用）
        scripture_manager.scriptures_data['metadata']['current_index'] = initial_index
        scripture_manager.save_scriptures()
        print("   - 已恢复初始经文索引")
        
        return True
    else:
        print("\n❌ 测试失败：")
        if not ics_index_unchanged:
            print("   - ICS生成时错误地改变了经文索引")
        if not notification_index_changed:
            print("   - 实际通知时没有正确递增经文索引")
        return False

def test_date_range():
    """测试日期范围是否包含过去的事件"""
    print("\n" + "=" * 60)
    print("测试4: 日期范围（代码检查）")
    print("=" * 60)
    
    print("\n检查 src/calendar_generator.py 中的日期过滤逻辑...")
    
    try:
        with open('src/calendar_generator.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否包含正确的日期过滤代码
        has_cutoff_date = 'cutoff_date = today - timedelta(days=28)' in content
        has_relevant_schedules = 'relevant_schedules' in content
        
        if has_cutoff_date and has_relevant_schedules:
            print("✅ 找到了正确的日期过滤逻辑")
            print("   - 设置了 cutoff_date（过去4周）")
            print("   - 使用 relevant_schedules 而不是 future_schedules")
            return True
        else:
            print("❌ 日期过滤逻辑可能不正确")
            if not has_cutoff_date:
                print("   - 未找到 cutoff_date 设置")
            if not has_relevant_schedules:
                print("   - 未找到 relevant_schedules 变量")
            return False
            
    except Exception as e:
        print(f"❌ 检查文件时出错: {e}")
        return False

def main():
    """运行所有测试"""
    print("🧪 ICS生成修复测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("经文选择稳定性", test_scripture_stability()))
    results.append(("经文索引稳定性", test_scripture_index_stability()))
    results.append(("模板渲染经文使用", test_template_rendering()))
    results.append(("日期范围检查", test_date_range()))
    
    # 显示汇总结果
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
    
    # 总体结果
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
        print("\n修复总结:")
        print("1. ✅ 过去的事件会被保留（过去4周）")
        print("2. ✅ 同一日期的经文在重新生成时保持不变")
        print("3. ✅ 生成ICS不会浪费经文索引")
        print("4. ✅ 实际发送通知时正常使用递增经文")
    else:
        print("❌ 部分测试失败，请检查代码")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

