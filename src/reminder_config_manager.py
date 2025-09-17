#!/usr/bin/env python3
"""
提醒配置管理器
Reminder Configuration Manager

管理ICS日历的提醒时间配置，包括：
- 事件时间设置（周几几点）
- 提醒时间设置（提前多久提醒）
- 配置保存到云端/本地
- 配置验证和默认值
"""

import os
import sys
import json
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ReminderTiming:
    """提醒时间配置"""
    minutes_before: int  # 提前多少分钟提醒
    hours_before: int = 0   # 提前多少小时提醒
    days_before: int = 0    # 提前多少天提醒
    
    def to_ics_trigger(self) -> str:
        """转换为ICS格式的TRIGGER字符串"""
        total_minutes = self.minutes_before + (self.hours_before * 60) + (self.days_before * 24 * 60)
        
        if total_minutes < 60:
            return f"-PT{total_minutes}M"
        elif total_minutes < 1440:  # 小于24小时
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes == 0:
                return f"-PT{hours}H"
            else:
                return f"-PT{hours}H{minutes}M"
        else:  # 大于等于24小时
            days = total_minutes // 1440
            remaining_minutes = total_minutes % 1440
            if remaining_minutes == 0:
                return f"-P{days}D"
            else:
                hours = remaining_minutes // 60
                minutes = remaining_minutes % 60
                if hours == 0:
                    return f"-P{days}DT{minutes}M"
                elif minutes == 0:
                    return f"-P{days}DT{hours}H"
                else:
                    return f"-P{days}DT{hours}H{minutes}M"
    
    @classmethod
    def from_minutes(cls, total_minutes: int):
        """从总分钟数创建ReminderTiming"""
        return cls(minutes_before=total_minutes)
    
    @classmethod
    def from_ics_trigger(cls, trigger_str: str):
        """从ICS TRIGGER字符串解析"""
        # 简化版解析，支持常见格式
        trigger_str = trigger_str.strip()
        if trigger_str.startswith('-PT') and trigger_str.endswith('M'):
            minutes = int(trigger_str[3:-1])
            return cls.from_minutes(minutes)
        elif trigger_str.startswith('-PT') and trigger_str.endswith('H'):
            hours = int(trigger_str[3:-1])
            return cls.from_minutes(hours * 60)
        else:
            # 默认30分钟
            return cls.from_minutes(30)

@dataclass
class EventTiming:
    """事件时间配置"""
    weekday: int  # 星期几 (0=Monday, 6=Sunday)
    hour: int     # 小时 (0-23)
    minute: int   # 分钟 (0-59)
    duration_minutes: int = 30  # 持续时间（分钟）
    
    def to_time(self) -> time:
        """转换为time对象"""
        return time(hour=self.hour, minute=self.minute)
    
    def get_weekday_name(self) -> str:
        """获取星期几的中文名称"""
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[self.weekday]
    
    @classmethod
    def from_time_and_weekday(cls, weekday: int, time_obj: time, duration_minutes: int = 30):
        """从时间和星期几创建EventTiming"""
        return cls(
            weekday=weekday,
            hour=time_obj.hour,
            minute=time_obj.minute,
            duration_minutes=duration_minutes
        )

