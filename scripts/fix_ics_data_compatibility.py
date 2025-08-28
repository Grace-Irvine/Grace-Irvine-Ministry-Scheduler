#!/usr/bin/env python3
"""
修复ICS日历管理中的数据兼容性问题
解决 MinistrySchedule 和 MinistryAssignment 数据结构不匹配的问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_cleaner import MinistrySchedule
from src.scheduler import MinistryAssignment
from datetime import date

def convert_schedule_to_assignment(schedule: MinistrySchedule) -> MinistryAssignment:
    """将 MinistrySchedule 转换为 MinistryAssignment"""
    return MinistryAssignment(
        date=schedule.date,
        audio_tech=schedule.audio_tech or "",
        screen_operator="",  # MinistrySchedule 中没有这个字段
        camera_operator=schedule.video_director or "",
        propresenter=schedule.propresenter_play or "",
        video_editor=schedule.propresenter_update or "靖铮"
    )

def convert_assignments_to_schedules(assignments: list) -> list:
    """将 MinistryAssignment 列表转换为 MinistrySchedule 列表"""
    schedules = []
    for assignment in assignments:
        schedule = MinistrySchedule(
            date=assignment.date,
            audio_tech=assignment.audio_tech,
            video_director=assignment.camera_operator,
            propresenter_play=assignment.propresenter,
            propresenter_update=assignment.video_editor
        )
        schedules.append(schedule)
    return schedules

def test_data_conversion():
    """测试数据转换功能"""
    print("🧪 测试数据转换功能")
    print("=" * 60)
    
    # 创建测试数据
    test_schedule = MinistrySchedule(
        date=date(2024, 1, 14),
        audio_tech="张三",
        video_director="李四",
        propresenter_play="王五",
        propresenter_update="赵六"
    )
    
    print("📋 原始 MinistrySchedule:")
    print(f"  日期: {test_schedule.date}")
    print(f"  音控: {test_schedule.audio_tech}")
    print(f"  导播/摄影: {test_schedule.video_director}")
    print(f"  ProPresenter播放: {test_schedule.propresenter_play}")
    print(f"  ProPresenter更新: {test_schedule.propresenter_update}")
    
    # 转换为 MinistryAssignment
    assignment = convert_schedule_to_assignment(test_schedule)
    
    print("\n📋 转换后的 MinistryAssignment:")
    print(f"  日期: {assignment.date}")
    print(f"  音控: {assignment.audio_tech}")
    print(f"  屏幕: {assignment.screen_operator}")
    print(f"  摄像/导播: {assignment.camera_operator}")
    print(f"  Propresenter: {assignment.propresenter}")
    print(f"  视频剪辑: {assignment.video_editor}")
    
    # 测试反向转换
    converted_schedule = convert_assignments_to_schedules([assignment])[0]
    
    print("\n📋 反向转换后的 MinistrySchedule:")
    print(f"  日期: {converted_schedule.date}")
    print(f"  音控: {converted_schedule.audio_tech}")
    print(f"  导播/摄影: {converted_schedule.video_director}")
    print(f"  ProPresenter播放: {converted_schedule.propresenter_play}")
    print(f"  ProPresenter更新: {converted_schedule.propresenter_update}")
    
    # 验证转换正确性
    assert assignment.date == test_schedule.date
    assert assignment.audio_tech == test_schedule.audio_tech
    assert assignment.camera_operator == test_schedule.video_director
    assert assignment.propresenter == test_schedule.propresenter_play
    assert assignment.video_editor == test_schedule.propresenter_update
    
    print("\n✅ 数据转换测试通过！")

def generate_conversion_functions():
    """生成转换函数代码"""
    print("\n📝 生成的转换函数代码:")
    print("=" * 60)
    
    conversion_code = '''
def convert_schedule_to_assignment(schedule: MinistrySchedule) -> MinistryAssignment:
    """将 MinistrySchedule 转换为 MinistryAssignment"""
    return MinistryAssignment(
        date=schedule.date,
        audio_tech=schedule.audio_tech or "",
        screen_operator="",  # MinistrySchedule 中没有这个字段
        camera_operator=schedule.video_director or "",
        propresenter=schedule.propresenter_play or "",
        video_editor=schedule.propresenter_update or "靖铮"
    )

def convert_schedules_to_assignments(schedules: list) -> list:
    """将 MinistrySchedule 列表转换为 MinistryAssignment 列表"""
    return [convert_schedule_to_assignment(schedule) for schedule in schedules]
'''
    
    print(conversion_code)

if __name__ == "__main__":
    test_data_conversion()
    generate_conversion_functions()
