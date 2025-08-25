#!/usr/bin/env python3
"""
模板修改工具

这个脚本帮助您快速修改通知模板，无需直接编辑 simple_scheduler.py
"""

import re
import shutil
from pathlib import Path

def backup_original():
    """备份原始文件"""
    source = Path("simple_scheduler.py")
    backup = Path("simple_scheduler.py.backup")
    
    if source.exists():
        shutil.copy2(source, backup)
        print(f"✅ 已备份原文件到: {backup}")
        return True
    else:
        print("❌ 找不到 simple_scheduler.py 文件")
        return False

def modify_weekly_template(new_template):
    """修改周三确认通知模板"""
    file_path = Path("simple_scheduler.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换周三模板
    pattern = r'(def generate_weekly_confirmation.*?template = f""")(.*?)("""\s*return template)'
    
    def replace_func(match):
        return match.group(1) + new_template + match.group(3)
    
    new_content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 周三确认通知模板已更新")

def modify_sunday_template(new_template):
    """修改周六提醒通知模板"""
    file_path = Path("simple_scheduler.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'(def generate_sunday_reminder.*?template = f""")(.*?)("""\s*return template)'
    
    def replace_func(match):
        return match.group(1) + new_template + match.group(3)
    
    new_content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 周六提醒通知模板已更新")

def modify_monthly_template(new_template):
    """修改月度总览通知模板"""
    file_path = Path("simple_scheduler.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 月度模板比较复杂，需要保留前面的逻辑
    pattern = r'(# 获取 Google Sheets 链接.*?template = f""")(.*?)("""\s*return template)'
    
    def replace_func(match):
        return match.group(1) + new_template + match.group(3)
    
    new_content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 月度总览通知模板已更新")

def interactive_mode():
    """交互式模板修改"""
    print("🎨 通知模板修改工具")
    print("=" * 40)
    
    if not backup_original():
        return
    
    while True:
        print("\n请选择要修改的模板：")
        print("1. 周三确认通知")
        print("2. 周六提醒通知")
        print("3. 月度总览通知")
        print("4. 查看示例模板")
        print("5. 恢复备份")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-5): ").strip()
        
        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            modify_weekly_interactive()
        elif choice == "2":
            modify_sunday_interactive()
        elif choice == "3":
            modify_monthly_interactive()
        elif choice == "4":
            show_examples()
        elif choice == "5":
            restore_backup()
        else:
            print("❌ 无效选择，请重试")

def modify_weekly_interactive():
    """交互式修改周三通知"""
    print("\n🔧 修改周三确认通知模板")
    print("-" * 30)
    print("当前模板变量可用：")
    print("- {month} : 月份")
    print("- {day} : 日期")
    print("- {assignment.audio_tech} : 音控人员")
    print("- {assignment.screen_operator} : 屏幕操作员")
    print("- {assignment.camera_operator} : 摄像/导播")
    print("- {assignment.propresenter} : Propresenter制作")
    print("- {assignment.video_editor} : 视频剪辑")
    
    print("\n请输入新的模板内容（多行输入，输入 'END' 结束）：")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    
    new_template = "\\n".join(lines)
    
    print("\n预览新模板：")
    print("-" * 20)
    print(new_template.replace("\\n", "\n"))
    print("-" * 20)
    
    confirm = input("\n确认应用此模板？(y/N): ").strip().lower()
    if confirm == 'y':
        modify_weekly_template(new_template)
        print("✅ 模板已更新！建议运行测试：python3 test_simple.py")
    else:
        print("❌ 取消修改")

def modify_sunday_interactive():
    """交互式修改周六通知"""
    print("\n🔧 修改周六提醒通知模板")
    print("-" * 30)
    print("请输入新的模板内容（多行输入，输入 'END' 结束）：")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    
    new_template = "\\n".join(lines)
    
    print("\n预览新模板：")
    print("-" * 20)
    print(new_template.replace("\\n", "\n"))
    print("-" * 20)
    
    confirm = input("\n确认应用此模板？(y/N): ").strip().lower()
    if confirm == 'y':
        modify_sunday_template(new_template)
        print("✅ 模板已更新！")
    else:
        print("❌ 取消修改")

def modify_monthly_interactive():
    """交互式修改月度通知"""
    print("\n🔧 修改月度总览通知模板")
    print("-" * 30)
    print("注意：月度模板使用以下变量：")
    print("- {year} : 年份")
    print("- {month:02d} : 月份（两位数）")
    print("- {sheet_url} : Google Sheets链接")
    print("- {schedule_text} : 格式化的安排文本")
    
    print("\n请输入新的模板内容（多行输入，输入 'END' 结束）：")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    
    new_template = "\\n".join(lines)
    
    print("\n预览新模板：")
    print("-" * 20)
    print(new_template.replace("\\n", "\n"))
    print("-" * 20)
    
    confirm = input("\n确认应用此模板？(y/N): ").strip().lower()
    if confirm == 'y':
        modify_monthly_template(new_template)
        print("✅ 模板已更新！")
    else:
        print("❌ 取消修改")

def show_examples():
    """显示示例模板"""
    print("\n📋 示例模板")
    print("=" * 40)
    print("运行以下命令查看详细示例：")
    print("python3 template_examples.py")
    print("\n也可以查看文档：")
    print("- TEMPLATE_CUSTOMIZATION.md")

def restore_backup():
    """恢复备份"""
    backup = Path("simple_scheduler.py.backup")
    original = Path("simple_scheduler.py")
    
    if backup.exists():
        shutil.copy2(backup, original)
        print("✅ 已恢复到备份版本")
    else:
        print("❌ 未找到备份文件")

def quick_apply_template(template_name):
    """快速应用预设模板"""
    templates = {
        "simple_weekly": """【{month}/{day} 主日事工】🕊️

音控:{assignment.audio_tech or 'TBD'} | 屏幕:{assignment.screen_operator or 'TBD'}
摄像:{assignment.camera_operator or 'TBD'} | 制作:{assignment.propresenter or 'TBD'}
剪辑:{assignment.video_editor}

有冲突请私信 🙏""",
        
        "formal_weekly": """🎵【恩典尔湾长老教会】🎵
═══════════════════════════

📅 {assignment.date.year}年{month}月{day}日主日事工安排

👥 服事团队：
🎤 音控：{assignment.audio_tech or '❌待安排'}
📺 屏幕：{assignment.screen_operator or '❌待安排'}  
📹 摄像/导播：{assignment.camera_operator or '❌待安排'}
💻 Propresenter：{assignment.propresenter or '❌待安排'}
✂️ 视频剪辑：{assignment.video_editor}

⏰ 重要时间：
• 周三晚 8:00 - 最终确认截止
• 主日上午 9:00 - 同工到场时间
• 主日上午 10:00 - 正式敬拜

请大家及时确认，若有冲突请尽快私信协调
感谢各位忠心的服事！🙏✨

═══════════════════════════"""
    }
    
    if template_name in templates:
        if not backup_original():
            return
        
        modify_weekly_template(templates[template_name])
        print(f"✅ 已应用 {template_name} 模板")
    else:
        print(f"❌ 未找到模板: {template_name}")
        print("可用模板:", list(templates.keys()))

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 命令行模式
        command = sys.argv[1]
        if command == "backup":
            backup_original()
        elif command == "restore":
            restore_backup()
        elif command == "apply" and len(sys.argv) > 2:
            quick_apply_template(sys.argv[2])
        else:
            print("用法:")
            print("python3 modify_template.py backup    # 备份原文件")
            print("python3 modify_template.py restore   # 恢复备份")
            print("python3 modify_template.py apply simple_weekly  # 应用简洁模板")
            print("python3 modify_template.py apply formal_weekly  # 应用正式模板")
    else:
        # 交互式模式
        interactive_mode()
