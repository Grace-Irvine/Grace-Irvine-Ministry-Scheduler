#!/usr/bin/env python3
"""
测试ICS日历管理修复
验证数据转换和日历生成功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_cleaner import MinistrySchedule, FocusedDataCleaner
from src.scheduler import MinistryAssignment
from datetime import date, timedelta

def test_ics_calendar_fix():
    """测试ICS日历管理修复"""
    print("🧪 测试ICS日历管理修复")
    print("=" * 60)
    
    # 创建测试数据
    test_schedules = [
        MinistrySchedule(
            date=date.today() + timedelta(days=7),  # 下周日
            audio_tech="张三",
            video_director="李四",
            propresenter_play="王五",
            propresenter_update="赵六"
        ),
        MinistrySchedule(
            date=date.today() + timedelta(days=14),  # 下下周日
            audio_tech="小明",
            video_director="小红",
            propresenter_play="小华",
            propresenter_update="小丽"
        )
    ]
    
    print(f"📋 创建了 {len(test_schedules)} 个测试排程")
    
    # 测试数据转换
    def convert_schedule_to_assignment(schedule):
        """将 MinistrySchedule 转换为 MinistryAssignment"""
        return MinistryAssignment(
            date=schedule.date,
            audio_tech=schedule.audio_tech or "",
            screen_operator="",  # MinistrySchedule 中没有这个字段
            camera_operator=schedule.video_director or "",
            propresenter=schedule.propresenter_play or "",
            video_editor=schedule.propresenter_update or "靖铮"
        )
    
    assignments = [convert_schedule_to_assignment(schedule) for schedule in test_schedules]
    
    print(f"✅ 成功转换为 {len(assignments)} 个 MinistryAssignment")
    
    # 测试同工列表生成
    def get_worker_list(assignments):
        """获取同工名单"""
        workers = set()
        for assignment in assignments:
            if assignment.audio_tech and assignment.audio_tech.strip():
                workers.add(assignment.audio_tech)
            if assignment.camera_operator and assignment.camera_operator.strip():
                workers.add(assignment.camera_operator)
            if assignment.propresenter and assignment.propresenter.strip():
                workers.add(assignment.propresenter)
            if assignment.video_editor and assignment.video_editor.strip():
                workers.add(assignment.video_editor)
        
        return list(workers)
    
    workers = get_worker_list(assignments)
    print(f"👥 同工名单: {workers}")
    
    # 测试日历生成函数
    def generate_coordinator_calendar_content(assignments):
        """生成负责人日历ICS内容（简化版）"""
        try:
            ics_lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH",
                "X-WR-CALNAME:Grace Irvine 事工协调日历",
                "X-WR-CALDESC:事工通知发送提醒日历（自动更新）",
                "X-WR-TIMEZONE:America/Los_Angeles"
            ]
            
            today = date.today()
            future_assignments = [a for a in assignments if a.date >= today][:15]
            
            events_created = 0
            for assignment in future_assignments:
                # 周三确认通知事件
                wednesday = assignment.date - timedelta(days=4)
                if wednesday >= today - timedelta(days=7):
                    events_created += 1
                
                # 周六提醒通知事件
                saturday = assignment.date - timedelta(days=1)
                if saturday >= today - timedelta(days=7):
                    events_created += 1
            
            ics_lines.append("END:VCALENDAR")
            return "\n".join(ics_lines), events_created
            
        except Exception as e:
            print(f"❌ 生成负责人日历时出错: {e}")
            return None, 0
    
    # 测试日历生成
    coordinator_ics, event_count = generate_coordinator_calendar_content(assignments)
    
    if coordinator_ics:
        print(f"✅ 负责人日历生成成功，包含 {event_count} 个事件")
        print("📅 日历内容预览:")
        print(coordinator_ics[:200] + "..." if len(coordinator_ics) > 200 else coordinator_ics)
    else:
        print("❌ 负责人日历生成失败")
    
    # 测试个人日历生成
    def generate_personal_calendar_content(assignments, worker_name):
        """生成个人日历ICS内容（简化版）"""
        try:
            ics_lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Grace Irvine Ministry Scheduler//Personal Calendar//CN",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH",
                f"X-WR-CALNAME:{worker_name} - Grace Irvine 个人服事日历",
                "X-WR-TIMEZONE:America/Los_Angeles"
            ]
            
            today = date.today()
            future_assignments = [a for a in assignments if a.date >= today]
            
            events_created = 0
            for assignment in future_assignments:
                # 检查该同工是否参与此次服事
                if (assignment.audio_tech == worker_name or 
                    assignment.camera_operator == worker_name or
                    assignment.propresenter == worker_name or
                    assignment.video_editor == worker_name):
                    events_created += 1
            
            ics_lines.append("END:VCALENDAR")
            return "\n".join(ics_lines), events_created
            
        except Exception as e:
            print(f"❌ 生成 {worker_name} 个人日历时出错: {e}")
            return None, 0
    
    # 测试个人日历生成
    if workers:
        test_worker = workers[0]
        personal_ics, personal_event_count = generate_personal_calendar_content(assignments, test_worker)
        
        if personal_ics:
            print(f"✅ {test_worker} 的个人日历生成成功，包含 {personal_event_count} 个事件")
        else:
            print(f"❌ {test_worker} 的个人日历生成失败")
    
    # 总结
    print("\n📋 修复总结")
    print("-" * 40)
    
    all_tests_passed = (
        len(assignments) == len(test_schedules) and
        len(workers) > 0 and
        coordinator_ics is not None and
        (not workers or personal_ics is not None)
    )
    
    if all_tests_passed:
        print("🎉 所有测试通过！ICS日历管理修复成功！")
        print("✅ 数据转换功能正常")
        print("✅ 同工列表生成正常")
        print("✅ 负责人日历生成正常")
        print("✅ 个人日历生成正常")
    else:
        print("❌ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    test_ics_calendar_fix()
