#!/usr/bin/env python3
"""
JSON 数据读取器
从 Google Cloud Storage 读取清洗后的 JSON 数据

数据源: grace-irvine-ministry-data bucket
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import date, datetime
from pathlib import Path
from google.cloud import storage

logger = logging.getLogger(__name__)


class JSONDataReader:
    """从 GCS 读取 JSON 数据的读取器"""
    
    def __init__(self, bucket_name: str = None, project_id: str = None):
        """初始化 JSON 数据读取器
        
        Args:
            bucket_name: GCS bucket 名称，默认从环境变量读取
            project_id: GCP 项目 ID，默认从环境变量读取
        """
        self.bucket_name = bucket_name or os.getenv(
            'DATA_SOURCE_BUCKET', 
            'grace-irvine-ministry-data'
        )
        self.project_id = project_id or os.getenv(
            'GOOGLE_CLOUD_PROJECT',
            'ai-for-god'
        )
        self.storage_client = None
        self.bucket = None
        self._setup_client()
    
    def _setup_client(self):
        """设置 GCS 客户端"""
        try:
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            
            if not self.bucket.exists():
                logger.warning(f"Bucket不存在: {self.bucket_name}")
                self.storage_client = None
                self.bucket = None
            else:
                logger.info(f"✅ GCS连接成功: gs://{self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ GCS初始化失败: {e}")
            self.storage_client = None
            self.bucket = None
    
    def read_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """从 GCS 或本地文件读取 JSON 文件
        
        Args:
            file_path: 文件路径（相对于 bucket 根目录或项目根目录）
            
        Returns:
            JSON 数据字典，如果失败返回 None
        """
        # 优先从 GCS 读取
        if self.storage_client and self.bucket:
            try:
                blob = self.bucket.blob(file_path)
                
                if blob.exists():
                    content = blob.download_as_text(encoding='utf-8')
                    data = json.loads(content)
                    logger.info(f"✅ 从GCS成功读取文件: {file_path}")
                    return data
            except Exception as e:
                logger.warning(f"从GCS读取文件失败 {file_path}: {e}")
        
        # 回退到本地文件
        try:
            project_root = Path(__file__).parent.parent
            test_data_dir = project_root / "test_data"
            
            # 尝试匹配文件名
            file_name = Path(file_path).name
            
            # 特殊处理：domains/sermon/latest.json -> sermon_latest.json
            if "domains/sermon/latest.json" in file_path:
                test_path = test_data_dir / "sermon_latest.json"
                if test_path.exists():
                    with open(test_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        logger.info(f"✅ 从本地测试文件读取: {test_path}")
                        return data
            
            # 特殊处理：domains/volunteer/latest.json -> volunteer_latest.json
            if "domains/volunteer/latest.json" in file_path:
                test_path = test_data_dir / "volunteer_latest.json"
                if test_path.exists():
                    with open(test_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        logger.info(f"✅ 从本地测试文件读取: {test_path}")
                        return data
            
            # 尝试从 test_data 目录读取（使用文件名）
            test_data_path = test_data_dir / file_name
            if test_data_path.exists():
                with open(test_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"✅ 从本地测试文件读取: {test_data_path}")
                    return data
            
            # 尝试读取旧路径 service-layer/latest.json
            if "latest.json" in file_path:
                old_path = test_data_dir / "service_layer_latest.json"
                if old_path.exists():
                    with open(old_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        logger.info(f"✅ 从本地测试文件读取: {old_path}")
                        return data
        except Exception as e:
            logger.warning(f"从本地文件读取失败: {e}")
        
        logger.warning(f"文件不存在: {file_path}")
        return None
    
    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """获取最新的清洗数据
        
        Returns:
            最新数据字典，包含 sermons 和 volunteers
        """
        # 读取证道数据
        sermon_data = self.read_json_file('domains/sermon/latest.json')
        
        # 读取服事人员数据
        volunteer_data = self.read_json_file('domains/volunteer/latest.json')
        
        # 合并数据
        combined = {}
        if sermon_data:
            combined['sermons'] = sermon_data.get('sermons', [])
            combined['sermon_metadata'] = sermon_data.get('metadata', {})
        
        if volunteer_data:
            combined['volunteers'] = volunteer_data.get('volunteers', [])
            combined['volunteer_metadata'] = volunteer_data.get('metadata', {})
        
        if combined:
            return combined
        
        # 向后兼容：尝试读取旧路径
        logger.info("尝试读取旧路径 service-layer/latest.json...")
        old_data = self.read_json_file('service-layer/latest.json')
        if old_data:
            return old_data
        
        return None
    
    def get_service_schedule(self) -> List[Dict[str, Any]]:
        """获取服事安排数据（合并证道和服事人员数据）
        
        Returns:
            服事安排列表，每个条目包含证道和服事人员信息
        """
        data = self.get_latest_data()
        
        if not data:
            return []
        
        # 向后兼容：如果数据中有 service_schedule，直接返回
        if 'service_schedule' in data:
            return data.get('service_schedule', [])
        
        # 从新数据结构中合并数据
        sermons = data.get('sermons', [])
        volunteers = data.get('volunteers', [])
        
        # 按日期合并数据
        schedule_dict = {}
        
        # 处理证道数据
        for sermon in sermons:
            # 支持多种日期字段名
            date_str = sermon.get('service_date') or sermon.get('date')
            if date_str:
                if date_str not in schedule_dict:
                    schedule_dict[date_str] = {
                        'date': date_str,
                        'sermon': {},
                        'volunteers': {}
                    }
                # 参考: https://github.com/Grace-Irvine/Grace-Irvine-Ministry-Clean/blob/main/config/config.json
                # 支持字段：sermon_title, preacher, reading, scripture
                schedule_dict[date_str]['sermon'] = {
                    'title': sermon.get('sermon_title') or sermon.get('title') or sermon.get('sermon', ''),
                    'speaker': sermon.get('preacher') or sermon.get('speaker') or (sermon.get('preacher', {}).get('name', '') if isinstance(sermon.get('preacher'), dict) else ''),
                    'reading': sermon.get('reading') or (sermon.get('reading', {}).get('name', '') if isinstance(sermon.get('reading'), dict) else ''),
                    'series': sermon.get('series', ''),
                    'scripture': sermon.get('scripture', ''),
                    'scripture_text': sermon.get('scripture_text', '')
                }
        
        # 处理服事人员数据
        # 动态提取所有部门和岗位，不硬编码部门名称
        for volunteer in volunteers:
            # 支持多种日期字段名
            date_str = volunteer.get('service_date') or volunteer.get('date')
            if not date_str:
                continue
                
            if date_str not in schedule_dict:
                schedule_dict[date_str] = {
                    'date': date_str,
                    'sermon': {},
                    'volunteers': {}
                }
            
            # 动态提取所有部门（排除日期字段）
            excluded_keys = {'service_date', 'date', 'metadata'}
            for dept_key, dept_data in volunteer.items():
                if dept_key in excluded_keys:
                    continue
                
                if not isinstance(dept_data, dict):
                    continue
                
                # 处理部门数据：提取所有岗位
                # 支持字段值为字符串、字典（包含name字段）、或列表
                dept_roles = {}
                for role_key, role_value in dept_data.items():
                    if role_value is None or role_value == '':
                        continue
                    
                    # 处理不同类型的值
                    if isinstance(role_value, dict):
                        # 如果是字典，提取 name 字段（如果存在）
                        # 如果字典中有 name 字段，使用 name；否则尝试直接使用整个字典
                        if 'name' in role_value:
                            role_name = role_value.get('name', '')
                        else:
                            # 如果没有 name 字段，可能是其他格式，转换为字符串
                            role_name = str(role_value)
                    elif isinstance(role_value, list):
                        # 如果是列表，提取每个元素中的 name 字段（如果是字典）
                        name_list = []
                        for item in role_value:
                            if isinstance(item, dict):
                                # 如果列表项是字典，提取 name 字段
                                item_name = item.get('name', '')
                                if item_name:
                                    name_list.append(item_name)
                            else:
                                # 如果列表项是字符串或其他类型，直接使用
                                if item:
                                    name_list.append(str(item))
                        role_name = ', '.join(name_list) if name_list else ''
                    else:
                        # 直接使用字符串值
                        role_name = str(role_value)
                    
                    if role_name:
                        dept_roles[role_key] = role_name
                
                # 如果有岗位数据，添加到排程中
                if dept_roles:
                    schedule_dict[date_str]['volunteers'][dept_key] = dept_roles
        
        # 转换为列表并按日期排序
        schedule_list = list(schedule_dict.values())
        schedule_list.sort(key=lambda x: x.get('date', ''))
        
        return schedule_list
    
    def get_sermon_data(self, target_date: date = None) -> Optional[Dict[str, Any]]:
        """获取证道数据
        
        Args:
            target_date: 目标日期，如果为 None 则返回所有数据
            
        Returns:
            证道数据字典
        """
        schedules = self.get_service_schedule()
        
        if target_date:
            # 查找特定日期的数据
            target_date_str = target_date.strftime('%Y-%m-%d')
            for schedule in schedules:
                if schedule.get('date') == target_date_str:
                    return schedule.get('sermon')
            return None
        
        # 返回所有证道数据
        sermons = []
        for schedule in schedules:
            if 'sermon' in schedule:
                sermon = schedule['sermon'].copy()
                sermon['date'] = schedule.get('date')
                sermons.append(sermon)
        return sermons
    
    def get_media_team_volunteers(self, target_date: date = None) -> List[Dict[str, Any]]:
        """获取媒体部同工数据
        
        Args:
            target_date: 目标日期，如果为 None 则返回所有数据
            
        Returns:
            媒体部同工安排列表
        """
        schedules = self.get_service_schedule()
        results = []
        
        for schedule in schedules:
            schedule_date_str = schedule.get('date')
            if not schedule_date_str:
                continue
            
            try:
                schedule_date = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
            except:
                continue
            
            if target_date and schedule_date != target_date:
                continue
            
            volunteers = schedule.get('volunteers', {})
            media_team = volunteers.get('media', {})
            
            if media_team:
                result = {
                    'date': schedule_date,
                    'audio_tech': media_team.get('audio_tech'),
                    'video_director': media_team.get('video_director'),
                    'propresenter_play': media_team.get('propresenter_play'),
                    'propresenter_update': media_team.get('propresenter_update')
                }
                results.append(result)
        
        return results
    
    def get_children_team_volunteers(self, target_date: date = None) -> List[Dict[str, Any]]:
        """获取儿童部同工数据
        
        Args:
            target_date: 目标日期，如果为 None 则返回所有数据
            
        Returns:
            儿童部同工安排列表
        """
        schedules = self.get_service_schedule()
        results = []
        
        for schedule in schedules:
            schedule_date_str = schedule.get('date')
            if not schedule_date_str:
                continue
            
            try:
                schedule_date = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
            except:
                continue
            
            if target_date and schedule_date != target_date:
                continue
            
            volunteers = schedule.get('volunteers', {})
            children_team = volunteers.get('children', {})
            
            if children_team:
                result = {
                    'date': schedule_date,
                    'teacher': children_team.get('teacher'),
                    'assistant': children_team.get('assistant'),
                    'worship': children_team.get('worship')
                }
                results.append(result)
        
        return results
    
    def get_weekly_overview(self, target_date: date = None) -> List[Dict[str, Any]]:
        """获取每周全部事工概览
        
        Args:
            target_date: 目标日期（周日），如果为 None 则返回所有数据
            
        Returns:
            每周概览列表
        """
        schedules = self.get_service_schedule()
        results = []
        
        for schedule in schedules:
            schedule_date_str = schedule.get('date')
            if not schedule_date_str:
                continue
            
            try:
                schedule_date = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
            except:
                continue
            
            if target_date and schedule_date != target_date:
                continue
            
            # 获取完整数据
            result = {
                'date': schedule_date,
                'sermon': schedule.get('sermon', {}),
                'volunteers': schedule.get('volunteers', {})
            }
            results.append(result)
        
        return results


def get_json_data_reader() -> JSONDataReader:
    """获取 JSON 数据读取器实例（单例模式）"""
    if not hasattr(get_json_data_reader, '_instance'):
        get_json_data_reader._instance = JSONDataReader()
    return get_json_data_reader._instance

