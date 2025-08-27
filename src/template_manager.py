#!/usr/bin/env python3
"""
模板管理器 - Template Manager
负责加载、管理和渲染通知模板
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import date

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MinistryAssignment:
    """事工安排数据结构（用于类型提示）"""
    date: date
    audio_tech: str = ""
    screen_operator: str = ""
    camera_operator: str = ""
    propresenter: str = ""
    video_editor: str = "靖铮"

class NotificationTemplateManager:
    """通知模板管理器"""
    
    def __init__(self, template_file: str = "templates/notification_templates.yaml"):
        """初始化模板管理器
        
        Args:
            template_file: 模板文件路径
        """
        self.template_file = template_file
        self.templates = {}
        self.load_templates()
    
    def load_templates(self) -> bool:
        """加载模板文件
        
        Returns:
            是否加载成功
        """
        try:
            template_path = Path(self.template_file)
            if not template_path.exists():
                logger.error(f"Template file not found: {self.template_file}")
                self._create_default_templates()
                return False
            
            with open(template_path, 'r', encoding='utf-8') as f:
                self.templates = yaml.safe_load(f)
            
            logger.info(f"Successfully loaded templates from {self.template_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self._create_default_templates()
            return False
    
    def save_templates(self) -> bool:
        """保存模板到文件
        
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            template_path = Path(self.template_file)
            template_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.templates, f, allow_unicode=True, default_flow_style=False, indent=2)
            
            logger.info(f"Successfully saved templates to {self.template_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
            return False
    
    def _create_default_templates(self):
        """创建默认模板"""
        self.templates = {
            'weekly_confirmation': {
                'template': '【本周{month}月{day}日主日事工安排提醒】🕊️\n\n• 音控：{audio_tech}\n• 屏幕：{screen_operator}\n• 摄像/导播：{camera_operator}\n• Propresenter 制作：{propresenter}\n• 视频剪辑：{video_editor}\n\n请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏',
                'no_assignment_template': '【本周主日事工安排提醒】🕊️\n\n暂无本周事工安排，请联系协调员确认。',
                'defaults': {
                    'audio_tech': '待安排',
                    'screen_operator': '待安排',
                    'camera_operator': '待安排',
                    'propresenter': '待安排',
                    'video_editor': '靖铮'
                }
            },
            'sunday_reminder': {
                'template': '【主日服事提醒】✨\n明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  \n请各位同工提前到场：  \n- 音控：{audio_tech} 9:00到，随敬拜团排练\n- 屏幕：{screen_operator} 9:00到，随敬拜团排练\n- 摄像/导播: {camera_operator} 9:30到，检查预设机位\n\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌',
                'no_assignment_template': '【主日服事提醒】✨\n\n暂无明日事工安排，请联系协调员确认。',
                'defaults': {
                    'audio_tech': '待安排',
                    'screen_operator': '待安排',
                    'camera_operator': '待安排',
                    'propresenter': '待安排',
                    'video_editor': '靖铮'
                }
            }
        }
    
    def get_template(self, template_type: str, key: str = 'template') -> str:
        """获取指定模板
        
        Args:
            template_type: 模板类型 (weekly_confirmation, sunday_reminder, monthly_overview)
            key: 模板键名 (template, no_assignment_template)
            
        Returns:
            模板字符串
        """
        try:
            return self.templates.get(template_type, {}).get(key, '')
        except Exception as e:
            logger.error(f"Failed to get template {template_type}.{key}: {e}")
            return ''
    
    def set_template(self, template_type: str, key: str, template_content: str) -> bool:
        """设置模板内容
        
        Args:
            template_type: 模板类型
            key: 模板键名
            template_content: 模板内容
            
        Returns:
            是否设置成功
        """
        try:
            if template_type not in self.templates:
                self.templates[template_type] = {}
            
            self.templates[template_type][key] = template_content
            return True
            
        except Exception as e:
            logger.error(f"Failed to set template {template_type}.{key}: {e}")
            return False
    
    def get_defaults(self, template_type: str) -> Dict[str, str]:
        """获取默认值配置
        
        Args:
            template_type: 模板类型
            
        Returns:
            默认值字典
        """
        return self.templates.get(template_type, {}).get('defaults', {})
    
    def render_weekly_confirmation(self, assignment: Optional[MinistryAssignment] = None) -> str:
        """渲染周三确认通知
        
        周三确认通知只显示4种事工：
        1. 音控
        2. 导播/摄影
        3. ProPresenter播放
        4. ProPresenter更新
        
        Args:
            assignment: 事工安排数据
            
        Returns:
            渲染后的通知内容
        """
        if not assignment:
            return self.get_template('weekly_confirmation', 'no_assignment_template')
        
        # 构建周三确认通知内容
        content = f"【本周{assignment.date.month}月{assignment.date.day}日主日事工安排提醒】🕊️\n\n"
        
        # 只显示指定的4种事工，且只显示有人员安排的
        ministry_roles = [
            ("音控", assignment.audio_tech),
            ("导播/摄影", assignment.camera_operator),
            ("ProPresenter播放", assignment.propresenter),
            ("ProPresenter更新", assignment.video_editor)  # 视频剪辑对应ProPresenter更新
        ]
        
        for role_name, person_name in ministry_roles:
            if person_name and person_name.strip():  # 只显示有人员的角色
                content += f"• {role_name}：{person_name}\n"
        
        content += "\n请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏"
        
        return content
    
    def render_sunday_reminder(self, assignment: Optional[MinistryAssignment] = None) -> str:
        """渲染周六提醒通知
        
        周六提醒通知显示4种事工：
        1. 音控
        2. 导播/摄影
        3. ProPresenter播放
        4. ProPresenter更新
        
        Args:
            assignment: 事工安排数据
            
        Returns:
            渲染后的通知内容
        """
        if not assignment:
            return self.get_template('sunday_reminder', 'no_assignment_template')
        
        # 构建周六提醒通知内容
        content = "【主日服事提醒】✨\n"
        content += "明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜\n"
        content += "请各位同工提前到场：\n"
        
        # 显示指定的4种事工，且只显示有人员安排的
        ministry_roles = [
            ("音控", assignment.audio_tech, "9:00到，随敬拜团排练"),
            ("导播/摄影", assignment.camera_operator, "9:30到，检查摄影机水平，预设机位"),
            ("ProPresenter播放", assignment.propresenter, "9:00到，随敬拜团排练"),
            ("ProPresenter更新", assignment.video_editor, "提前准备内容")
        ]
        
        for role_name, person_name, arrival_instruction in ministry_roles:
            if person_name and person_name.strip():  # 只显示有人员的角色
                content += f"- {role_name}：{arrival_instruction}，{person_name}\n"
        
        content += "\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌"
        
        return content
    
    def render_monthly_overview(self, assignments: list, year: int, month: int, sheet_url: str = "") -> str:
        """渲染月度总览通知
        
        Args:
            assignments: 事工安排列表
            year: 年份
            month: 月份
            sheet_url: Google Sheets链接
            
        Returns:
            渲染后的通知内容
        """
        template = self.get_template('monthly_overview', 'template')
        
        # 构建安排列表文本
        schedule_text = ""
        if assignments:
            schedule_prefix = self.templates.get('monthly_overview', {}).get('schedule_prefix', '\n当月安排预览：\n')
            schedule_text = schedule_prefix
            
            item_format = self.templates.get('monthly_overview', {}).get('schedule_item_format', '• {month_day}: {roles}')
            role_separator = self.templates.get('monthly_overview', {}).get('role_separator', ', ')
            role_formats = self.templates.get('monthly_overview', {}).get('role_formats', {})
            
            for assignment in assignments:
                month_day = f"{assignment.date.month}/{assignment.date.day}"
                roles = []
                
                if assignment.audio_tech:
                    format_str = role_formats.get('audio_tech', '音控:{name}')
                    roles.append(format_str.format(name=assignment.audio_tech))
                if assignment.screen_operator:
                    format_str = role_formats.get('screen_operator', '屏幕:{name}')
                    roles.append(format_str.format(name=assignment.screen_operator))
                if assignment.camera_operator:
                    format_str = role_formats.get('camera_operator', '摄像:{name}')
                    roles.append(format_str.format(name=assignment.camera_operator))
                if assignment.propresenter:
                    format_str = role_formats.get('propresenter', '制作:{name}')
                    roles.append(format_str.format(name=assignment.propresenter))
                
                if roles:
                    roles_text = role_separator.join(roles)
                    schedule_text += item_format.format(month_day=month_day, roles=roles_text) + '\n'
        
        # 准备模板变量
        template_vars = {
            'year': year,
            'month': month,
            'sheet_url': sheet_url,
            'schedule_text': schedule_text
        }
        
        try:
            return template.format(**template_vars)
        except Exception as e:
            logger.error(f"Failed to render monthly overview template: {e}")
            return f"【{year}年{month:02d}月事工排班一览】📅\n\n模板渲染出错，请检查配置。"
    
    def get_all_templates(self) -> Dict[str, Any]:
        """获取所有模板配置
        
        Returns:
            完整的模板配置字典
        """
        return self.templates.copy()
    
    def update_templates(self, new_templates: Dict[str, Any]) -> bool:
        """批量更新模板配置
        
        Args:
            new_templates: 新的模板配置
            
        Returns:
            是否更新成功
        """
        try:
            self.templates.update(new_templates)
            return self.save_templates()
        except Exception as e:
            logger.error(f"Failed to update templates: {e}")
            return False
    
    def preview_weekly_confirmation(self, assignment: Optional[MinistryAssignment] = None) -> Dict[str, Any]:
        """预览周三确认通知的结构和内容
        
        Args:
            assignment: 事工安排数据
            
        Returns:
            包含预览信息的字典
        """
        preview_info = {
            'template_type': '周三确认通知',
            'description': '用于周三晚上发送的事工安排确认通知',
            'included_roles': [
                '音控',
                '导播/摄影', 
                'ProPresenter播放',
                'ProPresenter更新'
            ],
            'excluded_roles': ['屏幕操作', '视频剪辑（固定人员）'],
            'send_time': '周三晚上 20:00',
            'purpose': '确认本周主日的事工安排，处理冲突调换'
        }
        
        if assignment:
            preview_info['sample_content'] = self.render_weekly_confirmation(assignment)
            preview_info['data_mapping'] = {
                '音控': assignment.audio_tech,
                '导播/摄影': assignment.camera_operator,
                'ProPresenter播放': assignment.propresenter,
                'ProPresenter更新': assignment.video_editor
            }
        
        return preview_info
    
    def preview_sunday_reminder(self, assignment: Optional[MinistryAssignment] = None) -> Dict[str, Any]:
        """预览周六提醒通知的结构和内容
        
        Args:
            assignment: 事工安排数据
            
        Returns:
            包含预览信息的字典
        """
        preview_info = {
            'template_type': '周六提醒通知',
            'description': '用于周六晚上发送的主日服事提醒通知',
            'included_roles': [
                '音控',
                '导播/摄影',
                'ProPresenter播放',
                'ProPresenter更新'
            ],
            'excluded_roles': ['屏幕操作', '视频剪辑'],
            'send_time': '周六晚上 20:00',
            'purpose': '提醒明日主日服事，确认到场时间和注意事项',
            'arrival_times': {
                '音控': '9:00到，随敬拜团排练',
                '导播/摄影': '9:30到，检查摄影机水平，预设机位',
                'ProPresenter播放': '9:00到，随敬拜团排练',
                'ProPresenter更新': '提前准备内容'
            }
        }
        
        if assignment:
            preview_info['sample_content'] = self.render_sunday_reminder(assignment)
            preview_info['data_mapping'] = {
                '音控': assignment.audio_tech,
                '导播/摄影': assignment.camera_operator,
                'ProPresenter播放': assignment.propresenter
            }
        
        return preview_info
    
    def get_template_structure(self) -> Dict[str, Any]:
        """获取模板结构概览
        
        Returns:
            模板结构信息
        """
        return {
            'template_types': {
                'weekly_confirmation': {
                    'name': '周三确认通知',
                    'roles': ['音控', '导播/摄影', 'ProPresenter播放', 'ProPresenter更新'],
                    'send_time': '周三 20:00',
                    'method': 'render_weekly_confirmation()'
                },
                'sunday_reminder': {
                    'name': '周六提醒通知',
                    'roles': ['音控', '导播/摄影', 'ProPresenter播放', 'ProPresenter更新'],
                    'send_time': '周六 20:00',
                    'method': 'render_sunday_reminder()'
                },
                'monthly_overview': {
                    'name': '月度总览通知',
                    'roles': ['所有角色'],
                    'send_time': '每月1日 09:00',
                    'method': 'render_monthly_overview()'
                }
            },
            'data_source': 'Google Sheets',
            'configuration': {
                'audio_tech': 'Q列 - 音控',
                'camera_operator': 'S列 - 导播/摄影',
                'propresenter': 'T列 - ProPresenter播放',
                'video_editor': 'U列 - ProPresenter更新/视频剪辑'
            }
        }

# 便捷函数
def create_template_manager(template_file: str = "templates/notification_templates.yaml") -> NotificationTemplateManager:
    """创建模板管理器实例"""
    return NotificationTemplateManager(template_file)

def get_default_template_manager() -> NotificationTemplateManager:
    """获取默认的模板管理器实例"""
    return NotificationTemplateManager()
