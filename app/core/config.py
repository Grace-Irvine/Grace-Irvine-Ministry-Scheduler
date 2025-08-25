"""
Configuration management for the Grace Irvine Ministry Scheduler

Handles loading settings from YAML files and environment variables.
"""
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings


class GoogleSheetsConfig(BaseSettings):
    """Google Sheets configuration"""
    spreadsheet_id: str = Field(..., env="GOOGLE_SPREADSHEET_ID")
    sheet_name: str = "总表"
    service_account_file: str = "configs/service_account.json"
    columns: Dict[str, Any] = {}


class EmailConfig(BaseSettings):
    """Email configuration"""
    class SendGridConfig(BaseSettings):
        api_key: str = Field(..., env="SENDGRID_API_KEY")
        from_email: str = Field(..., env="SENDGRID_FROM_EMAIL")
        from_name: str = "Grace Irvine Ministry"
    
    class SMTPConfig(BaseSettings):
        host: str = Field("smtp.gmail.com", env="SMTP_HOST")
        port: int = 587
        username: str = Field(..., env="SMTP_USERNAME")
        password: str = Field(..., env="SMTP_PASSWORD")
        use_tls: bool = True
    
    provider: str = "sendgrid"
    sendgrid: SendGridConfig = SendGridConfig()
    smtp: SMTPConfig = SMTPConfig()
    default_subject_prefix: str = "[Grace Irvine Ministry] "
    max_retries: int = 3
    retry_delay: int = 300


class SMSConfig(BaseSettings):
    """SMS configuration"""
    class TwilioConfig(BaseSettings):
        account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
        auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")
        from_number: str = Field(..., env="TWILIO_FROM_NUMBER")
    
    class AWSConfig(BaseSettings):
        access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
        secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
        region: str = "us-west-2"
    
    provider: str = "twilio"
    twilio: TwilioConfig = TwilioConfig()
    aws_sns: AWSConfig = AWSConfig()
    max_retries: int = 3
    retry_delay: int = 300


class CalendarConfig(BaseSettings):
    """Calendar configuration"""
    enabled: bool = True
    filename: str = "ministry_schedule.ics"
    output_directory: str = "data/calendars"
    base_url: Optional[str] = Field(None, env="CALENDAR_BASE_URL")
    default_alarms: List[int] = [30, 1440]  # 30 minutes, 1 day
    calendar_name: str = "Grace Irvine Ministry Schedule"
    calendar_description: str = "Ministry service schedule for Grace Irvine Presbyterian Church"
    timezone: str = "America/Los_Angeles"


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    url: str = "sqlite:///./data/database.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20


class AppConfig(BaseSettings):
    """Application configuration"""
    name: str = "Grace Irvine Ministry Scheduler"
    version: str = "1.0.0"
    debug: bool = Field(False, env="DEBUG")
    host: str = "0.0.0.0"
    port: int = 8000


class SecurityConfig(BaseSettings):
    """Security configuration"""
    api_key: Optional[str] = Field(None, env="API_KEY")
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["*"]


class FeaturesConfig(BaseSettings):
    """Feature flags"""
    enable_web_ui: bool = Field(True, env="ENABLE_WEB_UI")
    enable_api: bool = Field(True, env="ENABLE_API")
    enable_webhooks: bool = Field(False, env="ENABLE_WEBHOOKS")
    enable_analytics: bool = Field(False, env="ENABLE_ANALYTICS")


class NotificationScheduleConfig(BaseSettings):
    """Notification scheduling configuration"""
    class WeeklyConfirmationConfig(BaseSettings):
        enabled: bool = True
        day_of_week: int = 2  # Wednesday
        hour: int = 20
        minute: int = 0
        timezone: str = "America/Los_Angeles"
    
    class SundayReminderConfig(BaseSettings):
        enabled: bool = True
        day_of_week: int = 5  # Saturday
        hour: int = 20
        minute: int = 0
        timezone: str = "America/Los_Angeles"
    
    class MonthlyOverviewConfig(BaseSettings):
        enabled: bool = True
        day_of_month: int = 1
        hour: int = 9
        minute: int = 0
        timezone: str = "America/Los_Angeles"
    
    weekly_confirmation: WeeklyConfirmationConfig = WeeklyConfirmationConfig()
    sunday_reminder: SundayReminderConfig = SundayReminderConfig()
    monthly_overview: MonthlyOverviewConfig = MonthlyOverviewConfig()


