#!/usr/bin/env python3
"""
调试 ICS 数据读取和处理
检查数据是否正确从 bucket 读取，以及人名提取是否正确
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.json_data_reader import get_json_data_reader
from src.multi_calendar_generator import extract_person_name, is_placeholder_text

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_data_reading():
    """测试数据读取"""
    print("=" * 60)
    print("📊 测试数据读取")
    print("=" * 60)
    
    try:
        reader = get_json_data_reader()
        
        # 读取服事安排数据
        print("\n1. 读取服事安排数据...")
        schedules = reader.get_service_schedule()
        print(f"   ✅ 找到 {len(schedules)} 条服事安排")
        
        if not schedules:
            print("   ❌ 未找到数据，请检查 bucket 连接")
            return False
        
        # 显示前3条数据的详细信息
        print("\n2. 显示前3条数据详情:")
        for i, schedule in enumerate(schedules[:3], 1):
            print(f"\n   数据 {i}:")
            print(f"   日期: {schedule.get('date')}")
            
            # 显示证道信息
            sermon = schedule.get('sermon', {})
            if sermon:
                print(f"   证道: {sermon.get('title', 'N/A')} - {sermon.get('speaker', 'N/A')}")
            
            # 显示媒体部信息
            volunteers = schedule.get('volunteers', {})
            media = volunteers.get('technical') or volunteers.get('media', {})
            
            if media:
                print(f"   媒体部数据:")
                print(f"     类型: {type(media)}")
                print(f"     内容: {media}")
                
                # 检查每个字段的类型和值
                for role_key in ['audio', 'audio_tech', 'sound_control', 'video', 'video_director', 'director', 'propresenter_play', 'propresenter_update']:
                    role_value = media.get(role_key)
                    if role_value is not None:
                        print(f"     {role_key}:")
                        print(f"       类型: {type(role_value)}")
                        print(f"       值: {repr(role_value)}")
                        
                        # 测试人名提取
                        extracted = extract_person_name(role_value)
                        is_placeholder = is_placeholder_text(str(role_value)) if isinstance(role_value, str) else False
                        print(f"       提取结果: '{extracted}'")
                        print(f"       是否占位符: {is_placeholder}")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_person_name_extraction():
    """测试人名提取函数"""
    print("=" * 60)
    print("🧪 测试人名提取函数")
    print("=" * 60)
    
    test_cases = [
        # (输入值, 期望结果, 描述)
        ("张三", "张三", "正常人名"),
        ("音控人员", "", "占位符文本"),
        ("导播/摄影", "", "占位符文本"),
        ({"id": "xxx", "name": "李四"}, "李四", "字典格式"),
        ({"id": "xxx", "name": "音控人员"}, "", "字典格式占位符"),
        ({"name": "王五"}, "王五", "字典格式（只有name）"),
        (["张三", "李四"], "张三", "列表格式"),
        ([{"id": "xxx", "name": "赵六"}], "赵六", "列表包含字典"),
        ("", "", "空字符串"),
        (None, "", "None值"),
    ]
    
    print("\n测试用例:")
    for i, (input_value, expected, description) in enumerate(test_cases, 1):
        result = extract_person_name(input_value)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {i}. {description}")
        print(f"     输入: {repr(input_value)}")
        print(f"     期望: '{expected}'")
        print(f"     结果: '{result}'")
        if result != expected:
            print(f"     ⚠️  不匹配！")
        print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔍 ICS 数据读取和处理调试工具")
    print("=" * 60)
    
    # 测试人名提取函数
    test_person_name_extraction()
    
    # 测试数据读取
    test_data_reading()
    
    print("\n" + "=" * 60)
    print("✅ 调试完成")
    print("=" * 60)

