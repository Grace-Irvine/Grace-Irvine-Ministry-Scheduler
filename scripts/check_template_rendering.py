#!/usr/bin/env python3
"""
检查模板渲染逻辑
分析为什么会显示"待安排"以及如何改进
"""

import sys
import os
from pathlib import Path
from datetime import date

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.scheduler import GoogleSheetsExtractor
from src.template_manager import get_default_template_manager
from dotenv import load_dotenv

def main():
    """主函数"""
    print("🔍 模板渲染逻辑检查")
    print("=" * 60)
    
    try:
        # 设置环境
        load_dotenv()
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        
        if not spreadsheet_id:
            print("❌ 错误: 请在 .env 文件中设置 GOOGLE_SPREADSHEET_ID")
            return
        
        # 获取数据
        print("📊 正在获取数据...")
        extractor = GoogleSheetsExtractor(spreadsheet_id)
        assignments = extractor.parse_ministry_data()
        template_manager = get_default_template_manager()
        
        # 找到最近的一个未来安排
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today]
        
        if not future_assignments:
            print("❌ 未找到未来的事工安排")
            return
        
        assignment = future_assignments[0]
        
        print(f"📋 分析事工安排: {assignment.date}")
        print("=" * 60)
        
        # 显示原始数据
        print("🔍 原始数据:")
        print(f"  音控: '{assignment.audio_tech}'")
        print(f"  屏幕: '{assignment.screen_operator}'")
        print(f"  摄像/导播: '{assignment.camera_operator}'")
        print(f"  ProPresenter: '{assignment.propresenter}'")
        print(f"  视频剪辑: '{assignment.video_editor}'")
        
        # 显示模板默认值
        print("\n🔧 模板默认值:")
        defaults = template_manager.get_defaults('weekly_confirmation')
        for key, value in defaults.items():
            print(f"  {key}: '{value}'")
        
        # 显示渲染过程
        print("\n⚙️ 渲染过程分析:")
        template_vars = {
            'month': assignment.date.month,
            'day': assignment.date.day,
            'audio_tech': assignment.audio_tech or defaults.get('audio_tech', '待安排'),
            'screen_operator': assignment.screen_operator or defaults.get('screen_operator', '待安排'),
            'camera_operator': assignment.camera_operator or defaults.get('camera_operator', '待安排'),
            'propresenter': assignment.propresenter or defaults.get('propresenter', '待安排'),
            'video_editor': assignment.video_editor or defaults.get('video_editor', '靖铮')
        }
        
        for key, value in template_vars.items():
            if key not in ['month', 'day']:
                original = getattr(assignment, key, '')
                print(f"  {key}: '{original}' → '{value}'")
        
        # 显示当前渲染结果
        print("\n📝 当前渲染结果:")
        print("-" * 40)
        current_result = template_manager.render_weekly_confirmation(assignment)
        print(current_result)
        
        # 提供改进建议
        print("\n💡 改进建议:")
        print("-" * 40)
        print("1. 如果希望隐藏空角色，可以修改模板逻辑")
        print("2. 如果希望显示'暂无安排'而不是'待安排'，可以修改默认值")
        print("3. 如果希望完全不显示某些角色，可以在模板中添加条件判断")
        
        # 演示改进版本
        print("\n🔧 改进版本演示（隐藏空角色）:")
        print("-" * 40)
        
        improved_content = f"【本周{assignment.date.month}月{assignment.date.day}日主日事工安排提醒】🕊️\n\n"
        
        if assignment.audio_tech:
            improved_content += f"• 音控：{assignment.audio_tech}\n"
        if assignment.screen_operator:
            improved_content += f"• 屏幕：{assignment.screen_operator}\n"
        if assignment.camera_operator:
            improved_content += f"• 摄像/导播：{assignment.camera_operator}\n"
        if assignment.propresenter:
            improved_content += f"• Propresenter 制作：{assignment.propresenter}\n"
        if assignment.video_editor:
            improved_content += f"• 视频剪辑：{assignment.video_editor}\n"
        
        improved_content += "\n请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"
        
        print(improved_content)
        
        # 检查Google Sheets中是否真的没有屏幕操作员数据
        print("\n🔍 Google Sheets数据验证:")
        print("-" * 40)
        raw_data = extractor.get_raw_data()
        
        # 找到对应日期的行
        target_date_str = assignment.date.strftime("%m/%d/%Y")
        for i, row in enumerate(raw_data[1:], start=2):  # 跳过标题行
            if len(row) > 0 and target_date_str in str(row[0]):
                print(f"找到对应行 {i}: {row[0]}")
                
                # 检查各列的内容
                columns = ['Q', 'R', 'S', 'T', 'U']
                roles = ['音控', '导播', '导播/摄影', 'ProPresenter播放', 'ProPresenter更新']
                
                for col, role in zip(columns, roles):
                    col_idx = ord(col) - ord('A')
                    content = row[col_idx] if col_idx < len(row) else '(超出范围)'
                    print(f"  {col}列 ({role}): '{content}'")
                break
        else:
            print(f"未找到日期 {target_date_str} 的对应行")
        
    except Exception as e:
        print(f"❌ 检查过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