class Settings(PydanticBaseSettings):
    """Main settings class"""
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    google_sheets: GoogleSheetsConfig = GoogleSheetsConfig()
    email: EmailConfig = EmailConfig()
    sms: SMSConfig = SMSConfig()
    calendar: CalendarConfig = CalendarConfig()
    security: SecurityConfig = SecurityConfig()
    features: FeaturesConfig = FeaturesConfig()
    notification_schedule: NotificationScheduleConfig = NotificationScheduleConfig()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml_config()
    
    def _load_yaml_config(self):
        """Load additional configuration from YAML file"""
        config_path = Path("configs/settings.yaml")
        
        if not config_path.exists():
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
            
            if not yaml_config:
                return
            
            # Update Google Sheets columns configuration
            if 'google_sheets' in yaml_config and 'columns' in yaml_config['google_sheets']:
                self.google_sheets.columns = yaml_config['google_sheets']['columns']
            
            # Update notification schedule
            if 'notification_schedule' in yaml_config:
                schedule_config = yaml_config['notification_schedule']
                
                if 'weekly_confirmation' in schedule_config:
                    for key, value in schedule_config['weekly_confirmation'].items():
                        setattr(self.notification_schedule.weekly_confirmation, key, value)
                
                if 'sunday_reminder' in schedule_config:
                    for key, value in schedule_config['sunday_reminder'].items():
                        setattr(self.notification_schedule.sunday_reminder, key, value)
                
                if 'monthly_overview' in schedule_config:
                    for key, value in schedule_config['monthly_overview'].items():
                        setattr(self.notification_schedule.monthly_overview, key, value)
            
            # Update calendar configuration
            if 'calendar' in yaml_config:
                for key, value in yaml_config['calendar'].items():
                    if hasattr(self.calendar, key):
                        setattr(self.calendar, key, value)
            
            # Update email configuration
            if 'email' in yaml_config:
                email_config = yaml_config['email']
                
                if 'sendgrid' in email_config:
                    for key, value in email_config['sendgrid'].items():
                        if hasattr(self.email.sendgrid, key):
                            setattr(self.email.sendgrid, key, value)
                
                if 'smtp' in email_config:
                    for key, value in email_config['smtp'].items():
                        if hasattr(self.email.smtp, key):
                            setattr(self.email.smtp, key, value)
                
                # Update top-level email settings
                for key, value in email_config.items():
                    if key not in ['sendgrid', 'smtp'] and hasattr(self.email, key):
                        setattr(self.email, key, value)
            
            # Update SMS configuration
            if 'sms' in yaml_config:
                sms_config = yaml_config['sms']
                
                if 'twilio' in sms_config:
                    for key, value in sms_config['twilio'].items():
                        if hasattr(self.sms.twilio, key):
                            setattr(self.sms.twilio, key, value)
                
                if 'aws_sns' in sms_config:
                    for key, value in sms_config['aws_sns'].items():
                        if hasattr(self.sms.aws_sns, key):
                            setattr(self.sms.aws_sns, key, value)
                
                # Update top-level SMS settings
                for key, value in sms_config.items():
                    if key not in ['twilio', 'aws_sns'] and hasattr(self.sms, key):
                        setattr(self.sms, key, value)
            
        except Exception as e:
            # Don't fail startup if YAML config has issues
            print(f"Warning: Could not load YAML config: {e}")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def load_template_config() -> Dict[str, Any]:
    """Load notification template configuration"""
    config_path = Path("configs/notification_templates.yaml")
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load template config: {e}")
        return {}


def get_recipients_config() -> List[Dict[str, Any]]:
    """Get recipients configuration from settings"""
    settings = get_settings()
    
    # Load from YAML if available
    config_path = Path("configs/settings.yaml")
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
            
            if yaml_config and 'recipients' in yaml_config:
                recipients = []
                
                # Add primary recipients
                if 'primary' in yaml_config['recipients']:
                    for recipient in yaml_config['recipients']['primary']:
                        recipient['is_primary'] = True
                        recipients.append(recipient)
                
                # Add backup recipients
                if 'backup' in yaml_config['recipients']:
                    for recipient in yaml_config['recipients']['backup']:
                        recipient['is_primary'] = False
                        recipients.append(recipient)
                
                return recipients
        except Exception as e:
            print(f"Warning: Could not load recipients config: {e}")
    
    # Fallback to environment variables
    recipients = []
    
    # Try to load primary recipients from env vars
    primary_email_1 = os.getenv("PRIMARY_EMAIL_1")
    primary_phone_1 = os.getenv("PRIMARY_PHONE_1")
    
    if primary_email_1:
        recipients.append({
            "name": "Ministry Coordinator",
            "email": primary_email_1,
            "phone": primary_phone_1,
            "is_primary": True,
            "notifications": ["weekly_confirmation", "sunday_reminder", "monthly_overview"]
        })
    
    primary_email_2 = os.getenv("PRIMARY_EMAIL_2")
    primary_phone_2 = os.getenv("PRIMARY_PHONE_2")
    
    if primary_email_2:
        recipients.append({
            "name": "Worship Leader",
            "email": primary_email_2,
            "phone": primary_phone_2,
            "is_primary": True,
            "notifications": ["weekly_confirmation", "sunday_reminder"]
        })
    
    backup_email_1 = os.getenv("BACKUP_EMAIL_1")
    if backup_email_1:
        recipients.append({
            "name": "Pastor",
            "email": backup_email_1,
            "phone": None,
            "is_primary": False,
            "notifications": ["monthly_overview"]
        })
    
    return recipients
