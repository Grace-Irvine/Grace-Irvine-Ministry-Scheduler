#!/usr/bin/env python3
"""
检查数据源文件的数据结构
Check data structure in source files

查看 grace-irvine-ministry-data bucket 中文件的数据结构
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from google.cloud import storage
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_file_structure(bucket_name: str, file_path: str):
    """检查文件的数据结构
    
    Args:
        bucket_name: bucket 名称
        file_path: 文件路径
    """
    print("=" * 80)
    print(f"📄 检查文件: {file_path}")
    print("=" * 80)
    
    try:
        # 设置服务账号
        service_account_path = PROJECT_ROOT / "configs" / "service_account.json"
        if service_account_path.exists():
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)
        
        # 创建存储客户端
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        
        # 读取文件
        blob = bucket.blob(file_path)
        if not blob.exists():
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        content = blob.download_as_text(encoding='utf-8')
        data = json.loads(content)
        
        print(f"\n✅ 文件读取成功")
        print(f"📏 文件大小: {len(content)} 字节")
        print(f"📊 数据类型: {type(data).__name__}")
        
        if isinstance(data, dict):
            print(f"📋 顶层键: {list(data.keys())}")
            
            # 显示 metadata
            if 'metadata' in data:
                print(f"\n📊 Metadata:")
                metadata = data['metadata']
                if isinstance(metadata, dict):
                    for key, value in metadata.items():
                        print(f"   {key}: {value}")
            
            # 显示数据内容
            if 'sermons' in data:
                sermons = data['sermons']
                print(f"\n📖 证道数据:")
                print(f"   数量: {len(sermons) if isinstance(sermons, list) else 'N/A'}")
                if isinstance(sermons, list) and len(sermons) > 0:
                    print(f"   第一条数据键: {list(sermons[0].keys())}")
                    print(f"   第一条数据示例:")
                    first_item = sermons[0]
                    for key, value in list(first_item.items())[:10]:  # 显示前10个字段
                        if isinstance(value, (str, int, float, bool, type(None))):
                            value_str = str(value)[:50] if len(str(value)) > 50 else str(value)
                            print(f"      {key}: {value_str}")
            
            if 'volunteers' in data:
                volunteers = data['volunteers']
                print(f"\n👥 服事人员数据:")
                print(f"   数量: {len(volunteers) if isinstance(volunteers, list) else 'N/A'}")
                if isinstance(volunteers, list) and len(volunteers) > 0:
                    print(f"   第一条数据键: {list(volunteers[0].keys())}")
                    print(f"   第一条数据示例:")
                    first_item = volunteers[0]
                    for key, value in list(first_item.items())[:10]:  # 显示前10个字段
                        if isinstance(value, (str, int, float, bool, type(None))):
                            value_str = str(value)[:50] if len(str(value)) > 50 else str(value)
                            print(f"      {key}: {value_str}")
                        elif isinstance(value, dict):
                            print(f"      {key}: {dict(list(value.items())[:3])}...")  # 显示前3个键值对
                        elif isinstance(value, list):
                            print(f"      {key}: [{len(value)} items]")
        
        elif isinstance(data, list):
            print(f"📊 数组长度: {len(data)}")
            if len(data) > 0:
                print(f"   第一条数据键: {list(data[0].keys())}")
                print(f"   第一条数据示例:")
                first_item = data[0]
                for key, value in list(first_item.items())[:10]:  # 显示前10个字段
                    if isinstance(value, (str, int, float, bool, type(None))):
                        value_str = str(value)[:50] if len(str(value)) > 50 else str(value)
                        print(f"      {key}: {value_str}")
        
        return data
        
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    print("🧪 检查数据源文件结构")
    print("=" * 80)
    
    bucket_name = 'grace-irvine-ministry-data'
    
    # 检查证道数据
    print("\n")
    sermon_data = check_file_structure(bucket_name, 'domains/sermon/latest.json')
    
    # 检查服事人员数据
    print("\n")
    volunteer_data = check_file_structure(bucket_name, 'domains/volunteer/latest.json')
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 数据源总结")
    print("=" * 80)
    print("""
数据源 Bucket 架构:
  grace-irvine-ministry-data/
    ├── domains/
    │   ├── sermon/
    │   │   ├── latest.json              # 最新证道数据
    │   │   ├── 2024/sermon_2024.json    # 2024年证道数据
    │   │   ├── 2025/sermon_2025.json    # 2025年证道数据
    │   │   └── 2026/sermon_2026.json    # 2026年证道数据
    │   └── volunteer/
    │       ├── latest.json               # 最新服事人员数据
    │       ├── 2024/volunteer_2024.json # 2024年服事数据
    │       ├── 2025/volunteer_2025.json # 2025年服事数据
    │       └── 2026/volunteer_2026.json # 2026年服事数据

数据结构:
  - 证道数据: {metadata: {...}, sermons: [...]}
  - 服事人员数据: {metadata: {...}, volunteers: [...]}
    """)


if __name__ == "__main__":
    main()

