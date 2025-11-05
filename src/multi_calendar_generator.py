#!/usr/bin/env python3
"""
多类型 ICS 日历生成器
支持生成媒体部、儿童部、每周概览三种类型的 ICS 日历
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.json_data_reader import get_json_data_reader
from src.ics_notification_config import get_config_manager, NotificationTiming
from src.models import MinistryAssignment
from src.dynamic_template_manager import DynamicTemplateManager
from src.scripture_manager import get_scripture_manager

logger = logging.getLogger(__name__)


def escape_ics_text(text: str) -> str:
    """转义 ICS 文本中的特殊字符"""
    if not text:
        return ""
    text = str(text)
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    return text


def is_placeholder_text(value: str) -> bool:
    """判断是否为占位符文本
    
    Args:
        value: 要检查的值
    
    Returns:
        如果是占位符文本返回True，否则返回False
    """
    if not value or not isinstance(value, str):
        return False
    
    value = value.strip()
    
    # 常见的占位符文本模式
    placeholder_patterns = [
        '音控人员', '音控', '音频人员',
        '导播/摄影', '导播', '摄影', '摄像',
        'ProPresenter播放', 'ProPresenter', 'PPT播放', 'PPT',
        'ProPresenter更新', 'PPT更新',
        '视频剪辑', '剪辑',
        '主日学老师', '老师', '儿童部老师',
        '助教', '周日助教', '助教1', '助教2', '助教3',
        '敬拜带领', '敬拜', '敬拜同工', '敬拜同工1', '敬拜同工2',
        '司琴', '钢琴', '钢琴手',
        '周五老师', '儿童部',
        '待安排', '待定', 'TBD', '待确认'
    ]
    
    # 检查是否完全匹配占位符文本
    return value in placeholder_patterns


def extract_person_name(role_value: Any) -> str:
    """从岗位值中提取实际人名
    
    支持多种数据格式：
    - 字典格式：{"id": "xxx", "name": "实际姓名"}
    - 列表格式：["姓名1", "姓名2"] 或 [{"id": "xxx", "name": "姓名"}]
    - 字符串格式：直接的人名或占位符文本
    
    Args:
        role_value: 岗位值（可能是字典、列表或字符串）
    
    Returns:
        提取的实际人名，如果是占位符则返回空字符串
    """
    if not role_value:
        return ''
    
    # 如果是字典，提取 name 字段
    if isinstance(role_value, dict):
        name = role_value.get('name', '')
        if name and not is_placeholder_text(name):
            return str(name).strip()
        return ''
    
    # 如果是列表，取第一个非占位符的值
    if isinstance(role_value, list):
        for item in role_value:
            if isinstance(item, dict):
                name = item.get('name', '')
            else:
                name = str(item).strip()
            
            if name and not is_placeholder_text(name):
                return name
        return ''
    
    # 如果是字符串，检查是否为占位符
    name = str(role_value).strip()
    if name and not is_placeholder_text(name):
        return name
    
    return ''


def calculate_event_date(sunday_date: date, relative_days: int) -> date:
    """计算事件日期（相对于主日）
    
    Args:
        sunday_date: 主日日期（周日）
        relative_days: 相对于主日的天数偏移（负数表示主日之前）
    
    Returns:
        计算出的事件日期
    """
    return sunday_date + timedelta(days=relative_days)


def create_ics_event(
    uid: str,
    summary: str,
    description: str,
    start_dt: datetime,
    end_dt: datetime,
    location: str = "Grace Irvine 教会",
    reminder_trigger: str = "-PT30M"
) -> str:
    """创建单个 ICS 事件"""
    start_str = start_dt.strftime('%Y%m%dT%H%M%S')
    end_str = end_dt.strftime('%Y%m%dT%H%M%S')
    dtstamp_str = datetime.now().strftime('%Y%m%dT%H%M%S')
    
    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp_str}",
        f"DTSTART:{start_str}",
        f"DTEND:{end_str}",
        f"SUMMARY:{escape_ics_text(summary)}",
        f"DESCRIPTION:{escape_ics_text(description)}",
        f"LOCATION:{escape_ics_text(location)}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:提醒：{escape_ics_text(summary)}",
        f"TRIGGER:{reminder_trigger}",
        "END:VALARM",
        "END:VEVENT"
    ]
    
    return "\n".join(event_lines)


def format_media_team_summary(assignment, schedule_date: date, event_type: str = "确认") -> str:
    """格式化媒体部事件标题，包含具体人名和角色
    
    Args:
        assignment: MinistryAssignment 对象（字段值应该已经通过extract_person_name处理过）
        schedule_date: 主日日期
        event_type: 事件类型（"确认" 或 "提醒"）
    
    Returns:
        格式化后的标题
    """
    roles = []
    # assignment中的字段值应该已经通过extract_person_name处理过，过滤了占位符文本
    # 但为了安全起见，再次检查并过滤空值
    if assignment.audio_tech and assignment.audio_tech.strip():
        roles.append(f"音控:{assignment.audio_tech}")
    if assignment.video_director and assignment.video_director.strip():
        roles.append(f"导播:{assignment.video_director}")
    if assignment.propresenter_play and assignment.propresenter_play.strip():
        roles.append(f"播放:{assignment.propresenter_play}")
    if assignment.propresenter_update and assignment.propresenter_update.strip():
        roles.append(f"更新:{assignment.propresenter_update}")
    
    if roles:
        roles_text = " | ".join(roles)
        return f"媒体部{event_type}通知 ({schedule_date.month}/{schedule_date.day}) - {roles_text}"
    else:
        return f"媒体部{event_type}通知 ({schedule_date.month}/{schedule_date.day})"


def format_children_team_summary(children: dict, schedule_date: date, event_type: str = "确认") -> str:
    """格式化儿童部事件标题，包含具体人名和角色
    
    Args:
        children: 儿童部数据字典
        schedule_date: 主日日期
        event_type: 事件类型（"确认" 或 "提醒"）
    
    Returns:
        格式化后的标题
    """
    roles = []
    # 提取实际人名，过滤占位符文本
    teacher_name = extract_person_name(children.get('teacher') or children.get('sunday_child_teacher', ''))
    if teacher_name:
        roles.append(f"老师:{teacher_name}")
    
    assistant_name = extract_person_name(children.get('assistant') or children.get('sunday_child_assistant_1', ''))
    if assistant_name:
        roles.append(f"助教:{assistant_name}")
    
    worship_name = extract_person_name(children.get('worship') or children.get('sunday_child_worship', ''))
    if worship_name:
        roles.append(f"敬拜:{worship_name}")
    
    if roles:
        roles_text = " | ".join(roles)
        return f"儿童部{event_type}通知 ({schedule_date.month}/{schedule_date.day}) - {roles_text}"
    else:
        return f"儿童部{event_type}通知 ({schedule_date.month}/{schedule_date.day})"


def format_weekly_overview_summary(overview_data: dict, sunday_date: date) -> str:
    """格式化每周概览事件标题，包含证道信息和主要服事人员
    
    Args:
        overview_data: 每周概览数据字典
        sunday_date: 主日日期
    
    Returns:
        格式化后的标题
    """
    sermon = overview_data.get('sermon', {})
    volunteers = overview_data.get('volunteers', {})
    
    title_parts = []
    
    # 添加证道信息
    if sermon.get('title'):
        title_parts.append(f"证道:{sermon['title']}")
    if sermon.get('speaker'):
        title_parts.append(f"讲员:{sermon['speaker']}")
    
    # 添加主要服事人员（每个部门取第一个岗位）
    role_map = {
        'audio': '音控',
        'audio_tech': '音控',
        'sound_control': '音控',
        'video': '导播',
        'video_director': '导播',
        'director': '导播',
        'propresenter_play': '播放',
        'propresenter_update': '更新',
        'teacher': '老师',
        'sunday_child_teacher': '老师',
        'assistant': '助教',
        'sunday_child_assistant_1': '助教',
        'worship_lead': '敬拜',
        'worship': '敬拜',
        'leader': '敬拜',
        'lead': '敬拜',
        'pianist': '司琴'
    }
    
    for dept_key, dept_roles in volunteers.items():
        if not isinstance(dept_roles, dict):
            continue
        
        # 取第一个非空岗位
        for role_key, role_value in dept_roles.items():
            if not role_value:
                continue
            
            # 检查是否为有效值
            is_valid = False
            if isinstance(role_value, list):
                is_valid = len(role_value) > 0 and any(v for v in role_value if v)
            elif isinstance(role_value, str):
                is_valid = bool(role_value.strip())
            else:
                is_valid = bool(role_value)
            
            if is_valid:
                role_display = role_map.get(role_key, role_key.replace('_', ' '))
                # 使用 extract_person_name 提取实际人名，过滤占位符文本
                person = extract_person_name(role_value)
                
                if person:
                    title_parts.append(f"{role_display}:{person}")
                    break  # 每个部门只取一个岗位
    
    if title_parts:
        summary_text = " | ".join(title_parts[:4])  # 最多显示4个信息，避免标题过长
        return f"每周事工通知 ({sunday_date.month}/{sunday_date.day}) - {summary_text}"
    else:
        return f"每周事工通知 ({sunday_date.month}/{sunday_date.day})"


def generate_media_team_calendar() -> Optional[str]:
    """生成媒体部服事日历
    
    Returns:
        ICS 日历内容字符串，如果失败返回 None
    """
    try:
        logger.info("📅 生成媒体部服事日历...")
        
        # 获取数据读取器
        data_reader = get_json_data_reader()
        config_manager = get_config_manager()
        
        # 获取完整的排程数据（包含证道信息）
        schedules = data_reader.get_service_schedule()
        
        if not schedules:
            logger.warning("未找到排程数据")
            return None
        
        # 获取配置
        calendar_config = config_manager.config.get_calendar_config('media-team')
        if not calendar_config or not calendar_config.enabled:
            logger.warning("媒体部日历未启用")
            return None
        
        # 获取模板管理器和经文管理器
        template_manager = DynamicTemplateManager()
        scripture_manager = get_scripture_manager()
        
        # 创建 ICS 内容
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Media Team Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 媒体部服事日历",
            "X-WR-CALDESC:媒体部同工服事安排日历（自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        cutoff_date = today - timedelta(days=28)  # 保留过去4周
        events_created = 0
        
        # 转换为 MinistryAssignment 对象以便使用模板管理器
        from src.models import MinistryAssignment
        
        for schedule_data in schedules:
            try:
                schedule_date = datetime.strptime(schedule_data['date'], '%Y-%m-%d').date()
            except:
                continue
            
            if schedule_date < cutoff_date:
                continue
            
            # 动态获取媒体部数据（支持 technical 或 media 部门）
            volunteers = schedule_data.get('volunteers', {})
            # 支持多种部门名称
            media = volunteers.get('technical') or volunteers.get('media', {})
            
            if not media:
                continue
            
            # 调试：记录原始数据格式（使用 INFO 级别，方便调试）
            logger.info(f"📅 处理日期: {schedule_date}")
            logger.info(f"📊 媒体部原始数据: {media}")
            for role_key in ['audio', 'audio_tech', 'sound_control', 'video', 'video_director', 'director', 'propresenter_play', 'propresenter_update']:
                role_value = media.get(role_key)
                if role_value is not None:
                    logger.info(f"   {role_key}: {type(role_value).__name__} = {repr(role_value)}")
            
            # 创建 MinistryAssignment 对象
            # 动态提取岗位数据，支持多种字段名格式（从 JSON 中直接提取）
            # 注意：json_data_reader 应该已经将字典格式转换为字符串，但为了健壮性，这里也处理字典格式
            # 使用 extract_person_name 过滤占位符文本，只保留实际人名
            
            # 获取原始值（可能是字符串、字典或None）
            # 注意：如果json_data_reader没有正确提取字典格式，这里需要直接处理字典
            def get_role_value(role_dict, *keys):
                """从字典中获取岗位值，支持多个键名"""
                for key in keys:
                    value = role_dict.get(key)
                    if value is not None and value != '':
                        return value
                return ''
            
            audio_value = get_role_value(media, 'audio', 'audio_tech', 'sound_control')
            video_value = get_role_value(media, 'video', 'video_director', 'director')
            play_value = get_role_value(media, 'propresenter_play')
            update_value = get_role_value(media, 'propresenter_update')
            
            # 提取实际人名（过滤占位符文本）
            # extract_person_name 支持字符串、字典和列表格式
            # 如果json_data_reader没有正确提取字典格式，这里会直接处理字典
            audio_name = extract_person_name(audio_value) if audio_value else ''
            video_name = extract_person_name(video_value) if video_value else ''
            play_name = extract_person_name(play_value) if play_value else ''
            update_name = extract_person_name(update_value) if update_value else ''
            
            # 调试：记录提取结果（使用 INFO 级别，方便调试）
            logger.info(f"✨ 提取结果:")
            logger.info(f"   音控: {repr(audio_value)} ({type(audio_value).__name__}) -> {repr(audio_name)}")
            logger.info(f"   导播: {repr(video_value)} ({type(video_value).__name__}) -> {repr(video_name)}")
            logger.info(f"   播放: {repr(play_value)} ({type(play_value).__name__}) -> {repr(play_name)}")
            logger.info(f"   更新: {repr(update_value)} ({type(update_value).__name__}) -> {repr(update_name)}")
            
            # 如果所有字段都是空的，记录警告
            if not any([audio_name, video_name, play_name, update_name]):
                logger.warning(f"⚠️  日期 {schedule_date} 的媒体部数据全部为空，可能是占位符文本或数据格式问题")
                logger.warning(f"   原始数据: {media}")
            
            assignment = MinistryAssignment(
                date=schedule_date,
                audio_tech=audio_name,
                video_director=video_name,
                propresenter_play=play_name,
                propresenter_update=update_name
            )
            
            # 周三确认通知
            wednesday_config = calendar_config.get_notification('wednesday_confirmation')
            if wednesday_config:
                try:
                    event_date = calculate_event_date(schedule_date, wednesday_config.relative_to_sunday)
                    
                    if event_date >= today - timedelta(days=7):
                        # 使用模板管理器生成包含经文的通知内容
                        try:
                            notification_content = template_manager.render_weekly_confirmation(
                                schedule_date, 
                                assignment, 
                                for_ics_generation=True
                            )
                            description = f"发送内容：\n\n{notification_content}"
                        except Exception as e:
                            logger.warning(f"使用模板生成失败，使用简化内容: {e}")
                            # 回退到简化内容
                            description_lines = [
                                f"主日日期: {schedule_date.strftime('%Y-%m-%d')}",
                                "",
                                "媒体部服事安排:",
                            ]
                            
                            if assignment.audio_tech:
                                description_lines.append(f"音控: {assignment.audio_tech}")
                            if assignment.video_director:
                                description_lines.append(f"导播/摄影: {assignment.video_director}")
                            if assignment.propresenter_play:
                                description_lines.append(f"ProPresenter播放: {assignment.propresenter_play}")
                            if assignment.propresenter_update:
                                description_lines.append(f"ProPresenter更新: {assignment.propresenter_update}")
                            
                            description = "\n".join(description_lines)
                        
                        # 计算时间
                        start_dt = datetime.combine(event_date, wednesday_config.to_time())
                        end_dt = start_dt + timedelta(minutes=wednesday_config.duration_minutes)
                        
                        # 创建事件
                        summary = format_media_team_summary(assignment, schedule_date, "确认")
                        event_ics = create_ics_event(
                            uid=f"media_wednesday_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                            summary=summary,
                            description=description,
                            start_dt=start_dt,
                            end_dt=end_dt,
                            reminder_trigger=wednesday_config.to_ics_trigger()
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                except Exception as e:
                    logger.error(f"创建周三事件失败: {e}")
            
            # 周六提醒通知
            saturday_config = calendar_config.get_notification('saturday_reminder')
            if saturday_config:
                try:
                    event_date = calculate_event_date(schedule_date, saturday_config.relative_to_sunday)
                    
                    if event_date >= today - timedelta(days=7):
                        # 使用模板管理器生成包含经文的通知内容
                        try:
                            notification_content = template_manager.render_saturday_reminder(
                                schedule_date, 
                                assignment
                            )
                            description = f"发送内容：\n\n{notification_content}"
                        except Exception as e:
                            logger.warning(f"使用模板生成失败，使用简化内容: {e}")
                            # 回退到简化内容
                            description_lines = [
                                f"主日日期: {schedule_date.strftime('%Y-%m-%d')}",
                                "",
                                "媒体部服事安排:",
                            ]
                            
                            if assignment.audio_tech:
                                description_lines.append(f"音控: {assignment.audio_tech}")
                            if assignment.video_director:
                                description_lines.append(f"导播/摄影: {assignment.video_director}")
                            if assignment.propresenter_play:
                                description_lines.append(f"ProPresenter播放: {assignment.propresenter_play}")
                            if assignment.propresenter_update:
                                description_lines.append(f"ProPresenter更新: {assignment.propresenter_update}")
                            
                            description = "\n".join(description_lines)
                        
                        # 计算时间
                        start_dt = datetime.combine(event_date, saturday_config.to_time())
                        end_dt = start_dt + timedelta(minutes=saturday_config.duration_minutes)
                        
                        # 创建事件
                        summary = format_media_team_summary(assignment, schedule_date, "提醒")
                        event_ics = create_ics_event(
                            uid=f"media_saturday_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                            summary=summary,
                            description=description,
                            start_dt=start_dt,
                            end_dt=end_dt,
                            reminder_trigger=saturday_config.to_ics_trigger()
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                except Exception as e:
                    logger.error(f"创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        logger.info(f"✅ 媒体部日历生成完成: {events_created} 个事件")
        return ics_content
        
    except Exception as e:
        logger.error(f"❌ 生成媒体部日历失败: {e}")
        return None


def generate_children_team_calendar() -> Optional[str]:
    """生成儿童部服事日历
    
    Returns:
        ICS 日历内容字符串，如果失败返回 None
    """
    try:
        logger.info("📅 生成儿童部服事日历...")
        
        # 获取数据读取器
        data_reader = get_json_data_reader()
        config_manager = get_config_manager()
        
        # 获取完整的排程数据（包含证道信息）
        schedules = data_reader.get_service_schedule()
        
        if not schedules:
            logger.warning("未找到排程数据")
            return None
        
        # 获取配置
        calendar_config = config_manager.config.get_calendar_config('children-team')
        if not calendar_config or not calendar_config.enabled:
            logger.warning("儿童部日历未启用")
            return None
        
        # 获取模板管理器
        template_manager = DynamicTemplateManager()
        
        # 创建 ICS 内容
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Children Team Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 儿童部服事日历",
            "X-WR-CALDESC:儿童部同工服事安排日历（自动更新）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        cutoff_date = today - timedelta(days=28)  # 保留过去4周
        events_created = 0
        
        # 转换为 MinistryAssignment 对象以便使用模板管理器
        from src.models import MinistryAssignment
        
        for schedule_data in schedules:
            try:
                schedule_date = datetime.strptime(schedule_data['date'], '%Y-%m-%d').date()
            except:
                continue
            
            if schedule_date < cutoff_date:
                continue
            
            # 动态获取儿童部数据（支持 education 或 children 部门）
            children = volunteers.get('education') or volunteers.get('children', {})
            
            if not children:
                continue
            
            # 提取实际人名（过滤占位符文本）
            # 使用 extract_person_name 确保只提取实际人名
            teacher_value = children.get('teacher') or children.get('sunday_child_teacher', '')
            assistant_value = children.get('assistant') or children.get('sunday_child_assistant_1', '')
            worship_value = children.get('worship') or children.get('sunday_child_worship', '')
            
            teacher_name = extract_person_name(teacher_value) if teacher_value else ''
            assistant_name = extract_person_name(assistant_value) if assistant_value else ''
            worship_name = extract_person_name(worship_value) if worship_value else ''
            
            # 如果所有字段都是空的，跳过此日期
            if not any([teacher_name, assistant_name, worship_name]):
                logger.debug(f"日期 {schedule_date} 的儿童部数据全部为空或占位符，跳过")
                continue
            
            # 创建 MinistryAssignment 对象（儿童部数据需要特殊处理）
            # 为了使用模板管理器，我们需要创建一个基本的 assignment 对象
            assignment = MinistryAssignment(
                date=schedule_date,
                audio_tech=None,
                video_director=None,
                propresenter_play=None,
                propresenter_update=None
            )
            
            # 周三确认通知
            wednesday_config = calendar_config.get_notification('wednesday_confirmation')
            if wednesday_config:
                try:
                    event_date = calculate_event_date(schedule_date, wednesday_config.relative_to_sunday)
                    
                    if event_date >= today - timedelta(days=7):
                        # 使用模板管理器生成包含经文的通知内容
                        try:
                            notification_content = template_manager.render_weekly_confirmation(
                                schedule_date, 
                                assignment, 
                                for_ics_generation=True
                            )
                            # 添加儿童部服事信息（使用已提取的人名）
                            children_info = []
                            if teacher_name:
                                children_info.append(f"主日学老师: {teacher_name}")
                            if assistant_name:
                                children_info.append(f"助教: {assistant_name}")
                            if worship_name:
                                children_info.append(f"敬拜带领: {worship_name}")
                            
                            if children_info:
                                notification_content += "\n\n儿童部服事安排:\n" + "\n".join(children_info)
                            
                            description = f"发送内容：\n\n{notification_content}"
                        except Exception as e:
                            logger.warning(f"使用模板生成失败，使用简化内容: {e}")
                            # 回退到简化内容（使用已提取的人名）
                            description_lines = [
                                f"主日日期: {schedule_date.strftime('%Y-%m-%d')}",
                                "",
                                "儿童部服事安排:",
                            ]
                            
                            if teacher_name:
                                description_lines.append(f"主日学老师: {teacher_name}")
                            if assistant_name:
                                description_lines.append(f"助教: {assistant_name}")
                            if worship_name:
                                description_lines.append(f"敬拜带领: {worship_name}")
                            
                            description = "\n".join(description_lines)
                        
                        # 计算时间
                        start_dt = datetime.combine(event_date, wednesday_config.to_time())
                        end_dt = start_dt + timedelta(minutes=wednesday_config.duration_minutes)
                        
                        # 创建事件（使用提取的人名字典）
                        children_dict = {}
                        if teacher_name:
                            children_dict['teacher'] = teacher_name
                        if assistant_name:
                            children_dict['assistant'] = assistant_name
                        if worship_name:
                            children_dict['worship'] = worship_name
                        summary = format_children_team_summary(children_dict, schedule_date, "确认")
                        event_ics = create_ics_event(
                            uid=f"children_wednesday_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                            summary=summary,
                            description=description,
                            start_dt=start_dt,
                            end_dt=end_dt,
                            reminder_trigger=wednesday_config.to_ics_trigger()
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                except Exception as e:
                    logger.error(f"创建周三事件失败: {e}")
            
            # 周六提醒通知
            saturday_config = calendar_config.get_notification('saturday_reminder')
            if saturday_config:
                try:
                    event_date = calculate_event_date(schedule_date, saturday_config.relative_to_sunday)
                    
                    if event_date >= today - timedelta(days=7):
                        # 使用模板管理器生成包含经文的通知内容
                        try:
                            notification_content = template_manager.render_saturday_reminder(
                                schedule_date, 
                                assignment
                            )
                            # 添加儿童部服事信息（使用已提取的人名）
                            children_info = []
                            if teacher_name:
                                children_info.append(f"主日学老师: {teacher_name}")
                            if assistant_name:
                                children_info.append(f"助教: {assistant_name}")
                            if worship_name:
                                children_info.append(f"敬拜带领: {worship_name}")
                            
                            if children_info:
                                notification_content += "\n\n儿童部服事安排:\n" + "\n".join(children_info)
                            
                            description = f"发送内容：\n\n{notification_content}"
                        except Exception as e:
                            logger.warning(f"使用模板生成失败，使用简化内容: {e}")
                            # 回退到简化内容（使用已提取的人名）
                            description_lines = [
                                f"主日日期: {schedule_date.strftime('%Y-%m-%d')}",
                                "",
                                "儿童部服事安排:",
                            ]
                            
                            if teacher_name:
                                description_lines.append(f"主日学老师: {teacher_name}")
                            if assistant_name:
                                description_lines.append(f"助教: {assistant_name}")
                            if worship_name:
                                description_lines.append(f"敬拜带领: {worship_name}")
                            
                            description = "\n".join(description_lines)
                        
                        # 计算时间
                        start_dt = datetime.combine(event_date, saturday_config.to_time())
                        end_dt = start_dt + timedelta(minutes=saturday_config.duration_minutes)
                        
                        # 创建事件（使用提取的人名字典）
                        children_dict = {}
                        if teacher_name:
                            children_dict['teacher'] = teacher_name
                        if assistant_name:
                            children_dict['assistant'] = assistant_name
                        if worship_name:
                            children_dict['worship'] = worship_name
                        summary = format_children_team_summary(children_dict, schedule_date, "提醒")
                        event_ics = create_ics_event(
                            uid=f"children_saturday_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                            summary=summary,
                            description=description,
                            start_dt=start_dt,
                            end_dt=end_dt,
                            reminder_trigger=saturday_config.to_ics_trigger()
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                except Exception as e:
                    logger.error(f"创建周六事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        logger.info(f"✅ 儿童部日历生成完成: {events_created} 个事件")
        return ics_content
        
    except Exception as e:
        logger.error(f"❌ 生成儿童部日历失败: {e}")
        return None


def generate_weekly_overview_calendar() -> Optional[str]:
    """生成每周全部事工概览日历
    
    Returns:
        ICS 日历内容字符串，如果失败返回 None
    """
    try:
        logger.info("📅 生成每周全部事工概览日历...")
        
        # 获取数据读取器
        data_reader = get_json_data_reader()
        config_manager = get_config_manager()
        
        # 获取完整数据
        weekly_overviews = data_reader.get_weekly_overview()
        
        if not weekly_overviews:
            logger.warning("未找到每周概览数据")
            return None
        
        # 获取配置
        calendar_config = config_manager.config.get_calendar_config('weekly-overview')
        if not calendar_config or not calendar_config.enabled:
            logger.warning("每周概览日历未启用")
            return None
        
        # 获取模板管理器和经文管理器
        template_manager = DynamicTemplateManager()
        scripture_manager = get_scripture_manager()
        
        # 创建 ICS 内容
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Weekly Overview Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 每周全部事工概览",
            "X-WR-CALDESC:每周全部事工安排概览（包含证道和所有服事）",
            "X-WR-TIMEZONE:America/Los_Angeles",
            f"X-WR-CALDESC:最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        today = date.today()
        cutoff_date = today - timedelta(days=28)  # 保留过去4周
        events_created = 0
        
        for overview_data in weekly_overviews:
            sunday_date = overview_data['date']
            
            if sunday_date < cutoff_date:
                continue
            
            # 周一全部事工通知
            monday_config = calendar_config.get_notification('monday_overview')
            if monday_config:
                try:
                    event_date = calculate_event_date(sunday_date, monday_config.relative_to_sunday)
                    
                    if event_date >= today - timedelta(days=7):
                        # 获取经文分享
                        scripture_sharing = ""
                        try:
                            current_scripture = scripture_manager.get_scripture_by_date(sunday_date)
                            if current_scripture:
                                scripture_sharing = scripture_manager.format_scripture_for_template(current_scripture)
                        except Exception as e:
                            logger.warning(f"获取经文分享失败: {e}")
                        
                        # 生成通知内容
                        description_lines = [
                            f"主日日期: {sunday_date.strftime('%Y-%m-%d')}",
                            "",
                            "=== 证道信息 ===",
                        ]
                        
                        sermon = overview_data.get('sermon', {})
                        if sermon:
                            # 参考: https://github.com/Grace-Irvine/Grace-Irvine-Ministry-Clean/blob/main/config/config.json
                            if sermon.get('title'):
                                description_lines.append(f"讲道标题: {sermon['title']}")
                            if sermon.get('speaker'):
                                description_lines.append(f"讲员: {sermon['speaker']}")
                            if sermon.get('reading'):
                                description_lines.append(f"读经: {sermon['reading']}")
                            if sermon.get('series'):
                                description_lines.append(f"讲道系列: {sermon['series']}")
                            if sermon.get('scripture'):
                                description_lines.append(f"经文: {sermon['scripture']}")
                            if sermon.get('scripture_text'):
                                description_lines.append(f"经文内容: {sermon['scripture_text']}")
                        
                        # 添加经文分享
                        if scripture_sharing:
                            description_lines.append("")
                            description_lines.append("=== 经文分享 ===")
                            description_lines.append(scripture_sharing)
                        
                        description_lines.append("")
                        description_lines.append("=== 服事安排 ===")
                        
                        volunteers = overview_data.get('volunteers', {})
                        
                        # 动态提取所有部门和岗位，不硬编码部门名称
                        # 部门名称映射（可选，用于显示友好的中文名称）
                        dept_name_map = {
                            'technical': '媒体部',
                            'media': '媒体部',
                            'education': '儿童部',
                            'children': '儿童部',
                            'worship': '敬拜团队',
                            'outreach': '外展联络',
                            'sermon': '证道'
                        }
                        
                        # 岗位名称映射（可选，用于显示友好的中文名称）
                        # 如果JSON中没有岗位的中文名称，可以使用这个映射
                        role_name_map = {
                            'audio': '音控',
                            'sound_control': '音控',
                            'video': '导播/摄影',
                            'director': '导播/摄影',
                            'propresenter_play': 'ProPresenter播放',
                            'propresenter_update': 'ProPresenter更新',
                            'video_editor': '视频剪辑',
                            'worship_lead': '敬拜带领',
                            'leader': '敬拜带领',
                            'lead': '敬拜带领',
                            'pianist': '司琴',
                            'friday_child_ministry': '周五老师',
                            'teacher': '主日学老师',
                            'sunday_child_teacher': '主日学老师',
                            'sunday_child_assistant_1': '周日助教1',
                            'sunday_child_assistant_2': '周日助教2',
                            'sunday_child_assistant_3': '周日助教3',
                            'assistant': '助教'
                        }
                        
                        # 遍历所有部门
                        for dept_key, dept_roles in volunteers.items():
                            if not dept_roles or not isinstance(dept_roles, dict):
                                continue
                            
                            # 获取部门显示名称
                            dept_display_name = dept_name_map.get(dept_key, dept_key)
                            description_lines.append("")
                            description_lines.append(f"{dept_display_name}:")
                            
                            # 遍历该部门的所有岗位
                            for role_key, role_value in dept_roles.items():
                                if not role_value:
                                    continue
                                
                                # 获取岗位显示名称
                                role_display_name = role_name_map.get(role_key, role_key.replace('_', ' '))
                                
                                # 使用 extract_person_name 提取实际人名，过滤占位符文本
                                person_name = extract_person_name(role_value)
                                if not person_name:
                                    continue  # 跳过占位符文本
                                
                                # 处理岗位值
                                if isinstance(role_value, list):
                                    # 如果是列表，显示所有值
                                    person_names = []
                                    for val in role_value:
                                        name = extract_person_name(val)
                                        if name:
                                            person_names.append(name)
                                    if person_names:
                                        if len(person_names) > 1:
                                            for i, name in enumerate(person_names, 1):
                                                description_lines.append(f"  {role_display_name}{i}: {name}")
                                        else:
                                            description_lines.append(f"  {role_display_name}: {person_names[0]}")
                                else:
                                    # 直接显示提取的人名
                                    description_lines.append(f"  {role_display_name}: {person_name}")
                        
                        description = "\n".join(description_lines)
                        
                        # 计算时间
                        start_dt = datetime.combine(event_date, monday_config.to_time())
                        end_dt = start_dt + timedelta(minutes=monday_config.duration_minutes)
                        
                        # 创建事件
                        summary = format_weekly_overview_summary(overview_data, sunday_date)
                        event_ics = create_ics_event(
                            uid=f"weekly_monday_{event_date.strftime('%Y%m%d')}@graceirvine.org",
                            summary=summary,
                            description=description,
                            start_dt=start_dt,
                            end_dt=end_dt,
                            reminder_trigger=monday_config.to_ics_trigger()
                        )
                        ics_lines.append(event_ics)
                        events_created += 1
                except Exception as e:
                    logger.error(f"创建周一事件失败: {e}")
        
        ics_lines.append("END:VCALENDAR")
        ics_content = "\n".join(ics_lines)
        
        logger.info(f"✅ 每周概览日历生成完成: {events_created} 个事件")
        return ics_content
        
    except Exception as e:
        logger.error(f"❌ 生成每周概览日历失败: {e}")
        return None


def generate_all_calendars() -> Dict[str, Any]:
    """生成所有类型的 ICS 日历
    
    Returns:
        生成结果字典，包含每个日历的生成状态
    """
    results = {
        'success': True,
        'calendars': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # 生成媒体部日历
    media_ics = generate_media_team_calendar()
    results['calendars']['media-team'] = {
        'success': media_ics is not None,
        'content': media_ics,
        'events': media_ics.count('BEGIN:VEVENT') if media_ics else 0
    }
    
    # 生成儿童部日历
    children_ics = generate_children_team_calendar()
    results['calendars']['children-team'] = {
        'success': children_ics is not None,
        'content': children_ics,
        'events': children_ics.count('BEGIN:VEVENT') if children_ics else 0
    }
    
    # 生成每周概览日历
    overview_ics = generate_weekly_overview_calendar()
    results['calendars']['weekly-overview'] = {
        'success': overview_ics is not None,
        'content': overview_ics,
        'events': overview_ics.count('BEGIN:VEVENT') if overview_ics else 0
    }
    
    # 检查是否有失败的
    if any(not cal['success'] for cal in results['calendars'].values()):
        results['success'] = False
    
    return results


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("🔄 生成所有 ICS 日历...")
    results = generate_all_calendars()
    
    print(f"\n✅ 生成完成!")
    print(f"成功: {results['success']}")
    
    for calendar_type, calendar_result in results['calendars'].items():
        print(f"\n{calendar_type}:")
        print(f"  成功: {calendar_result['success']}")
        print(f"  事件数: {calendar_result['events']}")

