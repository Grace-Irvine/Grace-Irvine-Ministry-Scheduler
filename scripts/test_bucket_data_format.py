#!/usr/bin/env python3
"""
测试bucket数据格式，检查数据是否正确读取和处理
"""

import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.json_data_reader import get_json_data_reader
from src.multi_calendar_generator import extract_person_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("📊 测试bucket数据格式")
    print("=" * 60)
    
    reader = get_json_data_reader()
    schedules = reader.get_service_schedule()
    
    if not schedules:
        print("❌ 未找到数据")
        return
    
    print(f"\n✅ 找到 {len(schedules)} 条数据\n")
    
    for i, schedule in enumerate(schedules[:3], 1):
        print(f"数据 {i}:")
        print(f"  日期: {schedule.get('date')}")
        
        volunteers = schedule.get('volunteers', {})
        media = volunteers.get('technical') or volunteers.get('media', {})
        
        if not media:
            print("  ⚠️  没有媒体部数据")
            continue
        
        print(f"  媒体部原始数据: {media}")
        print(f"  数据类型: {type(media)}")
        
        for key in ['audio', 'video', 'propresenter_play', 'propresenter_update']:
            value = media.get(key)
            if value is not None:
                print(f"\n  {key}:")
                print(f"    类型: {type(value).__name__}")
                print(f"    值: {repr(value)}")
                
                if isinstance(value, dict):
                    print(f"    字典内容: {value}")
                    print(f"    是否有name字段: {'name' in value}")
                    if 'name' in value:
                        print(f"    name值: {repr(value.get('name'))}")
                
                # 测试提取
                extracted = extract_person_name(value)
                print(f"    提取结果: {repr(extracted)}")
                
                if not extracted:
                    print(f"    ⚠️  提取结果为空！")
                    if isinstance(value, str):
                        print(f"    字符串值 '{value}' 被识别为占位符文本")
                    elif isinstance(value, dict):
                        print(f"    字典格式可能没有正确提取name字段")
        
        print()

if __name__ == "__main__":
    main()

