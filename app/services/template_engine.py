"""
Notification Template Engine

Handles rendering of notification templates for different channels (email, SMS)
and notification types (weekly confirmation, Sunday reminder, monthly overview).
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from dataclasses import asdict

from app.models.schedule import (
    NotificationData, 
    ScheduleData, 
    NotificationType,
    NotificationTemplateResponse
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Template engine for generating notification content
    
    Features:
    - Jinja2-based template rendering
    - Support for email (HTML/text) and SMS templates
    - Built-in template variables and filters
    - Localization support (Chinese/English)
    - Template validation and testing
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.template_config = self._load_template_config()
        self.jinja_env = self._setup_jinja_environment()
    
    def _load_template_config(self) -> Dict[str, Any]:
        """Load template configuration from YAML file"""
        try:
            config_path = Path("configs/notification_templates.yaml")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("Loaded notification template configuration")
            return config
        except Exception as e:
            logger.error(f"Failed to load template config: {e}")
            return {}
    
    def _setup_jinja_environment(self) -> Environment:
        """Setup Jinja2 environment with custom filters and globals"""
        # Setup template loader
        template_dir = Path("templates")
        loader = FileSystemLoader(template_dir, encoding='utf-8')
        
        # Create environment
        env = Environment(
            loader=loader,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        env.filters.update({
            'chinese_date': self._filter_chinese_date,
            'chinese_time': self._filter_chinese_time,
            'chinese_weekday': self._filter_chinese_weekday,
            'format_roles': self._filter_format_roles,
            'group_by_date': self._filter_group_by_date,
            'summarize_volunteers': self._filter_summarize_volunteers,
            'truncate_sms': self._filter_truncate_sms,
        })
        
        # Add global variables
        env.globals.update({
            'church_name': '恩典尔湾长老教会',
            'church_name_en': 'Grace Irvine Presbyterian Church',
            'now': datetime.now,
            'today': date.today,
        })
        
        return env
    
    def _filter_chinese_date(self, date_obj: date) -> str:
        """Convert date to Chinese format: 2024年1月14日"""
        return f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
    
    def _filter_chinese_time(self, time_obj) -> str:
        """Convert time to Chinese format: 上午10:00 / 下午8:00"""
        if hasattr(time_obj, 'hour'):
            hour = time_obj.hour
            minute = time_obj.minute
        else:
            # Handle string time
            hour, minute = map(int, str(time_obj).split(':'))
        
        if hour < 12:
            period = "上午"
            display_hour = hour if hour > 0 else 12
        else:
            period = "下午"
            display_hour = hour if hour <= 12 else hour - 12
        
        return f"{period}{display_hour}:{minute:02d}"
    
    def _filter_chinese_weekday(self, date_obj: date) -> str:
        """Convert date to Chinese weekday"""
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        return weekdays[date_obj.weekday()]
    
    def _filter_format_roles(self, roles: Dict[str, str], format_type: str = 'list') -> str:
        """Format role assignments"""
        if not roles:
            return ""
        
        if format_type == 'list':
            # Format as "服事: 张三, 敬拜: 李四"
            formatted = []
            for service_type, person in roles.items():
                formatted.append(f"{service_type}: {person}")
            return ", ".join(formatted)
        
        elif format_type == 'table':
            # Format as table rows for HTML
            rows = []
            for service_type, person in roles.items():
                rows.append(f"<tr><td>{service_type}</td><td>{person}</td></tr>")
            return "".join(rows)
        
        elif format_type == 'sms':
            # Compact format for SMS with abbreviations
            abbreviations = self.template_config.get('sms_settings', {}).get('abbreviations', {})
            formatted = []
            for service_type, person in roles.items():
                abbrev = abbreviations.get(service_type, service_type)
                formatted.append(f"{person}({abbrev})")
            return ", ".join(formatted)
        
        return str(roles)
    
    def _filter_group_by_date(self, schedules: List[ScheduleData]) -> Dict[date, List[ScheduleData]]:
        """Group schedules by date"""
        grouped = {}
        for schedule in schedules:
            if schedule.date not in grouped:
                grouped[schedule.date] = []
            grouped[schedule.date].append(schedule)
        return grouped
    
    def _filter_summarize_volunteers(self, schedules: List[ScheduleData]) -> Dict[str, int]:
        """Summarize volunteer assignments"""
        volunteer_counts = {}
        for schedule in schedules:
            for person in schedule.roles.values():
                volunteer_counts[person] = volunteer_counts.get(person, 0) + 1
        return dict(sorted(volunteer_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _filter_truncate_sms(self, text: str, max_length: int = 160) -> str:
        """Truncate text for SMS with proper Chinese character handling"""
        if len(text) <= max_length:
            return text
        
        # Truncate and add ellipsis
        truncated = text[:max_length-2] + "..."
        return truncated
    
    def _prepare_template_variables(
        self, 
        notification_data: NotificationData,
        notification_type: NotificationType
    ) -> Dict[str, Any]:
        """Prepare variables for template rendering"""
        
        # Base variables
        variables = {
            'notification_type': notification_type,
            'date_range': notification_data.date_range,
            'schedules': notification_data.schedules,
            'total_services': len(notification_data.schedules),
            'generated_at': datetime.now(),
            'church_name': '恩典尔湾长老教会',
        }
        
        # Add notification-specific variables
        if notification_type == NotificationType.WEEKLY_CONFIRMATION:
            variables.update(self._prepare_weekly_variables(notification_data))
        elif notification_type == NotificationType.SUNDAY_REMINDER:
            variables.update(self._prepare_sunday_variables(notification_data))
        elif notification_type == NotificationType.MONTHLY_OVERVIEW:
            variables.update(self._prepare_monthly_variables(notification_data))
        
        # Add any custom variables from notification_data
        variables.update(notification_data.template_variables)
        
        return variables
    
    def _prepare_weekly_variables(self, notification_data: NotificationData) -> Dict[str, Any]:
        """Prepare variables specific to weekly confirmation notifications"""
        schedules = notification_data.schedules
        
        # Calculate week dates
        if schedules:
            first_date = min(s.date for s in schedules)
            last_date = max(s.date for s in schedules)
            week_range = f"{first_date.month}月{first_date.day}日-{last_date.month}月{last_date.day}日"
        else:
            week_range = "本周"
        
        # Count assignments
        total_assignments = sum(len(s.roles) for s in schedules)
        
        # Get unique volunteers
        all_volunteers = set()
        for schedule in schedules:
            all_volunteers.update(schedule.roles.values())
        
        return {
            'week_range': week_range,
            'week_schedules': schedules,
            'total_assignments': total_assignments,
            'unique_volunteers': len(all_volunteers),
            'volunteer_list': sorted(list(all_volunteers)),
        }
    
    def _prepare_sunday_variables(self, notification_data: NotificationData) -> Dict[str, Any]:
        """Prepare variables specific to Sunday reminder notifications"""
        schedules = notification_data.schedules
        
        # Should be only one Sunday service
        sunday_schedule = schedules[0] if schedules else None
        
        if sunday_schedule:
            service_date = sunday_schedule.date
            service_time = sunday_schedule.time
            
            # Calculate arrival time (30 minutes before service)
            arrival_time = datetime.combine(service_date, service_time) - timedelta(minutes=30)
            
            return {
                'service_date': service_date,
                'service_time': service_time,
                'arrival_time': arrival_time.time(),
                'sunday_schedule': sunday_schedule,
                'location': sunday_schedule.location,
                'assignments_count': len(sunday_schedule.roles),
            }
        else:
            return {
                'service_date': None,
                'service_time': None,
                'arrival_time': None,
                'sunday_schedule': None,
                'location': None,
                'assignments_count': 0,
            }
    
    def _prepare_monthly_variables(self, notification_data: NotificationData) -> Dict[str, Any]:
        """Prepare variables specific to monthly overview notifications"""
        schedules = notification_data.schedules
        
        if not schedules:
            return {
                'month_year': datetime.now().strftime('%Y年%m月'),
                'month_schedules': [],
                'total_services': 0,
                'unique_volunteers': 0,
                'role_summary': [],
                'volunteer_summary': [],
            }
        
        # Calculate month/year
        first_date = min(s.date for s in schedules)
        month_year = f"{first_date.year}年{first_date.month}月"
        
        # Count unique volunteers
        all_volunteers = set()
        role_counts = {}
        volunteer_assignments = {}
        
        for schedule in schedules:
            all_volunteers.update(schedule.roles.values())
            
            for service_type, person in schedule.roles.items():
                # Count by role
                role_counts[service_type] = role_counts.get(service_type, 0) + 1
                
                # Count by volunteer
                volunteer_assignments[person] = volunteer_assignments.get(person, 0) + 1
        
        # Create summaries
        role_summary = [
            {'role': role, 'assignments': count, 'volunteers': len(set())}
            for role, count in sorted(role_counts.items())
        ]
        
        volunteer_summary = [
            {'volunteer': person, 'assignments': count}
            for person, count in sorted(volunteer_assignments.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return {
            'month_year': month_year,
            'month_schedules': schedules,
            'total_services': len(schedules),
            'unique_volunteers': len(all_volunteers),
            'role_summary': role_summary,
            'volunteer_summary': volunteer_summary,
        }
    
    def render_email_subject(
        self,
        notification_type: NotificationType,
        template_variables: Dict[str, Any]
    ) -> str:
        """Render email subject line"""
        try:
            template_config = self.template_config.get(notification_type.value, {})
            subject_template = template_config.get('email', {}).get('subject', '')
            
            if not subject_template:
                # Fallback subject
                return f"[恩典尔湾] {notification_type.value} - {template_variables.get('date_range', '')}"
            
            template = Template(subject_template)
            return template.render(**template_variables)
            
        except Exception as e:
            logger.error(f"Error rendering email subject for {notification_type}: {e}")
            return f"[恩典尔湾] 事工通知"
    
    def render_email_html(
        self,
        notification_type: NotificationType,
        template_variables: Dict[str, Any]
    ) -> str:
        """Render HTML email content"""
        try:
            template_config = self.template_config.get(notification_type.value, {})
            template_file = template_config.get('email', {}).get('html_template', '')
            
            if not template_file:
                # Use fallback template
                template_file = 'email/default.html'
            
            template = self.jinja_env.get_template(template_file)
            return template.render(**template_variables)
            
        except Exception as e:
            logger.error(f"Error rendering HTML email for {notification_type}: {e}")
            # Return simple fallback
            return self._render_fallback_email(template_variables)
    
    def render_email_text(
        self,
        notification_type: NotificationType,
        template_variables: Dict[str, Any]
    ) -> str:
        """Render plain text email content"""
        try:
            template_config = self.template_config.get(notification_type.value, {})
            template_file = template_config.get('email', {}).get('text_template', '')
            
            if not template_file:
                # Use fallback template
                template_file = 'email/default.txt'
            
            template = self.jinja_env.get_template(template_file)
            return template.render(**template_variables)
            
        except Exception as e:
            logger.error(f"Error rendering text email for {notification_type}: {e}")
            # Return simple fallback
            return self._render_fallback_text(template_variables)
    
    def render_sms(
        self,
        notification_type: NotificationType,
        template_variables: Dict[str, Any]
    ) -> str:
        """Render SMS content"""
        try:
            template_config = self.template_config.get(notification_type.value, {})
            template_file = template_config.get('sms', {}).get('template', '')
            
            if not template_file:
                # Use fallback template
                template_file = 'sms/default.txt'
            
            template = self.jinja_env.get_template(template_file)
            content = template.render(**template_variables)
            
            # Apply SMS length limits
            max_length = template_config.get('sms', {}).get('max_length', 160)
            return self._filter_truncate_sms(content, max_length)
            
        except Exception as e:
            logger.error(f"Error rendering SMS for {notification_type}: {e}")
            # Return simple fallback
            return self._render_fallback_sms(template_variables)
    
    def _render_fallback_email(self, variables: Dict[str, Any]) -> str:
        """Fallback HTML email template"""
        schedules = variables.get('schedules', [])
        schedule_list = ""
        
        for schedule in schedules:
            roles_text = ", ".join([f"{role}: {person}" for role, person in schedule.roles.items()])
            schedule_list += f"<li>{schedule.date} {schedule.time} - {roles_text}</li>"
        
        return f"""
        <html>
        <body>
            <h2>恩典尔湾长老教会 - 事工通知</h2>
            <p>亲爱的同工们，</p>
            <p>以下是事工安排：</p>
            <ul>{schedule_list}</ul>
            <p>神祝福！</p>
        </body>
        </html>
        """
    
    def _render_fallback_text(self, variables: Dict[str, Any]) -> str:
        """Fallback plain text email template"""
        schedules = variables.get('schedules', [])
        schedule_text = ""
        
        for schedule in schedules:
            roles_text = ", ".join([f"{role}: {person}" for role, person in schedule.roles.items()])
            schedule_text += f"• {schedule.date} {schedule.time} - {roles_text}\n"
        
        return f"""
