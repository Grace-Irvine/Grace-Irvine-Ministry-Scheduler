#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - 统一数据模型
Unified Data Models

定义项目中使用的所有数据结构，确保一致性
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Dict, Any, List
from enum import Enum

class ServiceRole(Enum):
    """服事角色枚举"""
    AUDIO_TECH = "音控"
    VIDEO_DIRECTOR = "导播/摄影" 
    PROPRESENTER_PLAY = "ProPresenter播放"
    PROPRESENTER_UPDATE = "ProPresenter更新"
    VIDEO_EDITOR = "视频剪辑"

@dataclass
class MinistryAssignment:
    """事工安排统一数据模型
    
    这是项目中唯一的事工安排数据结构，
    所有模块都应该使用这个统一的模型。
    """
    date: date
    
    # 核心服事角色
    audio_tech: Optional[str] = None          # 音控
    video_director: Optional[str] = None      # 导播/摄影
    propresenter_play: Optional[str] = None   # ProPresenter播放
    propresenter_update: Optional[str] = None # ProPresenter更新
    video_editor: Optional[str] = "靖铮"      # 视频剪辑（通常固定）
    
    # 扩展字段（向后兼容）
    screen_operator: Optional[str] = field(init=False, default=None)  # 屏幕操作（已合并到ProPresenter）
    camera_operator: Optional[str] = field(init=False, default=None)  # 摄像操作（已合并到video_director）
    propresenter: Optional[str] = field(init=False, default=None)     # ProPresenter（已分离为play和update）
    
    def __post_init__(self):
        """初始化后处理，确保向后兼容性"""
        # 向后兼容字段映射
        self.screen_operator = self.propresenter_play
        self.camera_operator = self.video_director
        self.propresenter = self.propresenter_play or self.propresenter_update
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'audio_tech': self.audio_tech,
            'video_director': self.video_director,
            'propresenter_play': self.propresenter_play,
            'propresenter_update': self.propresenter_update,
            'video_editor': self.video_editor
        }
    
    def get_all_assignments(self) -> Dict[str, str]:
        """获取所有非空的事工安排"""
        assignments = {}
        
        if self.audio_tech:
            assignments[ServiceRole.AUDIO_TECH.value] = self.audio_tech
        if self.video_director:
            assignments[ServiceRole.VIDEO_DIRECTOR.value] = self.video_director
        if self.propresenter_play:
            assignments[ServiceRole.PROPRESENTER_PLAY.value] = self.propresenter_play
        if self.propresenter_update:
            assignments[ServiceRole.PROPRESENTER_UPDATE.value] = self.propresenter_update
        if self.video_editor:
            assignments[ServiceRole.VIDEO_EDITOR.value] = self.video_editor
            
        return assignments
    
    def get_assignment_by_role(self, role: ServiceRole) -> Optional[str]:
        """根据角色获取安排的人员"""
        role_mapping = {
            ServiceRole.AUDIO_TECH: self.audio_tech,
            ServiceRole.VIDEO_DIRECTOR: self.video_director,
            ServiceRole.PROPRESENTER_PLAY: self.propresenter_play,
            ServiceRole.PROPRESENTER_UPDATE: self.propresenter_update,
            ServiceRole.VIDEO_EDITOR: self.video_editor
        }
        return role_mapping.get(role)
    
    def set_assignment_by_role(self, role: ServiceRole, person: str):
        """根据角色设置安排的人员"""
        if role == ServiceRole.AUDIO_TECH:
            self.audio_tech = person
        elif role == ServiceRole.VIDEO_DIRECTOR:
            self.video_director = person
        elif role == ServiceRole.PROPRESENTER_PLAY:
            self.propresenter_play = person
        elif role == ServiceRole.PROPRESENTER_UPDATE:
            self.propresenter_update = person
        elif role == ServiceRole.VIDEO_EDITOR:
            self.video_editor = person
    
    def has_assignments(self) -> bool:
        """检查是否有任何事工安排"""
        return any([
            self.audio_tech,
            self.video_director,
            self.propresenter_play,
            self.propresenter_update,
            self.video_editor
        ])
    
    def is_complete(self) -> bool:
        """检查是否有完整的主要服事安排"""
        return all([
            self.audio_tech,
            self.video_director,
            self.propresenter_play
        ])
    
    def get_missing_roles(self) -> List[ServiceRole]:
        """获取缺失的主要角色"""
        missing = []
        
        if not self.audio_tech:
            missing.append(ServiceRole.AUDIO_TECH)
        if not self.video_director:
            missing.append(ServiceRole.VIDEO_DIRECTOR)
        if not self.propresenter_play:
            missing.append(ServiceRole.PROPRESENTER_PLAY)
            
        return missing
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MinistryAssignment':
        """从字典创建实例"""
        # 处理日期
        if isinstance(data.get('date'), str):
            from datetime import datetime
            date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
        else:
            date_obj = data.get('date')
        
        return cls(
            date=date_obj,
            audio_tech=data.get('audio_tech'),
            video_director=data.get('video_director'),
            propresenter_play=data.get('propresenter_play'),
            propresenter_update=data.get('propresenter_update'),
            video_editor=data.get('video_editor', '靖铮')
        )
    
    @classmethod
    def from_legacy_schedule(cls, schedule) -> 'MinistryAssignment':
        """从旧的MinistrySchedule转换"""
        return cls(
            date=schedule.date,
            audio_tech=schedule.audio_tech,
            video_director=schedule.video_director,
            propresenter_play=schedule.propresenter_play,
            propresenter_update=schedule.propresenter_update,
            video_editor="靖铮"
        )
    
    @classmethod
    def from_legacy_assignment(cls, assignment) -> 'MinistryAssignment':
        """从旧的MinistryAssignment转换"""
        return cls(
            date=assignment.date,
            audio_tech=getattr(assignment, 'audio_tech', None),
            video_director=getattr(assignment, 'camera_operator', None) or getattr(assignment, 'video_director', None),
            propresenter_play=getattr(assignment, 'propresenter', None) or getattr(assignment, 'screen_operator', None),
            propresenter_update=getattr(assignment, 'propresenter_update', None),
            video_editor=getattr(assignment, 'video_editor', '靖铮')
        )

