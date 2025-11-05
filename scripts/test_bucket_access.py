#!/usr/bin/env python3
"""
测试 Bucket 访问
Test bucket access using service account

使用 service_account.json 测试访问 GCS bucket
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

def test_bucket_access(bucket_name: str, service_account_path: str = None):
    """测试访问 bucket
    
    Args:
        bucket_name: bucket 名称
        service_account_path: 服务账号 JSON 文件路径
    """
    print("=" * 80)
    print(f"📦 测试访问 Bucket: {bucket_name}")
    print("=" * 80)
    
    try:
        # 设置服务账号路径
        if service_account_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)
            print(f"\n✅ 使用服务账号: {service_account_path}")
        else:
            default_path = PROJECT_ROOT / "configs" / "service_account.json"
            if default_path.exists():
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(default_path)
                print(f"\n✅ 使用默认服务账号: {default_path}")
            else:
                print(f"\n⚠️  未找到服务账号文件，使用默认凭据")
        
        # 创建存储客户端
        print(f"\n🔗 创建存储客户端...")
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
        client = storage.Client(project=project_id)
        print(f"   ✅ 客户端创建成功")
        print(f"   📋 项目ID: {project_id}")
        
        # 获取 bucket
        print(f"\n📦 获取 bucket: {bucket_name}")
        bucket = client.bucket(bucket_name)
        
        # 检查 bucket 是否存在
        print(f"\n🔍 检查 bucket 是否存在...")
        if bucket.exists():
            print(f"   ✅ Bucket 存在")
        else:
            print(f"   ❌ Bucket 不存在")
            return False
        
        # 获取 bucket 信息
        print(f"\n📊 Bucket 信息:")
        bucket.reload()
        print(f"   📋 名称: {bucket.name}")
        print(f"   📍 位置: {bucket.location}")
        print(f"   📍 存储类别: {bucket.storage_class}")
        print(f"   🕒 创建时间: {bucket.time_created}")
        
        # 列出文件
        print(f"\n📁 列出文件...")
        blobs = list(bucket.list_blobs(max_results=20))
        print(f"   ✅ 找到 {len(blobs)} 个文件（最多显示20个）")
        
        if blobs:
            print(f"\n   📄 文件列表:")
            for i, blob in enumerate(blobs, 1):
                size_kb = blob.size / 1024 if blob.size else 0
                updated = blob.time_created or blob.updated
                print(f"   {i:2d}. {blob.name}")
                print(f"       大小: {size_kb:.1f} KB")
                print(f"       更新时间: {updated}")
                print()
        else:
            print(f"   ⚠️  Bucket 为空")
        
        # 测试读取特定文件
        print(f"\n🔍 测试读取特定文件...")
        test_files = [
            'service-layer/latest.json',
            'service-layer/service_schedule.json',
            'service-layer/sermon_schedule.json'
        ]
        
        for file_path in test_files:
            blob = bucket.blob(file_path)
            if blob.exists():
                print(f"   ✅ {file_path} 存在")
                try:
                    content = blob.download_as_text(encoding='utf-8')
                    data = json.loads(content)
                    if isinstance(data, dict):
                        print(f"      📊 数据键: {list(data.keys())}")
                    elif isinstance(data, list):
                        print(f"      📊 数组长度: {len(data)}")
                    print(f"      📏 文件大小: {len(content)} 字节")
                except Exception as e:
                    print(f"      ⚠️  读取失败: {e}")
            else:
                print(f"   ❌ {file_path} 不存在")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_account_info(service_account_path: str):
    """读取并显示服务账号信息"""
    print("=" * 80)
    print("🔑 服务账号信息")
    print("=" * 80)
    
    try:
        with open(service_account_path, 'r', encoding='utf-8') as f:
            sa_info = json.load(f)
        
        print(f"\n📋 服务账号详情:")
        print(f"   📧 邮箱: {sa_info.get('client_email')}")
        print(f"   🆔 项目ID: {sa_info.get('project_id')}")
        print(f"   🔑 私钥ID: {sa_info.get('private_key_id')}")
        print(f"   ✅ 类型: {sa_info.get('type')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 读取服务账号信息失败: {e}")
        return False


def main():
    """主函数"""
    print("🧪 测试 Bucket 访问")
    print("=" * 80)
    
    # 服务账号路径
    service_account_path = PROJECT_ROOT / "configs" / "service_account.json"
    
    if not service_account_path.exists():
        print(f"❌ 服务账号文件不存在: {service_account_path}")
        return
    
    # 显示服务账号信息
    test_service_account_info(service_account_path)
    
    # 测试访问数据源 bucket
    data_bucket = os.getenv('DATA_SOURCE_BUCKET', 'grace-irvine-ministry-data')
    print("\n" + "=" * 80)
    test_bucket_access(data_bucket, service_account_path)
    
    # 测试访问输出 bucket
    output_bucket = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
    print("\n" + "=" * 80)
    test_bucket_access(output_bucket, service_account_path)


if __name__ == "__main__":
    main()

