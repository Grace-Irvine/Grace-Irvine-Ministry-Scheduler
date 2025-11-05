#!/usr/bin/env python3
"""
测试 GCS 权限
Test GCS permissions for reading JSON data and writing ICS files

测试服务账号是否有正确的权限来：
1. 从数据源 bucket (grace-irvine-ministry-data) 读取 JSON 文件
2. 向 ICS 存储 bucket (grace-irvine-ministry-scheduler) 写入 ICS 文件
"""

import os
import sys
import json
from pathlib import Path
from google.cloud import storage
from google.cloud.exceptions import Forbidden, NotFound

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_service_account_email(service_account_path: str = None) -> str:
    """获取服务账号邮箱"""
    if service_account_path is None:
        service_account_path = PROJECT_ROOT / "configs" / "service_account.json"
    
    if not Path(service_account_path).exists():
        return None
    
    try:
        with open(service_account_path, 'r') as f:
            service_account = json.load(f)
        return service_account.get('client_email')
    except Exception as e:
        print(f"❌ 无法读取服务账号文件: {e}")
        return None

def test_bucket_access(client: storage.Client, bucket_name: str, action: str = "read") -> tuple:
    """测试 bucket 访问权限
    
    Args:
        client: GCS 客户端
        bucket_name: bucket 名称
        action: 操作类型 ("read", "write", "list")
    
    Returns:
        (success: bool, message: str)
    """
    try:
        bucket = client.bucket(bucket_name)
        
        # 测试 bucket 是否存在
        if not bucket.exists():
            return False, f"Bucket 不存在: {bucket_name}"
        
        # 根据操作类型测试权限
        if action == "read":
            # 尝试列出对象（测试读取权限）
            try:
                blobs = list(bucket.list_blobs(max_results=1))
                return True, f"✅ 可以读取 bucket: {bucket_name}"
            except Forbidden:
                return False, f"❌ 没有读取权限: {bucket_name}"
            except Exception as e:
                return False, f"❌ 读取测试失败: {e}"
        
        elif action == "write":
            # 尝试创建一个测试文件（测试写入权限）
            try:
                test_blob = bucket.blob("__test_permission_check__.txt")
                test_blob.upload_from_string("test", content_type="text/plain")
                test_blob.delete()
                return True, f"✅ 可以写入 bucket: {bucket_name}"
            except Forbidden:
                return False, f"❌ 没有写入权限: {bucket_name}"
            except Exception as e:
                return False, f"❌ 写入测试失败: {e}"
        
        elif action == "list":
            # 测试列出对象权限
            try:
                blobs = list(bucket.list_blobs(max_results=10))
                return True, f"✅ 可以列出 bucket 内容: {bucket_name}"
            except Forbidden:
                return False, f"❌ 没有列出权限: {bucket_name}"
            except Exception as e:
                return False, f"❌ 列出测试失败: {e}"
        
    except Exception as e:
        return False, f"❌ 测试失败: {e}"

def test_file_read(client: storage.Client, bucket_name: str, file_path: str) -> tuple:
    """测试读取特定文件
    
    Args:
        client: GCS 客户端
        bucket_name: bucket 名称
        file_path: 文件路径
    
    Returns:
        (success: bool, message: str)
    """
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        
        if blob.exists():
            content = blob.download_as_text(encoding='utf-8')
            data = json.loads(content)
            return True, f"✅ 可以读取文件: {file_path}"
        else:
            return False, f"❌ 文件不存在: {file_path}"
    except Forbidden:
        return False, f"❌ 没有读取文件权限: {file_path}"
    except json.JSONDecodeError:
        return False, f"❌ 文件不是有效的 JSON: {file_path}"
    except Exception as e:
        return False, f"❌ 读取文件失败: {e}"

def main():
    """主函数"""
    print("=" * 80)
    print("🔐 GCS 权限测试")
    print("=" * 80)
    print()
    
    # 获取服务账号信息
    service_account_path = PROJECT_ROOT / "configs" / "service_account.json"
    service_account_email = get_service_account_email(service_account_path)
    
    if service_account_email:
        print(f"📧 服务账号: {service_account_email}")
    else:
        print("⚠️  未找到服务账号文件，将使用默认凭据")
    
    print()
    
    # 设置服务账号路径
    if service_account_path.exists():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)
        print(f"✅ 使用服务账号: {service_account_path}")
    else:
        print("⚠️  服务账号文件不存在，将使用默认凭据")
    
    print()
    
    # 创建存储客户端
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
        client = storage.Client(project=project_id)
        print(f"✅ GCS 客户端创建成功")
        print(f"📋 项目ID: {project_id}")
        print()
    except Exception as e:
        print(f"❌ GCS 客户端创建失败: {e}")
        print()
        print("💡 可能的解决方案:")
        print("   1. 检查 GOOGLE_APPLICATION_CREDENTIALS 环境变量")
        print("   2. 确认服务账号文件存在且有效")
        print("   3. 运行: gcloud auth application-default login")
        return 1
    
    # 测试数据源 bucket
    print("=" * 80)
    print("📊 测试数据源 Bucket: grace-irvine-ministry-data")
    print("=" * 80)
    print()
    
    data_bucket = "grace-irvine-ministry-data"
    
    # 测试读取权限
    success, message = test_bucket_access(client, data_bucket, "read")
    print(f"{message}")
    
    # 测试列出权限
    success, message = test_bucket_access(client, data_bucket, "list")
    print(f"{message}")
    
    # 测试读取特定文件
    print()
    print("📄 测试读取 JSON 文件:")
    test_files = [
        "domains/sermon/latest.json",
        "domains/volunteer/latest.json",
        "service-layer/latest.json"  # 旧路径
    ]
    
    for file_path in test_files:
        success, message = test_file_read(client, data_bucket, file_path)
        print(f"   {message}")
    
    print()
    
    # 测试 ICS 存储 bucket
    print("=" * 80)
    print("📅 测试 ICS 存储 Bucket: grace-irvine-ministry-scheduler")
    print("=" * 80)
    print()
    
    ics_bucket = "grace-irvine-ministry-scheduler"
    
    # 测试读取权限
    success, message = test_bucket_access(client, ics_bucket, "read")
    print(f"{message}")
    
    # 测试写入权限
    success, message = test_bucket_access(client, ics_bucket, "write")
    print(f"{message}")
    
    print()
    
    # 总结
    print("=" * 80)
    print("📋 权限设置建议")
    print("=" * 80)
    print()
    
    if service_account_email:
        print("🔑 设置数据源 bucket 权限:")
        print(f"   gsutil iam ch serviceAccount:{service_account_email}:roles/storage.objectViewer gs://{data_bucket}")
        print(f"   gsutil iam ch serviceAccount:{service_account_email}:roles/storage.legacyBucketReader gs://{data_bucket}")
        print()
        
        print("🔑 设置 ICS 存储 bucket 权限:")
        print(f"   gsutil iam ch serviceAccount:{service_account_email}:roles/storage.objectCreator gs://{ics_bucket}")
        print(f"   gsutil iam ch serviceAccount:{service_account_email}:roles/storage.objectViewer gs://{ics_bucket}")
        print()
    else:
        print("⚠️  无法获取服务账号邮箱，请手动设置权限")
        print()
    
    print("📚 详细说明请参考: docs/GCS_PERMISSION_SETUP.md")
    print()
    
    return 0

if __name__ == "__main__":
    exit(main())

