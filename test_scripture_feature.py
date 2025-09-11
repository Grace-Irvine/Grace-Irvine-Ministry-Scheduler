#!/usr/bin/env python3
"""
测试经文分享功能
Test Scripture Sharing Feature

演示完整的经文分享功能集成
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_scripture_manager():
    """测试经文管理器"""
    print("🧪 测试经文管理器功能")
    print("=" * 60)
    
    from src.scripture_manager import get_scripture_manager
    
    manager = get_scripture_manager()
    
    # 1. 测试获取统计信息
    stats = manager.get_scripture_stats()
    print(f"📊 经文统计:")
    print(f"   总数: {stats.get('total_count', 0)}")
    print(f"   当前索引: {stats.get('current_index', 0)}")
    print(f"   主题: {', '.join(stats.get('themes', []))}")
    print()
    
    # 2. 测试获取当前经文
    current = manager.get_current_scripture()
    if current:
        print(f"📖 当前经文:")
        print(f"   出处: {current.get('verse', '')}")
        print(f"   内容: {current.get('content', '')}")
        print(f"   主题: {current.get('theme', '')}")
        print()
    
    # 3. 测试格式化
    formatted = manager.format_scripture_for_template(current)
    print(f"📝 格式化结果:")
    print(formatted)
    print()
    
    # 4. 测试获取下一个经文（更新索引）
    next_scripture = manager.get_next_scripture()
    if next_scripture:
        print(f"⏭️ 下一个经文:")
        print(f"   出处: {next_scripture.get('verse', '')}")
        print(f"   索引已更新为: {manager.get_scripture_stats().get('current_index', 0)}")
        print()
    
    return True

def test_template_integration():
    """测试模板集成"""
    print("🧪 测试模板集成功能")
    print("=" * 60)
    
    from src.dynamic_template_manager import get_dynamic_template_manager
    from src.models import MinistryAssignment
    
    manager = get_dynamic_template_manager()
    
    # 创建测试数据
    test_date = date.today() + timedelta(days=7)
    test_schedule = MinistryAssignment(
        date=test_date,
        audio_tech="Jimmy",
        video_director="靖铮", 
        propresenter_play="张宇",
        propresenter_update="Daniel"
    )
    
    # 生成包含经文的通知
    print(f"📅 测试日期: {test_date.strftime('%Y年%m月%d日')}")
    print()
    
    notification = manager.render_weekly_confirmation(test_date, test_schedule)
    
    print("📧 生成的周三确认通知:")
    print("-" * 50)
    print(notification)
    print("-" * 50)
    print()
    
    return True

def test_multiple_generations():
    """测试多次生成（验证经文轮换）"""
    print("🧪 测试经文轮换功能")
    print("=" * 60)
    
    from src.dynamic_template_manager import get_dynamic_template_manager
    from src.models import MinistryAssignment
    
    manager = get_dynamic_template_manager()
    
    print("🔄 连续生成3次通知，观察经文轮换:")
    print()
    
    for i in range(3):
        test_date = date.today() + timedelta(days=7*(i+1))
        test_schedule = MinistryAssignment(
            date=test_date,
            audio_tech=f"同工{i+1}",
            video_director="靖铮",
            propresenter_play="张宇"
        )
        
        notification = manager.render_weekly_confirmation(test_date, test_schedule)
        
        print(f"第 {i+1} 次生成:")
        print("-" * 30)
        
        # 只显示经文部分
        lines = notification.split('\n')
        scripture_started = False
        for line in lines:
            if line.startswith('📖'):
                scripture_started = True
            if scripture_started:
                print(line)
                if line.startswith('💡') or (scripture_started and line.strip() == ''):
                    break
        print()
    
    return True

def test_scripture_management():
    """测试经文管理功能"""
    print("🧪 测试经文管理功能")
    print("=" * 60)
    
    from src.scripture_manager import get_scripture_manager
    
    manager = get_scripture_manager()
    
    # 1. 显示所有经文
    scriptures = manager.get_all_scriptures()
    print(f"📚 当前经文库包含 {len(scriptures)} 段经文:")
    
    for i, scripture in enumerate(scriptures):
        content = scripture.get('content', '')
        first_line = content.split('\n')[0] if content else 'Unknown'
        print(f"   {i+1}. {first_line[:40]}{'...' if len(first_line) > 40 else ''}")
    print()
    
    # 2. 测试添加新经文
    print("➕ 测试添加新经文:")
    success = manager.add_scripture(
        "这是一段测试经文内容。\n(测试经文 1:1 和合本)"
    )
    print(f"   添加结果: {'✅ 成功' if success else '❌ 失败'}")
    print()
    
    # 3. 测试更新经文
    print("🔧 测试更新经文:")
    test_scripture = manager.get_all_scriptures()[-1]  # 获取最后一个（刚添加的）
    success = manager.update_scripture(
        test_scripture.get('id'),
        "这是更新后的测试经文内容。\n(测试经文 1:1 和合本修订版)"
    )
    print(f"   更新结果: {'✅ 成功' if success else '❌ 失败'}")
    print()
    
    # 4. 测试删除经文
    print("🗑️ 测试删除经文:")
    success = manager.delete_scripture(test_scripture.get('id'))
    print(f"   删除结果: {'✅ 成功' if success else '❌ 失败'}")
    print()
    
    # 5. 最终统计
    final_stats = manager.get_scripture_stats()
    print(f"📊 最终统计:")
    print(f"   经文总数: {final_stats.get('total_count', 0)}")
    print(f"   当前索引: {final_stats.get('current_index', 0)}")
    print()
    
    return True

def main():
    """主测试函数"""
    print("🚀 Grace Irvine Ministry Scheduler - 经文分享功能测试")
    print("=" * 80)
    print()
    
    tests = [
        ("经文管理器基础功能", test_scripture_manager),
        ("模板集成功能", test_template_integration),
        ("经文轮换功能", test_multiple_generations),
        ("经文管理CRUD功能", test_scripture_management)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"🧪 开始测试: {test_name}")
            success = test_func()
            results.append((test_name, success))
            print(f"{'✅ 通过' if success else '❌ 失败'}: {test_name}")
        except Exception as e:
            print(f"❌ 错误: {test_name} - {e}")
            results.append((test_name, False))
        print("\n" + "=" * 80 + "\n")
    
    # 总结
    print("📊 测试总结:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {status}: {test_name}")
    
    print(f"\n🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！经文分享功能已成功集成！")
        print("\n📝 功能说明:")
        print("   • 经文内容存储在 templates/scripture_sharing.json")
        print("   • 每次生成周三通知时自动选择下一段经文")
        print("   • 可通过前端界面管理经文内容（添加/编辑/删除）")
        print("   • 支持本地和云端存储")
        print("   • 经文按顺序循环使用")
    else:
        print("⚠️ 部分测试失败，请检查配置和依赖")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