@dataclass 
class TemplateContext:
    """模板渲染上下文"""
    assignment: MinistryAssignment
    template_type: str
    additional_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationEvent:
    """通知事件数据结构"""
    event_type: str  # 'weekly_confirmation', 'saturday_reminder', 'monthly_overview'
    target_date: date
    assignment: Optional[MinistryAssignment] = None
    assignments: Optional[List[MinistryAssignment]] = None
    notification_content: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'event_type': self.event_type,
            'target_date': self.target_date.strftime('%Y-%m-%d'),
            'assignment': self.assignment.to_dict() if self.assignment else None,
            'assignments': [a.to_dict() for a in self.assignments] if self.assignments else None,
            'notification_content': self.notification_content
        }

@dataclass
class CalendarEvent:
    """日历事件数据结构"""
    uid: str
    summary: str
    description: str
    start_datetime: date
    end_datetime: date
    location: str = ""
    
    def to_ics_format(self) -> str:
        """转换为ICS格式"""
        # 这个方法将在日历生成器中实现
        pass

# 便捷函数
def create_ministry_assignment(
    date: date,
    audio_tech: str = None,
    video_director: str = None,
    propresenter_play: str = None,
    propresenter_update: str = None,
    video_editor: str = "靖铮"
) -> MinistryAssignment:
    """创建事工安排实例的便捷函数"""
    return MinistryAssignment(
        date=date,
        audio_tech=audio_tech,
        video_director=video_director,
        propresenter_play=propresenter_play,
        propresenter_update=propresenter_update,
        video_editor=video_editor
    )

def validate_ministry_assignment(assignment: MinistryAssignment) -> tuple[bool, List[str]]:
    """验证事工安排数据
    
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    if not assignment.date:
        errors.append("日期不能为空")
    
    if assignment.date and assignment.date < date.today():
        errors.append("日期不能是过去的日期")
    
    # 检查是否至少有一个主要角色
    main_roles = [assignment.audio_tech, assignment.video_director, assignment.propresenter_play]
    if not any(main_roles):
        errors.append("至少需要安排一个主要服事角色（音控、导播/摄影、ProPresenter播放）")
    
    return len(errors) == 0, errors

# 类型别名（向后兼容）
MinistrySchedule = MinistryAssignment  # 为了向后兼容
