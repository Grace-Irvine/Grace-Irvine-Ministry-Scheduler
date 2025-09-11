#!/usr/bin/env python3
"""
修复ICS模板一致性问题
Fix ICS template consistency issues
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_unified_template_functions():
    """创建统一的模板生成函数"""
    
    unified_template_code = '''
def generate_unified_wednesday_template(sunday_date, schedule):
    """统一的周三确认通知模板生成器"""
    template = f"""【本周{sunday_date.month}月{sunday_date.day}日主日事工安排提醒】🕊️

"""
    
    assignments = schedule.get_all_assignments() if schedule else {}
    
    if assignments:
        for role, person in assignments.items():
            template += f"• {role}：{person}\\n"
    else:
        template += "• 音控：待安排\\n• 导播/摄影：待安排\\n• ProPresenter播放：待安排\\n• ProPresenter更新：待安排\\n"
    
    template += """• 视频剪辑：靖铮

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"""
    
    return template

def generate_unified_saturday_template(sunday_date, schedule):
    """统一的周六提醒通知模板生成器"""
    template = f"""【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  

"""
    
    assignments = schedule.get_all_assignments() if schedule else {}
    
    if assignments.get('音控'):
        template += f"- 音控：{assignments['音控']} 9:00到，随敬拜团排练\\n"
    else:
        template += "- 音控：待确认 9:00到，随敬拜团排练\\n"
    
    if assignments.get('导播/摄影'):
        template += f"- 导播/摄影: {assignments['导播/摄影']} 9:30到，检查预设机位\\n"
    else:
        template += "- 导播/摄影: 待确认 9:30到，检查预设机位\\n"
    
    if assignments.get('ProPresenter播放'):
        template += f"- ProPresenter播放：{assignments['ProPresenter播放']} 9:00到，随敬拜团排练\\n"
    else:
        template += "- ProPresenter播放：待确认 9:00到，随敬拜团排练\\n"
    
    template += "\\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌"
    
    return template
'''
    
    return unified_template_code

def update_generate_real_calendars():
    """更新generate_real_calendars.py文件以使用统一模板"""
    
    file_path = PROJECT_ROOT / "generate_real_calendars.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加统一模板函数
        unified_functions = create_unified_template_functions()
        
        # 在导入部分后添加统一函数
        import_end = content.find("from dotenv import load_dotenv")
        if import_end != -1:
            import_end = content.find("\n", import_end) + 1
            content = content[:import_end] + "\n" + unified_functions + "\n" + content[import_end:]
        
        # 替换notification_content生成逻辑
        old_wednesday_logic = '''notification_content = template_manager.render_weekly_confirmation(assignment)'''
        new_wednesday_logic = '''notification_content = generate_unified_wednesday_template(schedule.date, schedule)'''
        
        old_saturday_logic = '''notification_content = template_manager.render_sunday_reminder(assignment)'''
        new_saturday_logic = '''notification_content = generate_unified_saturday_template(schedule.date, schedule)'''
        
        content = content.replace(old_wednesday_logic, new_wednesday_logic)
        content = content.replace(old_saturday_logic, new_saturday_logic)
        
        # 保存修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新 {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 更新 {file_path} 失败: {e}")
        return False

def update_streamlit_app():
    """更新streamlit_app.py中的ICS生成逻辑"""
    
    file_path = PROJECT_ROOT / "streamlit_app.py"
    
    if not file_path.exists():
        print(f"⚠️ {file_path} 不存在，跳过更新")
        return True
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换ICS生成中的模板逻辑
        old_pattern = '''notification_content = template_manager.render_weekly_confirmation(assignment)'''
        new_pattern = '''# 使用与前端一致的模板生成逻辑
                    from app_unified import generate_wednesday_template
                    notification_content = generate_wednesday_template(schedule.date, schedule)'''
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            
            # 同样处理周六模板
            old_saturday = '''notification_content = template_manager.render_sunday_reminder(assignment)'''
            new_saturday = '''# 使用与前端一致的模板生成逻辑
                    from app_unified import generate_saturday_template
                    notification_content = generate_saturday_template(schedule.date, schedule)'''
            
            content = content.replace(old_saturday, new_saturday)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已更新 {file_path}")
        else:
            print(f"ℹ️ {file_path} 中未找到需要更新的模式")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新 {file_path} 失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 修复ICS模板一致性问题")
    print("=" * 50)
    
    success_count = 0
    
    # 更新generate_real_calendars.py
    if update_generate_real_calendars():
        success_count += 1
    
    # 更新streamlit_app.py（如果存在）
    if update_streamlit_app():
        success_count += 1
    
    print(f"\n📊 更新结果: {success_count}/2 个文件更新完成")
    
    if success_count >= 1:
        print("✅ 模板一致性修复完成！")
        print("\n🔄 建议操作:")
        print("1. 重新生成ICS日历文件")
        print("2. 使用Web界面查看ICS事件内容")
        print("3. 对比前端模板和ICS事件描述的一致性")
    else:
        print("❌ 修复失败，请检查错误信息")

if __name__ == "__main__":
    main()
