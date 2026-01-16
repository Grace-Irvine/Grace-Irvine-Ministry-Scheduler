#!/usr/bin/env python3
"""
ICS 通知配置管理器
管理 ICS 日历的通知时间配置
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import time, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class NotificationTiming:
    """通知时间配置"""
    relative_to_sunday: int  # 相对于主日（周日）的天数偏移
    time_str: str  # 时间字符串 "HH:MM"
    duration_minutes: int = 30  # 持续时间（分钟）
    reminder_minutes: int = 30  # 提醒提前时间（分钟）
    
    def to_time(self) -> time:
        """转换为 time 对象"""
        hour, minute = map(int, self.time_str.split(':'))
        return time(hour, minute)
    
    def to_ics_trigger(self) -> str:
        """转换为 ICS TRIGGER 格式"""
        return f"-PT{self.reminder_minutes}M"


@dataclass
class CalendarNotificationConfig:
    """单个日历的通知配置"""
    enabled: bool = True
    notifications: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def get_notification(self, notification_type: str) -> Optional[NotificationTiming]:
        """获取特定类型的通知配置"""
        if notification_type not in self.notifications:
            return None
        
        config = self.notifications[notification_type]
        if not config.get('enabled', True):
            return None
        
        return NotificationTiming(
            relative_to_sunday=config.get('relative_to_sunday', -4),
            time_str=config.get('time', '20:00'),
            duration_minutes=config.get('duration_minutes', 30),
            reminder_minutes=config.get('reminder_minutes', 30)
        )


@dataclass
class ICSNotificationConfig:
    """ICS 通知配置"""
    calendars: Dict[str, Any] = field(default_factory=dict)
    
    def get_calendar_config(self, calendar_type: str) -> Optional[CalendarNotificationConfig]:
        """获取特定类型的日历配置"""
        if calendar_type not in self.calendars:
            return None
        
        config_data = self.calendars[calendar_type]
        notifications = config_data.get('notifications', {})
        
        return CalendarNotificationConfig(
            enabled=config_data.get('enabled', True),
            notifications=notifications
        )
    
    def is_calendar_enabled(self, calendar_type: str) -> bool:
        """检查日历是否启用"""
        config = self.get_calendar_config(calendar_type)
        return config is not None and config.enabled


class ICSNotificationConfigManager:
    """ICS 通知配置管理器"""
    
    def __init__(self, config_path: str = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: Optional[ICSNotificationConfig] = None
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 优先从环境变量读取
        if os.getenv('ICS_CONFIG_PATH'):
            return os.getenv('ICS_CONFIG_PATH')
        
        # 使用默认路径
        return 'configs/ics_notification_config.json'
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "calendars": {
                "media-team": {
                    "enabled": True,
                    "notifications": {
                        "wednesday_confirmation": {
                            "enabled": True,
                            "relative_to_sunday": -4,
                            "time": "20:00",
                            "duration_minutes": 30,
                            "reminder_minutes": 30
                        },
                        "saturday_reminder": {
                            "enabled": True,
                            "relative_to_sunday": -1,
                            "time": "20:00",
                            "duration_minutes": 30,
                            "reminder_minutes": 30
                        }
                    }
                },
                "children-team": {
                    "enabled": True,
                    "notifications": {
                        "wednesday_confirmation": {
                            "enabled": True,
                            "relative_to_sunday": -4,
                            "time": "20:00",
                            "duration_minutes": 30,
                            "reminder_minutes": 30
                        },
                        "saturday_reminder": {
                            "enabled": True,
                            "relative_to_sunday": -1,
                            "time": "20:00",
                            "duration_minutes": 30,
                            "reminder_minutes": 30
                        }
                    }
                }
            }
        }
    
    def _load_config(self):
        """加载配置"""
        try:
            # 尝试从本地文件读取
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.config = ICSNotificationConfig(calendars=config_data.get('calendars', {}))
                    logger.info(f"✅ 从本地文件加载配置: {self.config_path}")
                    return
            
            # 尝试从 GCS 读取
            try:
                from src.cloud_storage_manager import get_storage_manager
                storage_manager = get_storage_manager()
                if storage_manager and storage_manager.is_cloud_mode:
                    config_data = storage_manager.read_file(self.config_path, 'json')
                    if config_data:
                        self.config = ICSNotificationConfig(calendars=config_data.get('calendars', {}))
                        logger.info(f"✅ 从GCS加载配置: {self.config_path}")
                        return
            except Exception as e:
                logger.warning(f"从GCS读取配置失败: {e}")
            
            # 使用默认配置
            logger.info("使用默认配置")
            default_data = self._get_default_config()
            self.config = ICSNotificationConfig(calendars=default_data.get('calendars', {}))
            
        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            # 使用默认配置
            default_data = self._get_default_config()
            self.config = ICSNotificationConfig(calendars=default_data.get('calendars', {}))
    
    def save_config(self, config: ICSNotificationConfig = None):
        """保存配置
        
        Args:
            config: 要保存的配置，如果为 None 则保存当前配置
        """
        if config:
            self.config = config
        
        if not self.config:
            return
        
        try:
            # 确保目录存在
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # 转换为字典
            config_dict = {
                'calendars': {}
            }
            
            for calendar_type, calendar_config in self.config.calendars.items():
                config_dict['calendars'][calendar_type] = calendar_config
            
            # 保存到本地文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 配置已保存: {self.config_path}")
            
            # 尝试同步到 GCS
            try:
                from src.cloud_storage_manager import get_storage_manager
                storage_manager = get_storage_manager()
                if storage_manager and storage_manager.is_cloud_mode:
                    storage_manager.write_file(self.config_path, config_dict, sync_to_cloud=True)
                    logger.info(f"✅ 配置已同步到GCS: {self.config_path}")
            except Exception as e:
                logger.warning(f"同步配置到GCS失败: {e}")
                
        except Exception as e:
            logger.error(f"❌ 保存配置失败: {e}")
    
    def get_notification_timing(
        self, 
        calendar_type: str, 
        notification_type: str
    ) -> Optional[NotificationTiming]:
        """获取通知时间配置
        
        Args:
            calendar_type: 日历类型 (media-team, children-team)
            notification_type: 通知类型 (wednesday_confirmation, saturday_reminder, monday_overview)
            
        Returns:
            通知时间配置，如果不存在返回 None
        """
        if not self.config:
            return None
        
        calendar_config = self.config.get_calendar_config(calendar_type)
        if not calendar_config:
            return None
        
        return calendar_config.get_notification(notification_type)


# 全局配置管理器实例
_config_manager: Optional[ICSNotificationConfigManager] = None


def get_config_manager() -> ICSNotificationConfigManager:
    """获取配置管理器实例（单例模式）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ICSNotificationConfigManager()
    return _config_manager

