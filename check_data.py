#!/usr/bin/env python3
"""
数据验证脚本 - 检查 Google Sheets 数据格式和连接

用法:
  python check_data.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from simple_scheduler import GoogleSheetsExtractor
from dotenv import load_dotenv

def main():
    print("🔍 Grace Irvine Ministry Scheduler - 数据验证")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查环境变量
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    if not spreadsheet_id:
        print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
        return False
    
    print(f"📊 Spreadsheet ID: {spreadsheet_id}")
    
    # 检查服务账号文件
    service_account_path = "configs/service_account.json"
    if not Path(service_account_path).exists():
        print(f"❌ 错误: 服务账号文件不存在: {service_account_path}")
        print("请按照 SIMPLE_SETUP.md 的指示设置 Google Cloud 服务账号")
        return False
    
    print(f"🔑 服务账号文件: ✅ 存在")
    
    try:
        # 测试连接
        print("\n🔗 正在测试 Google Sheets 连接...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        print("✅ Google Sheets 连接成功!")
        
        # 获取原始数据
        print("\n📋 正在检查数据格式...")
        raw_data = extractor.get_raw_data()
        
        if not raw_data:
            print("❌ 错误: 表格为空")
            return False
        
        print(f"📊 表格行数: {len(raw_data)} (包含标题行)")
        
        # 显示标题行
        if len(raw_data) > 0:
            headers = raw_data[0]
            print(f"📝 标题行 ({len(headers)} 列):")
            for i, header in enumerate(headers[:10]):  # 只显示前10列
                print(f"    {chr(65+i)}列: {header}")
            if len(headers) > 10:
                print(f"    ... 还有 {len(headers)-10} 列")
        
        # 显示前几行数据示例
        print("\n📋 数据示例 (前3行):")
        for i, row in enumerate(raw_data[1:4], 1):  # 跳过标题行
            print(f"  第{i}行:")
            for j, cell in enumerate(row[:5]):  # 只显示前5列
                print(f"    {chr(65+j)}列: {cell}")
            print()
        
        # 解析事工数据
        print("🔄 正在解析事工数据...")
        assignments = extractor.parse_ministry_data()
        
        if not assignments:
            print("⚠️  警告: 未找到有效的事工安排数据")
            print("请检查:")
            print("  1. 日期格式是否正确 (例如: 2024/1/14)")
            print("  2. 是否有实际的人员安排")
            print("  3. 列位置是否对应正确")
            return False
        
        print(f"✅ 成功解析 {len(assignments)} 条事工安排")
        
        # 显示解析结果统计
        print("\n📊 数据统计:")
        
        # 按日期统计
        dates = [a.date for a in assignments]
        if dates:
            print(f"  📅 日期范围: {min(dates)} 到 {max(dates)}")
        
        # 统计各角色的安排数量
        role_counts = {
            "音控": sum(1 for a in assignments if a.audio_tech),
            "屏幕": sum(1 for a in assignments if a.screen_operator),
            "摄像/导播": sum(1 for a in assignments if a.camera_operator),
            "Propresenter": sum(1 for a in assignments if a.propresenter)
        }
        
        print("  👥 角色安排统计:")
        for role, count in role_counts.items():
            print(f"    {role}: {count} 次")
        
        # 显示最近的几个安排
        print("\n📋 最近的事工安排:")
        today = date.today()
        upcoming = [a for a in assignments if a.date >= today][:3]
        
        if upcoming:
            for assignment in upcoming:
                print(f"  📅 {assignment.date}:")
                if assignment.audio_tech:
                    print(f"    🎵 音控: {assignment.audio_tech}")
                if assignment.screen_operator:
                    print(f"    📺 屏幕: {assignment.screen_operator}")
                if assignment.camera_operator:
                    print(f"    📹 摄像/导播: {assignment.camera_operator}")
                if assignment.propresenter:
                    print(f"    💻 Propresenter: {assignment.propresenter}")
                print()
        else:
            print("  ⚠️  未找到今天之后的安排")
        
        # 检查常见问题
        print("🔍 数据质量检查:")
        
        issues = []
        
        # 检查空白安排
        empty_assignments = [a for a in assignments if not any([
            a.audio_tech, a.screen_operator, a.camera_operator, a.propresenter
        ])]
        if empty_assignments:
            issues.append(f"发现 {len(empty_assignments)} 个完全空白的安排")
        
        # 检查日期连续性 (周日)
        sundays = [a.date for a in assignments if a.date.weekday() == 6]  # 6 = 周日
        if sundays:
            expected_sundays = []
            start = min(sundays)
            end = max(sundays)
            current = start
            while current <= end:
                if current.weekday() == 6:
                    expected_sundays.append(current)
                current = date.fromordinal(current.toordinal() + 1)
            
            missing_sundays = set(expected_sundays) - set(sundays)
            if missing_sundays:
                issues.append(f"缺少 {len(missing_sundays)} 个周日的安排")
        
        if issues:
            print("  ⚠️  发现的问题:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  ✅ 数据质量良好")
        
        print("\n" + "=" * 50)
        print("✅ 数据验证完成!")
        print("\n📋 下一步:")
        print("1. 如果数据看起来正确，可以运行 generate_notifications.py")
        print("2. 如果有问题，请检查 Google Sheets 的数据格式")
        print("3. 确保列的位置与代码中的映射一致")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
