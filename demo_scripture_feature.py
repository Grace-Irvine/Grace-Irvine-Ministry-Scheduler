#!/usr/bin/env python3
"""
经文分享功能演示脚本
Scripture Sharing Feature Demo

快速演示经文分享功能的使用
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def demo():
    print("🎬 Grace Irvine Ministry Scheduler - 经文分享功能演示")
    print("=" * 60)
    print()
    
    # 1. 展示当前经文库
    print("📚 当前经文库内容:")
    print("-" * 30)
    
    from src.scripture_manager import get_scripture_manager
    scripture_manager = get_scripture_manager()
    
    scriptures = scripture_manager.get_all_scriptures()
    for i, scripture in enumerate(scriptures, 1):
        content = scripture.get('content', '')
        first_line = content.split('\n')[0] if content else 'Unknown'
        print(f"{i:2d}. 📖 {first_line}")
        if len(content.split('\n')) > 1:
            last_line = content.split('\n')[-1]
            print(f"    {last_line}")
    
    print(f"\n📊 统计: 共 {len(scriptures)} 段经文")
    
    # 2. 演示模板生成
    print("\n" + "=" * 60)
    print("📧 演示：生成包含经文的周三通知")
    print("-" * 30)
    
    from src.dynamic_template_manager import get_dynamic_template_manager
    from src.models import MinistryAssignment
    
    template_manager = get_dynamic_template_manager()
    
    # 创建示例数据
    test_date = date.today() + timedelta(days=7)
    test_schedule = MinistryAssignment(
        date=test_date,
        audio_tech="Jimmy",
        video_director="靖铮",
        propresenter_play="张宇",
        propresenter_update="Daniel"
    )
    
    # 生成通知
    notification = template_manager.render_weekly_confirmation(test_date, test_schedule)
    
    print("生成的通知内容：")
    print("┌" + "─" * 58 + "┐")
    for line in notification.split('\n'):
        print(f"│ {line:<56} │")
    print("└" + "─" * 58 + "┘")
    
    # 3. 演示经文轮换
    print("\n" + "=" * 60)
    print("🔄 演示：经文自动轮换")
    print("-" * 30)
    
    print("连续生成3次通知，观察经文变化：")
    
    for i in range(3):
        print(f"\n第 {i+1} 次生成:")
        
        # 生成新通知
        notification = template_manager.render_weekly_confirmation(test_date, test_schedule)
        
        # 提取经文部分
        lines = notification.split('\n')
        scripture_lines = []
        capture = False
        
        for line in lines:
            if line.startswith('📖'):
                capture = True
            if capture:
                scripture_lines.append(line)
            if line.startswith('💡') and capture:
                break
        
        for line in scripture_lines:
            print(f"  {line}")
    
    # 4. 演示管理功能
    print("\n" + "=" * 60)
    print("🛠️ 演示：经文管理功能")
    print("-" * 30)
    
    # 获取当前状态
    stats = scripture_manager.get_scripture_stats()
    print(f"📍 当前位置: 第 {stats.get('current_index', 0) + 1} 段")
    print(f"📚 经文总数: {stats.get('total_count', 0)}")
    
    # 显示当前经文
    current = scripture_manager.get_current_scripture()
    if current:
        content = current.get('content', '')
        first_line = content.split('\n')[0] if content else 'Unknown'
        print(f"📖 当前经文: {first_line}")
        if len(content.split('\n')) > 1:
            last_line = content.split('\n')[-1]
            print(f"📍 出处: {last_line}")
    
    # 5. 快速入门指南
    print("\n" + "=" * 60)
    print("🚀 快速入门")
    print("-" * 30)
    
    print("1. 启动Streamlit应用:")
    print("   python3 -m streamlit run app_unified.py")
    print()
    print("2. 在侧边栏选择 '📖 经文管理'")
    print()
    print("3. 使用各个标签页:")
    print("   • 📝 经文列表: 查看和管理现有经文")
    print("   • ➕ 添加经文: 添加新的经文内容") 
    print("   • 🔧 编辑经文: 修改现有经文")
    print("   • 📊 使用预览: 预览经文使用效果")
    print()
    print("4. 生成通知时经文会自动包含")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成！经文分享功能已成功集成。")
    print("📖 详细使用说明请参阅 SCRIPTURE_SHARING_GUIDE.md")

if __name__ == "__main__":
    demo()
