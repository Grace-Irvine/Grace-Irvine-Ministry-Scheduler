"""
Ministry Schedule Data Models
"""
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator
import uuid

Base = declarative_base()


class ServiceType(str, Enum):
    """Ministry service types"""
    CHAIRMAN = "主席"
    SPEAKER = "讲员"
    WORSHIP_LEADER = "领会"
    WORSHIP = "敬拜"
    PIANIST = "司琴"
    SOUND = "音控"
    PROJECTION = "投影"
    USHER = "招待"
    SUNDAY_SCHOOL = "儿童主日学"
    CLEANING = "清洁"


class NotificationType(str, Enum):
    """Notification types"""
    WEEKLY_CONFIRMATION = "weekly_confirmation"
    SUNDAY_REMINDER = "sunday_reminder"
    MONTHLY_OVERVIEW = "monthly_overview"


class NotificationStatus(str, Enum):
    """Notification status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


# SQLAlchemy Models
class MinistrySchedule(Base):
    """Ministry schedule database model"""
    __tablename__ = "ministry_schedules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=False)
    location = Column(String(200), nullable=False)
    service_type = Column(String(50), nullable=False)
    person_name = Column(String(100), nullable=False)
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_sheet_row = Column(Integer)  # Original row in Google Sheets
    
    def __repr__(self):
        return f"<MinistrySchedule(date={self.date}, service_type={self.service_type}, person={self.person_name})>"


class NotificationTemplate(Base):
    """Notification template database model"""
    __tablename__ = "notification_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    notification_type = Column(String(50), nullable=False)
    
    # Email templates
    email_subject_template = Column(Text)
    email_html_template = Column(Text)
    email_text_template = Column(Text)
    
    # SMS template
    sms_template = Column(Text)
    
    # Configuration
    data_scope_config = Column(JSON)  # How to query data for this template
    recipient_config = Column(JSON)   # Who receives this notification
    
    # Scheduling
    is_active = Column(Boolean, default=True)
    schedule_config = Column(JSON)    # When to send (cron-like)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationLog(Base):
    """Notification sending log"""
    __tablename__ = "notification_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(100), nullable=False)
    notification_type = Column(String(50), nullable=False)
    
    # Recipient info
    recipient_email = Column(String(200))
    recipient_phone = Column(String(20))
    recipient_name = Column(String(100))
    
    # Message content
    subject = Column(Text)
    content = Column(Text)
    channel = Column(String(20))  # email, sms
    
    # Status tracking
    status = Column(String(20), nullable=False, default="pending")
    sent_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Recipient(Base):
    """Notification recipients"""
    __tablename__ = "recipients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(200))
    phone = Column(String(20))
    
    # Configuration
    notification_types = Column(JSON)  # List of notification types they receive
    is_primary = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Preferences
    preferred_channel = Column(String(20), default="email")  # email, sms, both
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models for API
class MinistryScheduleBase(BaseModel):
    """Base schedule model"""
    date: date
    time: time
    location: str
    service_type: ServiceType
    person_name: str
    notes: Optional[str] = None
    
    @validator('person_name')
    def validate_person_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Person name must be at least 2 characters long')
        return v.strip()
    
    @validator('location')
    def validate_location(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Location must be specified')
        return v.strip()


class MinistryScheduleCreate(MinistryScheduleBase):
    """Schedule creation model"""
    source_sheet_row: Optional[int] = None


class MinistryScheduleUpdate(BaseModel):
    """Schedule update model"""
    date: Optional[date] = None
    time: Optional[time] = None
    location: Optional[str] = None
    service_type: Optional[ServiceType] = None
    person_name: Optional[str] = None
    notes: Optional[str] = None


class MinistryScheduleResponse(MinistryScheduleBase):
    """Schedule response model"""
    id: str
    created_at: datetime
    updated_at: datetime
    source_sheet_row: Optional[int] = None
    
    class Config:
        from_attributes = True


class NotificationTemplateBase(BaseModel):
    """Base notification template model"""
    template_id: str
    name: str
    notification_type: NotificationType
    email_subject_template: Optional[str] = None
    email_html_template: Optional[str] = None
    email_text_template: Optional[str] = None
    sms_template: Optional[str] = None
    is_active: bool = True


class NotificationTemplateResponse(NotificationTemplateBase):
    """Notification template response model"""
    id: str
    data_scope_config: Optional[Dict[str, Any]] = None
    recipient_config: Optional[Dict[str, Any]] = None
    schedule_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RecipientBase(BaseModel):
    """Base recipient model"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    notification_types: List[NotificationType] = []
    is_primary: bool = True
    is_active: bool = True
    preferred_channel: str = "email"
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            raise ValueError('Phone number must include country code (e.g., +1)')
        return v


class RecipientResponse(RecipientBase):
    """Recipient response model"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotificationLogResponse(BaseModel):
    """Notification log response model"""
    id: str
    template_id: str
    notification_type: NotificationType
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    recipient_name: Optional[str] = None
    subject: Optional[str] = None
    channel: str
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Dataclasses for internal processing
@dataclass
class ScheduleData:
    """Internal schedule data structure"""
    date: date
    time: time
    location: str
    roles: Dict[str, str]  # service_type -> person_name mapping
    notes: Optional[str] = None
    
    def get_all_assignments(self) -> List[tuple]:
        """Get all assignments as (service_type, person_name) tuples"""
        return [(service_type, person) for service_type, person in self.roles.items() if person]


@dataclass
class NotificationData:
    """Data structure for notification generation"""
    template_id: str
    notification_type: NotificationType
    date_range: str
    schedules: List[ScheduleData]
    recipients: List[Dict[str, str]]
    template_variables: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Calculate summary statistics
        self.template_variables.update({
            'total_services': len(self.schedules),
            'total_assignments': sum(len(s.roles) for s in self.schedules),
            'unique_volunteers': len(set(
                person for schedule in self.schedules 
                for person in schedule.roles.values() 
                if person
            )),
            'date_range': self.date_range,
            'generated_at': datetime.now(),
        })


@dataclass
class CalendarEvent:
    """Calendar event data structure"""
    uid: str
    summary: str
    description: str
    start_datetime: datetime
    end_datetime: datetime
    location: str
    organizer_email: str
    alarm_minutes: List[int] = field(default_factory=lambda: [30, 1440])
    
    def __post_init__(self):
        if not self.uid:
            self.uid = str(uuid.uuid4())


# Query helper models
class DateRange(BaseModel):
    """Date range for queries"""
    start_date: date
    end_date: date
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v < start_date:
            raise ValueError('End date must be after start date')
        return v


class ScheduleQuery(BaseModel):
    """Schedule query parameters"""
    date_range: Optional[DateRange] = None
    service_types: Optional[List[ServiceType]] = None
    person_name: Optional[str] = None
    location: Optional[str] = None
    limit: Optional[int] = Field(None, ge=1, le=1000)
    offset: Optional[int] = Field(0, ge=0)


class NotificationQuery(BaseModel):
    """Notification query parameters"""
    notification_type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    date_range: Optional[DateRange] = None
    recipient_email: Optional[str] = None
    limit: Optional[int] = Field(None, ge=1, le=1000)
    offset: Optional[int] = Field(0, ge=0)