@dataclass
class NotificationConfig:
    """通知配置"""
    event_type: str  # 事件类型标识
    name: str        # 配置名称
    description: str # 配置描述
    event_timing: EventTiming    # 事件时间
    reminder_timing: ReminderTiming  # 提醒时间
    enabled: bool = True  # 是否启用
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'event_type': self.event_type,
            'name': self.name,
            'description': self.description,
            'event_timing': asdict(self.event_timing),
            'reminder_timing': asdict(self.reminder_timing),
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建NotificationConfig"""
        return cls(
            event_type=data['event_type'],
            name=data['name'],
            description=data['description'],
            event_timing=EventTiming(**data['event_timing']),
            reminder_timing=ReminderTiming(**data['reminder_timing']),
            enabled=data.get('enabled', True)
        )

class ReminderConfigManager:
    """提醒配置管理器"""
    
    CONFIG_FILE = "configs/reminder_settings.json"
    CLOUD_CONFIG_PATH = "configs/reminder_settings.json"  # 云端路径
    
    def __init__(self):
        """初始化配置管理器"""
        self.configs: Dict[str, NotificationConfig] = {}
        self.storage_manager = None
        self._setup_storage()
        self.load_configs()
    
    def _setup_storage(self):
        """设置存储管理器"""
        try:
            # 在独立运行时，使用绝对导入
            try:
                from .cloud_storage_manager import get_storage_manager
            except ImportError:
                # 如果相对导入失败，尝试绝对导入
                sys.path.insert(0, str(PROJECT_ROOT))
                from src.cloud_storage_manager import get_storage_manager
            
            self.storage_manager = get_storage_manager()
            logger.info(f"存储管理器初始化成功，云端模式: {self.storage_manager.is_cloud_mode if self.storage_manager else False}")
        except Exception as e:
            logger.error(f"设置存储管理器失败: {e}")
            self.storage_manager = None
    
    def get_default_configs(self) -> Dict[str, NotificationConfig]:
        """获取默认配置"""
        return {
            'weekly_confirmation': NotificationConfig(
                event_type='weekly_confirmation',
                name='周三确认通知',
                description='发送周末服事安排确认通知',
                event_timing=EventTiming(weekday=2, hour=20, minute=0, duration_minutes=30),  # 周三8点
                reminder_timing=ReminderTiming(minutes_before=30),  # 提前30分钟
                enabled=True
            ),
            'saturday_reminder': NotificationConfig(
                event_type='saturday_reminder',
                name='周六提醒通知',
                description='发送主日服事提醒通知',
                event_timing=EventTiming(weekday=5, hour=20, minute=0, duration_minutes=30),  # 周六8点
                reminder_timing=ReminderTiming(minutes_before=30),  # 提前30分钟
                enabled=True
            ),
            'monthly_overview': NotificationConfig(
                event_type='monthly_overview',
                name='月度总览通知',
                description='发送月度事工安排总览',
                event_timing=EventTiming(weekday=6, hour=19, minute=0, duration_minutes=30),  # 周日7点
                reminder_timing=ReminderTiming(minutes_before=0, hours_before=2),  # 提前2小时
                enabled=False  # 默认禁用
            )
        }
    
    def load_configs(self) -> bool:
        """加载配置"""
        try:
            # 优先从云端加载（使用统一的存储管理器）
            if self.storage_manager:
                config_data = self.storage_manager.read_file(self.CLOUD_CONFIG_PATH, "json")
                if config_data:
                    self._parse_config_data(config_data)
                    logger.info("从云端加载提醒配置成功")
                    return True
                else:
                    logger.info("云端配置文件不存在，尝试本地加载")
            
            # 回退到本地文件
            local_path = Path(self.CONFIG_FILE)
            if local_path.exists():
                with open(local_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self._parse_config_data(config_data)
                logger.info("从本地加载提醒配置成功")
                
                # 如果有存储管理器，同步到云端
                if self.storage_manager:
                    logger.info("正在同步本地配置到云端...")
                    self.save_configs()
                return True
            
            # 使用默认配置
            logger.info("未找到配置文件，使用默认配置")
            self.configs = self.get_default_configs()
            self.save_configs()  # 保存默认配置到云端和本地
            return True
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self.configs = self.get_default_configs()
            return False
    
    def _parse_config_data(self, config_data: Dict[str, Any]):
        """解析配置数据"""
        self.configs = {}
        
        # 解析配置格式
        if 'reminder_configs' in config_data:
            # 新格式
            for event_type, config_dict in config_data['reminder_configs'].items():
                try:
                    self.configs[event_type] = NotificationConfig.from_dict(config_dict)
                except Exception as e:
                    logger.error(f"解析配置失败 {event_type}: {e}")
        
        # 如果解析失败或配置为空，使用默认配置
        if not self.configs:
            logger.warning("配置解析失败，使用默认配置")
            self.configs = self.get_default_configs()
    
    def save_configs(self) -> bool:
        """保存配置"""
        try:
            # 构建配置数据
            config_data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'description': 'Grace Irvine Ministry Scheduler - 提醒时间配置',
                'reminder_configs': {}
            }
            
            for event_type, config in self.configs.items():
                config_data['reminder_configs'][event_type] = config.to_dict()
            
            # 使用统一的存储管理器保存（优先云端，同时本地备份）
            if self.storage_manager:
                success = self.storage_manager.write_file(
                    self.CLOUD_CONFIG_PATH, 
                    config_data, 
                    sync_to_cloud=True,  # 同步到云端
                    backup=True          # 创建备份
                )
                
                if success:
                    logger.info("提醒配置已成功保存（云端+本地）")
                    return True
                else:
                    logger.warning("存储管理器保存失败，尝试直接本地保存")
            
            # 回退：直接保存到本地
            local_path = Path(self.CONFIG_FILE)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info("提醒配置已保存到本地")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def get_config(self, event_type: str) -> Optional[NotificationConfig]:
        """获取指定类型的配置"""
        return self.configs.get(event_type)
    
    def update_config(self, event_type: str, config: NotificationConfig) -> bool:
        """更新配置"""
        try:
            self.configs[event_type] = config
            return self.save_configs()
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def get_all_configs(self) -> Dict[str, NotificationConfig]:
        """获取所有配置"""
        return self.configs.copy()
    
    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        try:
            self.configs = self.get_default_configs()
            return self.save_configs()
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False
    
    def validate_config(self, config: NotificationConfig) -> List[str]:
        """验证配置有效性"""
        errors = []
        
        # 验证事件时间
        if not 0 <= config.event_timing.weekday <= 6:
            errors.append(f"无效的星期几: {config.event_timing.weekday}")
        
        if not 0 <= config.event_timing.hour <= 23:
            errors.append(f"无效的小时: {config.event_timing.hour}")
        
        if not 0 <= config.event_timing.minute <= 59:
            errors.append(f"无效的分钟: {config.event_timing.minute}")
        
        if config.event_timing.duration_minutes <= 0:
            errors.append(f"无效的持续时间: {config.event_timing.duration_minutes}")
        
        # 验证提醒时间
        total_minutes = (config.reminder_timing.minutes_before + 
                        config.reminder_timing.hours_before * 60 + 
                        config.reminder_timing.days_before * 24 * 60)
        
        if total_minutes < 0:
            errors.append("提醒时间不能为负数")
        
        if total_minutes > 7 * 24 * 60:  # 最多提前一周
            errors.append("提醒时间不能超过7天")
        
        return errors
    
    def get_event_schedule_offsets(self) -> Dict[str, int]:
        """获取事件相对于主日的天数偏移
        
        返回格式: {event_type: days_before_sunday}
        """
        offsets = {}
        
        for event_type, config in self.configs.items():
            if not config.enabled:
                continue
                
            # 计算相对于周日的偏移
            # 周日 = 6, 周一 = 0, 周二 = 1, ..., 周六 = 5
            event_weekday = config.event_timing.weekday
            
            if event_weekday == 6:  # 周日
                offset = 0
            else:
                # 计算到下个周日的天数
                offset = -(6 - event_weekday)
            
            offsets[event_type] = offset
        
        return offsets

    def get_storage_status(self) -> Dict[str, Any]:
        """获取存储状态信息"""
        status = {
            'storage_manager_available': self.storage_manager is not None,
            'cloud_mode': False,
            'cloud_storage_available': False,
            'local_file_exists': False,
            'cloud_file_exists': False,
            'last_sync_time': None,
            'bucket_name': None
        }
        
        if self.storage_manager:
            status['cloud_mode'] = self.storage_manager.is_cloud_mode
            status['bucket_name'] = getattr(self.storage_manager.config, 'bucket_name', None)
            
            # 检查云端存储可用性
            if hasattr(self.storage_manager, 'storage_client') and self.storage_manager.storage_client:
                status['cloud_storage_available'] = True
            
            # 检查文件存在性
            try:
                cloud_data = self.storage_manager.read_file(self.CLOUD_CONFIG_PATH, "json")
                status['cloud_file_exists'] = cloud_data is not None
                
                if cloud_data and 'last_updated' in cloud_data:
                    status['last_sync_time'] = cloud_data['last_updated']
            except Exception:
                status['cloud_file_exists'] = False
        
        # 检查本地文件
        local_path = Path(self.CONFIG_FILE)
        status['local_file_exists'] = local_path.exists()
        
        return status

    def force_sync_to_cloud(self) -> bool:
        """强制同步当前配置到云端"""
        if not self.storage_manager:
            logger.error("存储管理器不可用，无法同步到云端")
            return False
        
        if not self.storage_manager.is_cloud_mode:
            logger.info("非云端模式，跳过云端同步")
            return True
        
        try:
            # 构建配置数据
            config_data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'description': 'Grace Irvine Ministry Scheduler - 提醒时间配置（强制同步）',
                'reminder_configs': {}
            }
            
            for event_type, config in self.configs.items():
                config_data['reminder_configs'][event_type] = config.to_dict()
            
            # 直接写入云端
            success = self.storage_manager.write_file(
                self.CLOUD_CONFIG_PATH, 
                config_data, 
                sync_to_cloud=True,
                backup=False  # 强制同步时不创建备份
            )
            
            if success:
                logger.info("配置已强制同步到云端")
                return True
            else:
                logger.error("强制同步到云端失败")
                return False
                
        except Exception as e:
            logger.error(f"强制同步失败: {e}")
            return False

# 全局实例
_reminder_manager = None

def get_reminder_manager() -> ReminderConfigManager:
    """获取提醒配置管理器单例"""
    global _reminder_manager
    if _reminder_manager is None:
        _reminder_manager = ReminderConfigManager()
    return _reminder_manager

def test_reminder_config():
    """测试提醒配置功能"""
    print("🧪 测试提醒配置管理器")
    print("=" * 50)
    
    # 创建管理器
    manager = get_reminder_manager()
    
    # 显示当前配置
    configs = manager.get_all_configs()
    print(f"📋 加载了 {len(configs)} 个配置:")
    
    for event_type, config in configs.items():
        print(f"{chr(10)}📅 {config.name} ({event_type}):")
        print(f"  启用: {'✅' if config.enabled else '❌'}")
        print(f"  事件时间: {config.event_timing.get_weekday_name()} {config.event_timing.hour:02d}:{config.event_timing.minute:02d}")
        print(f"  持续时间: {config.event_timing.duration_minutes} 分钟")
        print(f"  提醒设置: {config.reminder_timing.to_ics_trigger()}")
        
        # 验证配置
        errors = manager.validate_config(config)
        if errors:
            print(f"  ⚠️ 配置错误: {', '.join(errors)}")
        else:
            print(f"  ✅ 配置有效")
    
    # 测试偏移计算
    print(f"\n📊 事件时间偏移:")
    offsets = manager.get_event_schedule_offsets()
    for event_type, offset in offsets.items():
        config = configs[event_type]
        if offset == 0:
            print(f"  {config.name}: 主日当天")
        elif offset > 0:
            print(f"  {config.name}: 主日后 {offset} 天")
        else:
            print(f"  {config.name}: 主日前 {abs(offset)} 天")
    
    print(f"\n✅ 测试完成!")
    return True

if __name__ == "__main__":
    success = test_reminder_config()
    sys.exit(0 if success else 1)