恩典尔湾长老教会 - 事工通知

亲爱的同工们，

以下是事工安排：
{schedule_text}

神祝福！
        """.strip()
    
    def _render_fallback_sms(self, variables: Dict[str, Any]) -> str:
        """Fallback SMS template"""
        schedules = variables.get('schedules', [])
        if schedules:
            first_schedule = schedules[0]
            roles_text = ", ".join([f"{person}({role})" for role, person in list(first_schedule.roles.items())[:3]])
            return f"恩典尔湾事工提醒：{first_schedule.date} {roles_text}等。详见邮件。"
        else:
            return "恩典尔湾事工通知，请查看邮件了解详情。"
    
    def render_notification(
        self,
        notification_data: NotificationData
    ) -> Dict[str, str]:
        """
        Render complete notification content for all channels
        
        Args:
            notification_data: Notification data object
            
        Returns:
            Dictionary with rendered content:
            {
                'email_subject': str,
                'email_html': str,
                'email_text': str,
                'sms': str
            }
        """
        try:
            # Prepare template variables
            variables = self._prepare_template_variables(
                notification_data,
                notification_data.notification_type
            )
            
            # Render all content types
            rendered = {
                'email_subject': self.render_email_subject(
                    notification_data.notification_type, 
                    variables
                ),
                'email_html': self.render_email_html(
                    notification_data.notification_type, 
                    variables
                ),
                'email_text': self.render_email_text(
                    notification_data.notification_type, 
                    variables
                ),
                'sms': self.render_sms(
                    notification_data.notification_type, 
                    variables
                )
            }
            
            logger.info(f"Successfully rendered {notification_data.notification_type} notification")
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering notification: {e}")
            raise
    
    def validate_template(self, template_file: str) -> Tuple[bool, str]:
        """
        Validate a template file
        
        Args:
            template_file: Path to template file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            template = self.jinja_env.get_template(template_file)
            
            # Try rendering with sample data
            sample_data = {
                'church_name': '恩典尔湾长老教会',
                'date_range': '测试日期',
                'schedules': [],
                'total_services': 0,
            }
            
            template.render(**sample_data)
            return True, "Template is valid"
            
        except Exception as e:
            return False, str(e)
    
    def list_available_templates(self) -> Dict[str, List[str]]:
        """List all available templates by type"""
        template_dir = Path("templates")
        templates = {
            'email': [],
            'sms': []
        }
        
        for template_type in templates.keys():
            type_dir = template_dir / template_type
            if type_dir.exists():
                templates[template_type] = [
                    f.name for f in type_dir.glob("*.html") 
                    if f.is_file()
                ] + [
                    f.name for f in type_dir.glob("*.txt") 
                    if f.is_file()
                ]
        
        return templates
