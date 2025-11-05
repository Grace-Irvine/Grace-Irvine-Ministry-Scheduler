#!/usr/bin/env python3
"""
列出数据源 Bucket 的文件架构
List file structure in data source bucket

尝试列出 grace-irvine-ministry-data bucket 中的所有文件和目录结构
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from google.cloud import storage
from google.api_core import exceptions
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def list_bucket_structure(bucket_name: str, service_account_path: str = None):
    """列出 bucket 的文件架构
    
    Args:
        bucket_name: bucket 名称
        service_account_path: 服务账号 JSON 文件路径
    """
    print("=" * 80)
    print(f"📦 列出 Bucket 文件架构: {bucket_name}")
    print("=" * 80)
    
    try:
        # 设置服务账号路径
        if service_account_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)
        else:
            default_path = PROJECT_ROOT / "configs" / "service_account.json"
            if default_path.exists():
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(default_path)
        
        # 创建存储客户端
        print(f"\n🔗 创建存储客户端...")
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
        client = storage.Client(project=project_id)
        
        # 获取 bucket
        print(f"📦 获取 bucket: {bucket_name}")
        bucket = client.bucket(bucket_name)
        
        # 尝试列出所有文件
        print(f"\n📁 列出所有文件...")
        try:
            blobs = list(bucket.list_blobs())
            print(f"   ✅ 找到 {len(blobs)} 个文件")
        except exceptions.Forbidden as e:
            print(f"   ❌ 权限不足: {e}")
            print(f"\n💡 提示: 需要给服务账号添加以下权限:")
            print(f"   - Storage Object Viewer (roles/storage.objectViewer)")
            print(f"   - Storage Legacy Bucket Reader (roles/storage.legacyBucketReader)")
            return False
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return False
        
        if not blobs:
            print(f"   ⚠️  Bucket 为空")
            return True
        
        # 按目录组织文件
        print(f"\n📂 文件架构:")
        print("=" * 80)
        
        # 按前缀分组
        structure = defaultdict(list)
        for blob in blobs:
            # 获取目录路径
            parts = blob.name.split('/')
            if len(parts) > 1:
                directory = '/'.join(parts[:-1])
                filename = parts[-1]
            else:
                directory = '.'
                filename = parts[0]
            
            structure[directory].append({
                'name': filename,
                'full_path': blob.name,
                'size': blob.size,
                'updated': blob.time_created or blob.updated,
                'content_type': blob.content_type
            })
        
        # 按目录排序
        sorted_dirs = sorted(structure.keys())
        
        for directory in sorted_dirs:
            if directory == '.':
                print(f"\n📁 根目录:")
            else:
                print(f"\n📁 {directory}/")
            
            files = structure[directory]
            files.sort(key=lambda x: x['name'])
            
            for file_info in files:
                size_kb = file_info['size'] / 1024 if file_info['size'] else 0
                size_str = f"{size_kb:.1f} KB" if size_kb > 0 else "0 KB"
                print(f"   📄 {file_info['name']}")
                print(f"      大小: {size_str}")
                print(f"      类型: {file_info['content_type'] or 'unknown'}")
                print(f"      更新时间: {file_info['updated']}")
                
                # 如果是 JSON 文件，尝试读取并显示结构
                if file_info['name'].endswith('.json'):
                    try:
                        blob = bucket.blob(file_info['full_path'])
                        content = blob.download_as_text(encoding='utf-8')
                        import json
                        data = json.loads(content)
                        if isinstance(data, dict):
                            print(f"      数据键: {list(data.keys())}")
                        elif isinstance(data, list):
                            print(f"      数组长度: {len(data)}")
                            if len(data) > 0 and isinstance(data[0], dict):
                                print(f"      第一条数据键: {list(data[0].keys())}")
                    except Exception as e:
                        print(f"      读取失败: {e}")
        
        # 统计信息
        print("\n" + "=" * 80)
        print("📊 统计信息:")
        print(f"   总文件数: {len(blobs)}")
        print(f"   总目录数: {len(structure)}")
        total_size = sum(f['size'] for files in structure.values() for f in files)
        total_size_mb = total_size / (1024 * 1024)
        print(f"   总大小: {total_size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🧪 列出数据源 Bucket 文件架构")
    print("=" * 80)
    
    # 服务账号路径
    service_account_path = PROJECT_ROOT / "configs" / "service_account.json"
    
    if not service_account_path.exists():
        print(f"❌ 服务账号文件不存在: {service_account_path}")
        return
    
    # 测试访问数据源 bucket
    data_bucket = os.getenv('DATA_SOURCE_BUCKET', 'grace-irvine-ministry-data')
    
    success = list_bucket_structure(data_bucket, service_account_path)
    
    if not success:
        print("\n" + "=" * 80)
        print("💡 解决方案:")
        print("=" * 80)
        print("如果遇到权限错误，需要给服务账号添加权限:")
        print(f"\ngsutil iam ch serviceAccount:scheduler-service@ai-for-god.iam.gserviceaccount.com:roles/storage.objectViewer gs://{data_bucket}")
        print(f"\ngsutil iam ch serviceAccount:scheduler-service@ai-for-god.iam.gserviceaccount.com:roles/storage.legacyBucketReader gs://{data_bucket}")


if __name__ == "__main__":
    main()

