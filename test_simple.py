#!/usr/bin/env python3
"""
简单测试脚本 - 验证核心功能

无需真实的 Google Sheets 连接，使用模拟数据测试模板生成。
"""

from datetime import date, datetime
from simple_scheduler import MinistryAssignment, NotificationGenerator, GoogleSheetsExtractor
import sys
from unittest.mock import Mock

def create_mock_extractor():
    """创建模拟的数据提取器"""
    extractor = Mock(spec=GoogleSheetsExtractor)
    
    # 模拟本周主日安排 (假设今天是周三，这周日是1/14)
    current_week_assignment = MinistryAssignment(
        date=date(2024, 1, 14),
        audio_tech="张三",
        screen_operator="李四",
        camera_operator="王五",
        propresenter="赵六",
        video_editor="靖铮"
    )
    
    # 模拟下周主日安排 (1/21)
    next_week_assignment = MinistryAssignment(
        date=date(2024, 1, 21),
        audio_tech="钱七",
        screen_operator="孙八",
        camera_operator="周九",
        propresenter="吴十",
        video_editor="靖铮"
    )
    
    # 模拟月度安排
    monthly_assignments = [
        MinistryAssignment(
            date=date(2024, 1, 7),
            audio_tech="甲",
            screen_operator="乙",
            camera_operator="丙",
            propresenter="丁"
        ),
        current_week_assignment,
        next_week_assignment,
        MinistryAssignment(
            date=date(2024, 1, 28),
            audio_tech="戊",
            screen_operator="己",
            camera_operator="庚",
            propresenter="辛"
        )
    ]
    
    # 设置模拟方法
    extractor.get_current_week_assignment.return_value = current_week_assignment
    extractor.get_next_sunday_assignment.return_value = next_week_assignment
    extractor.get_monthly_assignments.return_value = monthly_assignments
    extractor.spreadsheet_id = "test_spreadsheet_id_123456"
    
    return extractor

def test_templates():
    """测试所有模板生成"""
    print("🧪 测试模板生成功能")
    print("=" * 50)
    
    # 创建模拟提取器
    mock_extractor = create_mock_extractor()
    
    # 创建通知生成器
    generator = NotificationGenerator(mock_extractor)
    
    try:
        print("\n📅 【测试周三确认通知】")
        print("-" * 30)
        weekly_notification = generator.generate_weekly_confirmation()
        print(weekly_notification)
        
        # 验证关键内容
        assert "张三" in weekly_notification
        assert "李四" in weekly_notification
        assert "王五" in weekly_notification
        assert "赵六" in weekly_notification
        assert "靖铮" in weekly_notification
        assert "1月14日" in weekly_notification
        print("✅ 周三通知测试通过")
        
        print("\n🔔 【测试周六提醒通知】")
        print("-" * 30)
        sunday_notification = generator.generate_sunday_reminder()
        print(sunday_notification)
        
        # 验证关键内容
        assert "钱七" in sunday_notification
        assert "孙八" in sunday_notification
        assert "周九" in sunday_notification
        assert "9:00到" in sunday_notification
        assert "9:30到" in sunday_notification
        print("✅ 周六通知测试通过")
        
        print("\n📊 【测试月度总览通知】")
        print("-" * 30)
        monthly_notification = generator.generate_monthly_overview(2024, 1)
        print(monthly_notification)
        
        # 验证关键内容
        assert "2024年01月" in monthly_notification
        assert "1/7:" in monthly_notification
        assert "1/14:" in monthly_notification
        assert "1/21:" in monthly_notification
        assert "1/28:" in monthly_notification
        assert "test_spreadsheet_id_123456" in monthly_notification
        print("✅ 月度通知测试通过")
        
        print("\n" + "=" * 50)
        print("✅ 所有模板测试通过！")
        
        return True
        
    except AssertionError as e:
        print(f"❌ 断言失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_structure():
    """测试数据结构"""
    print("\n🔧 测试数据结构")
    print("-" * 30)
    
    try:
        # 测试 MinistryAssignment
        assignment = MinistryAssignment(
            date=date(2024, 1, 14),
            audio_tech="测试音控",
            screen_operator="测试屏幕",
            camera_operator="测试摄像",
            propresenter="测试制作"
        )
        
        assert assignment.date == date(2024, 1, 14)
        assert assignment.audio_tech == "测试音控"
        assert assignment.video_editor == "靖铮"  # 默认值
        print("✅ MinistryAssignment 结构正确")
        
        # 测试空值处理
        empty_assignment = MinistryAssignment(
            date=date(2024, 1, 21),
            audio_tech="",
            screen_operator="",
            camera_operator="",
            propresenter=""
        )
        
        assert empty_assignment.audio_tech == ""
        print("✅ 空值处理正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Grace Irvine Ministry Scheduler - 简单测试")
    print("=" * 60)
    
    # 运行测试
    tests_passed = 0
    total_tests = 2
    
    if test_data_structure():
        tests_passed += 1
    
    if test_templates():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！代码实现正确。")
        print("\n📋 下一步:")
        print("1. 设置 Google Sheets API 认证")
        print("2. 配置 .env 文件")
        print("3. 运行 check_data.py 验证真实数据")
        print("4. 使用 generate_notifications.py 生成通知")
        return True
    else:
        print("❌ 部分测试失败，请检查代码实现。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
