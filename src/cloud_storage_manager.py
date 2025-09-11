#!/usr/bin/env python3
"""
云端存储管理器
Cloud Storage Manager

统一管理本地和GCP Storage的文件操作
支持模板、ICS文件、数据缓存的云端存储
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class StorageConfig:
    """存储配置"""
    bucket_name: str
    project_id: str = None
    region: str = "us-central1"
    
    # 文件路径配置
    templates_path: str = "templates/"
    calendars_path: str = "calendars/"
    data_cache_path: str = "data/cache/"
    backups_path: str = "backups/"
    logs_path: str = "logs/"

class CloudStorageManager:
    """云端存储管理器
    
    功能:
    1. 自动检测本地/云端环境
    2. 统一的文件读写接口
    3. 自动同步和备份
    4. 缓存管理
    """
    
    def __init__(self, config: StorageConfig = None):
        """初始化云端存储管理器"""
        self.config = config or self._load_config()
        self.is_cloud_mode = self._detect_cloud_environment()
        self.storage_client = None
        self.bucket = None
        
        # 本地路径
        self.local_root = Path(__file__).parent.parent
        
        # 设置GCP Storage（如果在云端环境）
        if self.is_cloud_mode:
            self._setup_gcp_storage()
    
    def _load_config(self) -> StorageConfig:
        """加载存储配置"""
        bucket_name = os.getenv('GCP_STORAGE_BUCKET', 'grace-irvine-ministry-scheduler')
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'ai-for-god')
        
        return StorageConfig(
            bucket_name=bucket_name,
            project_id=project_id
        )
    
    def _detect_cloud_environment(self) -> bool:
        """检测是否在云端环境"""
        # 明确的云端环境标识
        cloud_indicators = [
            'K_SERVICE' in os.environ,  # Cloud Run
            'GAE_ENV' in os.environ,    # App Engine
            os.getenv('STORAGE_MODE') == 'cloud',  # 显式设置
        ]
        
        # 如果设置了非默认bucket名称，也认为是云端模式
        if self.config.bucket_name and self.config.bucket_name != 'grace-irvine-ministry-scheduler':
            cloud_indicators.append(True)
        
        return any(cloud_indicators)
    
    def _setup_gcp_storage(self):
        """设置GCP Storage客户端"""
        try:
            from google.cloud import storage
            self.storage_client = storage.Client(project=self.config.project_id)
            self.bucket = self.storage_client.bucket(self.config.bucket_name)
            
            # 验证bucket存在
            if self.bucket.exists():
                logger.info(f"GCP Storage连接成功: gs://{self.config.bucket_name}")
            else:
                logger.warning(f"Bucket不存在: {self.config.bucket_name}")
                self.storage_client = None
                
        except ImportError:
            logger.error("google-cloud-storage包未安装，无法使用GCP Storage")
            self.storage_client = None
        except Exception as e:
            logger.error(f"GCP Storage初始化失败: {e}")
            self.storage_client = None
    
    def read_file(self, file_path: str, file_type: str = "auto") -> Optional[Union[str, bytes, Dict]]:
        """统一的文件读取接口
        
        Args:
            file_path: 文件路径（相对于项目根目录）
            file_type: 文件类型 ("text", "json", "binary", "auto")
            
        Returns:
            文件内容，如果失败返回None
        """
        # 云端优先策略
        if self.is_cloud_mode and self.storage_client:
            content = self._read_from_gcp(file_path, file_type)
            if content is not None:
                logger.info(f"从GCP Storage读取: {file_path}")
                return content
        
        # 回退到本地文件
        return self._read_from_local(file_path, file_type)
    
    def write_file(self, file_path: str, content: Union[str, bytes, Dict], 
                   sync_to_cloud: bool = True, backup: bool = True) -> bool:
        """统一的文件写入接口
        
        Args:
            file_path: 文件路径
            content: 文件内容
            sync_to_cloud: 是否同步到云端
            backup: 是否创建备份
            
        Returns:
            是否写入成功
        """
        success = True
        
        # 1. 写入本地文件
        if not self._write_to_local(file_path, content):
            success = False
        
        # 2. 创建备份（如果需要）
        if backup and self._is_important_file(file_path):
            self._create_backup(file_path, content)
        
        # 3. 同步到云端（如果需要）
        if sync_to_cloud and self.is_cloud_mode and self.storage_client:
            if not self._write_to_gcp(file_path, content):
                logger.warning(f"云端同步失败: {file_path}")
                # 本地写入成功，云端失败不影响整体功能
        
        return success
    
    def _read_from_gcp(self, file_path: str, file_type: str) -> Optional[Union[str, bytes, Dict]]:
        """从GCP Storage读取文件"""
        try:
            blob = self.bucket.blob(file_path)
            if not blob.exists():
                return None
            
            if file_type == "binary":
                return blob.download_as_bytes()
            else:
                content = blob.download_as_text(encoding='utf-8')
                
                if file_type == "json" or (file_type == "auto" and file_path.endswith('.json')):
                    return json.loads(content)
                else:
                    return content
                    
        except Exception as e:
            logger.error(f"从GCP Storage读取文件失败 {file_path}: {e}")
            return None
    
    def _read_from_local(self, file_path: str, file_type: str) -> Optional[Union[str, bytes, Dict]]:
        """从本地文件读取"""
        try:
            local_path = self.local_root / file_path
            if not local_path.exists():
                return None
            
            if file_type == "binary":
                with open(local_path, 'rb') as f:
                    return f.read()
            else:
                with open(local_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if file_type == "json" or (file_type == "auto" and file_path.endswith('.json')):
                    return json.loads(content)
                else:
                    return content
                    
        except Exception as e:
            logger.error(f"从本地文件读取失败 {file_path}: {e}")
            return None
    
    def _write_to_local(self, file_path: str, content: Union[str, bytes, Dict]) -> bool:
        """写入本地文件"""
        try:
            local_path = self.local_root / file_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(content, dict):
                with open(local_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            elif isinstance(content, bytes):
                with open(local_path, 'wb') as f:
                    f.write(content)
            else:
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            logger.info(f"本地文件写入成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"本地文件写入失败 {file_path}: {e}")
            return False
    
    def _write_to_gcp(self, file_path: str, content: Union[str, bytes, Dict]) -> bool:
        """写入GCP Storage"""
        try:
            blob = self.bucket.blob(file_path)
            
            if isinstance(content, dict):
                content_str = json.dumps(content, ensure_ascii=False, indent=2)
                blob.upload_from_string(content_str, content_type='application/json')
            elif isinstance(content, bytes):
                blob.upload_from_string(content, content_type='application/octet-stream')
            else:
                # 根据文件扩展名设置content_type
                if file_path.endswith('.ics'):
                    content_type = 'text/calendar; charset=utf-8'
                elif file_path.endswith('.json'):
                    content_type = 'application/json'
                else:
                    content_type = 'text/plain; charset=utf-8'
                
                blob.upload_from_string(content, content_type=content_type)
            
            logger.info(f"GCP Storage写入成功: gs://{self.config.bucket_name}/{file_path}")
            return True
            
        except Exception as e:
            logger.error(f"GCP Storage写入失败 {file_path}: {e}")
            return False
    
    def _create_backup(self, file_path: str, content: Union[str, bytes, Dict]):
        """创建备份文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"
            backup_path = f"{self.config.backups_path}{backup_name}"
            
            # 备份到云端（如果可用）
            if self.is_cloud_mode and self.storage_client:
                self._write_to_gcp(backup_path, content)
            
            # 备份到本地
            local_backup_dir = self.local_root / "backups"
            local_backup_dir.mkdir(exist_ok=True)
            self._write_to_local(f"backups/{backup_name}", content)
            
            logger.info(f"备份创建成功: {backup_name}")
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
    
    def _is_important_file(self, file_path: str) -> bool:
        """判断是否是重要文件需要备份"""
        important_patterns = [
            'templates/dynamic_templates.json',
            'calendars/*.ics',
            'data/processed_schedules.json'
        ]
        
        for pattern in important_patterns:
            if pattern.replace('*', '') in file_path:
                return True
        return False
    
    def sync_all_files(self) -> Dict[str, bool]:
        """同步所有重要文件到云端"""
        if not (self.is_cloud_mode and self.storage_client):
            return {"error": "云端存储不可用"}
        
        sync_files = [
            "templates/dynamic_templates.json",
            "calendars/grace_irvine_coordinator.ics"
        ]
        
        results = {}
        
        for file_path in sync_files:
            local_path = self.local_root / file_path
            if local_path.exists():
                try:
                    with open(local_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    results[file_path] = self._write_to_gcp(file_path, content)
                except Exception as e:
                    logger.error(f"同步文件失败 {file_path}: {e}")
                    results[file_path] = False
            else:
                results[file_path] = False
        
        return results
    
    def get_file_status(self, file_path: str) -> Dict[str, Any]:
        """获取文件状态信息"""
        status = {
            'file_path': file_path,
            'local_exists': False,
            'cloud_exists': False,
            'local_size': 0,
            'cloud_size': 0,
            'local_modified': None,
            'cloud_modified': None,
            'sync_needed': False
        }
        
        # 检查本地文件
        local_path = self.local_root / file_path
        if local_path.exists():
            status['local_exists'] = True
            stat = local_path.stat()
            status['local_size'] = stat.st_size
            status['local_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # 检查云端文件
        if self.is_cloud_mode and self.storage_client:
            try:
                blob = self.bucket.blob(file_path)
                if blob.exists():
                    blob.reload()
                    status['cloud_exists'] = True
                    status['cloud_size'] = blob.size
                    status['cloud_modified'] = blob.time_created.isoformat()
                    
                    # 判断是否需要同步
                    if status['local_exists'] and status['cloud_exists']:
                        local_time = datetime.fromisoformat(status['local_modified'])
                        cloud_time = blob.time_created.replace(tzinfo=None)
                        status['sync_needed'] = abs((local_time - cloud_time).total_seconds()) > 60
                        
            except Exception as e:
                logger.error(f"检查云端文件状态失败 {file_path}: {e}")
        
        return status
    
    def list_backups(self, file_pattern: str = None) -> List[Dict[str, Any]]:
        """列出备份文件"""
        backups = []
        
        # 本地备份
        local_backup_dir = self.local_root / "backups"
        if local_backup_dir.exists():
            for backup_file in local_backup_dir.glob("*"):
                if file_pattern and file_pattern not in backup_file.name:
                    continue
                
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'location': 'local',
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'path': str(backup_file)
                })
        
        # 云端备份
        if self.is_cloud_mode and self.storage_client:
            try:
                prefix = self.config.backups_path
                for blob in self.bucket.list_blobs(prefix=prefix):
                    if file_pattern and file_pattern not in blob.name:
                        continue
                    
                    backups.append({
                        'name': blob.name.replace(prefix, ''),
                        'location': 'cloud',
                        'size': blob.size,
                        'created': blob.time_created.isoformat(),
                        'path': f"gs://{self.config.bucket_name}/{blob.name}"
                    })
            except Exception as e:
                logger.error(f"列出云端备份失败: {e}")
        
        # 按创建时间排序
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """清理旧备份文件"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cleaned_count = 0
        
        # 清理本地备份
        local_backup_dir = self.local_root / "backups"
        if local_backup_dir.exists():
            for backup_file in local_backup_dir.glob("*"):
                stat = backup_file.stat()
                if datetime.fromtimestamp(stat.st_mtime) < cutoff_date:
                    backup_file.unlink()
                    cleaned_count += 1
        
        # 清理云端备份
        if self.is_cloud_mode and self.storage_client:
            try:
                prefix = self.config.backups_path
                for blob in self.bucket.list_blobs(prefix=prefix):
                    if blob.time_created.replace(tzinfo=None) < cutoff_date:
                        blob.delete()
                        cleaned_count += 1
            except Exception as e:
                logger.error(f"清理云端备份失败: {e}")
        
        logger.info(f"清理了 {cleaned_count} 个旧备份文件")
        return cleaned_count
    
    # 便捷方法
    def read_template_config(self) -> Optional[Dict]:
        """读取模板配置"""
        return self.read_file("templates/dynamic_templates.json", "json")
    
    def write_template_config(self, config: Dict) -> bool:
        """写入模板配置"""
        return self.write_file("templates/dynamic_templates.json", config)
    
    def read_scripture_config(self) -> Optional[Dict]:
        """读取经文配置"""
        return self.read_file("templates/scripture_sharing.json", "json")
    
    def write_scripture_config(self, config: Dict) -> bool:
        """写入经文配置"""
        return self.write_file("templates/scripture_sharing.json", config)
    
    def read_ics_calendar(self, calendar_name: str = "grace_irvine_coordinator.ics") -> Optional[str]:
        """读取ICS日历文件"""
        return self.read_file(f"calendars/{calendar_name}", "text")
    
    def write_ics_calendar(self, calendar_content: str, calendar_name: str = "grace_irvine_coordinator.ics") -> bool:
        """写入ICS日历文件"""
        return self.write_file(f"calendars/{calendar_name}", calendar_content)
    
    def get_public_calendar_url(self, calendar_name: str = "grace_irvine_coordinator.ics") -> str:
        """获取公开的日历订阅URL"""
        if self.is_cloud_mode and self.storage_client:
            # 云端环境返回GCS公开URL
            return f"https://storage.googleapis.com/{self.config.bucket_name}/calendars/{calendar_name}"
        else:
            # 本地环境返回应用URL
            port = os.getenv('PORT', '8501')
            return f"http://localhost:{port}/calendars/{calendar_name}"
    
    def get_storage_status(self) -> Dict[str, Any]:
        """获取存储状态"""
        status = {
            'mode': 'cloud' if self.is_cloud_mode else 'local',
            'bucket_name': self.config.bucket_name if self.is_cloud_mode else None,
            'storage_available': bool(self.storage_client),
            'files': {}
        }
        
        # 检查重要文件状态
        important_files = [
            "templates/dynamic_templates.json",
            "calendars/grace_irvine_coordinator.ics"
        ]
        
        for file_path in important_files:
            status['files'][file_path] = self.get_file_status(file_path)
        
        return status

# 全局实例
_storage_manager = None

def get_storage_manager() -> CloudStorageManager:
    """获取存储管理器单例"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = CloudStorageManager()
    return _storage_manager

def test_storage_manager():
    """测试存储管理器"""
    print("🧪 测试云端存储管理器...")
    
    manager = get_storage_manager()
    
    # 测试基本功能
    print(f"存储模式: {'云端' if manager.is_cloud_mode else '本地'}")
    print(f"Bucket: {manager.config.bucket_name}")
    print(f"存储客户端: {'可用' if manager.storage_client else '不可用'}")
    
    # 测试文件读取
    template_config = manager.read_template_config()
    if template_config:
        print("✅ 模板配置读取成功")
    else:
        print("❌ 模板配置读取失败")
        return False
    
    # 测试状态检查
    status = manager.get_storage_status()
    print(f"✅ 存储状态: {status['mode']} 模式")
    
    return True

if __name__ == "__main__":
    success = test_storage_manager()
    print(f"{'✅ 测试通过' if success else '❌ 测试失败'}")
    sys.exit(0 if success else 1)
