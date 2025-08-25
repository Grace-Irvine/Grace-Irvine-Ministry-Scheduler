"""
Calendar Service for generating .ics files and subscription URLs

Generates iCalendar-compliant .ics files with ministry schedules and reminders.
Supports calendar subscriptions with automatic updates.
"""
import logging
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid
import pytz
from icalendar import Calendar, Event, Alarm
from urllib.parse import urljoin

from app.models.schedule import ScheduleData, CalendarEvent
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Service for generating and managing ministry schedule calendars
    
    Features:
    - Generate .ics files from schedule data
    - Support for multiple alarm/reminder types
    - Calendar subscription URLs
    - Timezone handling
    - Event metadata and descriptions
    - Calendar versioning and updates
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.timezone = pytz.timezone(self.settings.calendar.timezone)
        self.output_dir = Path(self.settings.calendar.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_calendar_event(
        self,
        schedule: ScheduleData,
        person_name: str,
        service_type: str
    ) -> CalendarEvent:
        """
        Create a calendar event from schedule data
        
        Args:
            schedule: Schedule data
            person_name: Person assigned to the service
            service_type: Type of ministry service
            
        Returns:
            CalendarEvent object
        """
        # Create datetime objects
        start_datetime = datetime.combine(schedule.date, schedule.time)
        start_datetime = self.timezone.localize(start_datetime)
        
        # Default service duration (2 hours)
        end_datetime = start_datetime + timedelta(hours=2)
        
        # Create unique event ID
        event_uid = f"ministry-{schedule.date.isoformat()}-{service_type}-{person_name}@graceirvine.org"
        
        # Create event summary (title)
        summary = f"事工服事: {service_type}"
        
        # Create detailed description
        description_parts = [
            f"服事类型: {service_type}",
            f"服事人员: {person_name}",
            f"聚会时间: {schedule.time.strftime('%H:%M')}",
            f"聚会地点: {schedule.location}",
        ]
        
        if schedule.notes:
            description_parts.append(f"备注: {schedule.notes}")
        
        # Add other roles for context
        other_roles = [
            f"{role}: {person}" 
            for role, person in schedule.roles.items() 
            if role != service_type
        ]
        if other_roles:
            description_parts.append("")
            description_parts.append("其他服事安排:")
            description_parts.extend(other_roles)
        
        description = "\\n".join(description_parts)
        
        # Create calendar event
        calendar_event = CalendarEvent(
            uid=event_uid,
            summary=summary,
            description=description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location=schedule.location,
            organizer_email=self.settings.email.sendgrid.from_email,
            alarm_minutes=self.settings.calendar.default_alarms
        )
        
        return calendar_event
    
    def _create_icalendar_event(self, calendar_event: CalendarEvent) -> Event:
        """
        Create an iCalendar Event object from CalendarEvent
        
        Args:
            calendar_event: CalendarEvent data
            
        Returns:
            icalendar.Event object
        """
        event = Event()
        
        # Basic event properties
        event.add('uid', calendar_event.uid)
        event.add('summary', calendar_event.summary)
        event.add('description', calendar_event.description)
        event.add('dtstart', calendar_event.start_datetime)
        event.add('dtend', calendar_event.end_datetime)
        event.add('location', calendar_event.location)
        event.add('organizer', f"mailto:{calendar_event.organizer_email}")
        
        # Add timestamp
        event.add('dtstamp', datetime.now(self.timezone))
        event.add('created', datetime.now(self.timezone))
        event.add('last-modified', datetime.now(self.timezone))
        
        # Add sequence number for updates
        event.add('sequence', 0)
        
        # Add status
        event.add('status', 'CONFIRMED')
        
        # Add class
        event.add('class', 'PUBLIC')
        
        # Add categories
        event.add('categories', ['Ministry', 'Church Service', 'Grace Irvine'])
        
        # Add alarms (reminders)
        for alarm_minutes in calendar_event.alarm_minutes:
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f'事工提醒: {calendar_event.summary}')
            alarm.add('trigger', timedelta(minutes=-alarm_minutes))
            event.add_component(alarm)
        
        return event
    
    def generate_calendar_events(self, schedules: List[ScheduleData]) -> List[CalendarEvent]:
        """
        Generate calendar events from schedule data
        
        Args:
            schedules: List of schedule data
            
        Returns:
            List of CalendarEvent objects
        """
        events = []
        
        for schedule in schedules:
            # Create an event for each person/role assignment
            for service_type, person_name in schedule.roles.items():
                if person_name:  # Skip empty assignments
                    event = self._create_calendar_event(schedule, person_name, service_type)
                    events.append(event)
        
        logger.info(f"Generated {len(events)} calendar events from {len(schedules)} schedules")
        return events
    
    def create_icalendar(
        self,
        events: List[CalendarEvent],
        calendar_name: Optional[str] = None,
        calendar_description: Optional[str] = None
    ) -> Calendar:
        """
        Create an iCalendar object from calendar events
        
        Args:
            events: List of CalendarEvent objects
            calendar_name: Calendar name (optional)
            calendar_description: Calendar description (optional)
            
        Returns:
            icalendar.Calendar object
        """
        # Create calendar
        cal = Calendar()
        
        # Calendar properties
        cal.add('prodid', '-//Grace Irvine Presbyterian Church//Ministry Scheduler//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        
        # Calendar metadata
        cal.add('x-wr-calname', calendar_name or self.settings.calendar.calendar_name)
        cal.add('x-wr-caldesc', calendar_description or self.settings.calendar.calendar_description)
        cal.add('x-wr-timezone', self.settings.calendar.timezone)
        
        # Add refresh interval (1 hour)
        cal.add('x-published-ttl', 'PT1H')
        
        # Add events
        for calendar_event in events:
            ical_event = self._create_icalendar_event(calendar_event)
            cal.add_component(ical_event)
        
        logger.info(f"Created iCalendar with {len(events)} events")
        return cal
    
    def save_calendar_file(
        self,
        calendar: Calendar,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save calendar to .ics file
        
        Args:
            calendar: iCalendar object
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = self.settings.calendar.filename
        
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'wb') as f:
                f.write(calendar.to_ical())
            
            logger.info(f"Saved calendar to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save calendar file: {e}")
            raise
    
    def generate_calendar_from_schedules(
        self,
        schedules: List[ScheduleData],
        filename: Optional[str] = None,
        calendar_name: Optional[str] = None
    ) -> Path:
        """
        Generate complete calendar file from schedule data
        
        Args:
            schedules: List of schedule data
            filename: Output filename (optional)
            calendar_name: Calendar name (optional)
            
        Returns:
            Path to generated calendar file
        """
        # Generate events
        events = self.generate_calendar_events(schedules)
        
        # Create calendar
        calendar = self.create_icalendar(events, calendar_name)
        
        # Save to file
        return self.save_calendar_file(calendar, filename)
    
    def get_subscription_url(self, filename: Optional[str] = None) -> str:
        """
        Get calendar subscription URL
        
        Args:
            filename: Calendar filename (optional)
            
        Returns:
            Subscription URL (webcal://)
        """
        if not filename:
            filename = self.settings.calendar.filename
        
        base_url = self.settings.calendar.base_url
        if not base_url:
            logger.warning("Calendar base URL not configured")
            return ""
        
        # Create subscription URL
        http_url = urljoin(base_url, f"calendars/{filename}")
        webcal_url = http_url.replace('http://', 'webcal://').replace('https://', 'webcal://')
        
        return webcal_url
    
    def get_download_url(self, filename: Optional[str] = None) -> str:
        """
        Get calendar download URL
        
        Args:
            filename: Calendar filename (optional)
            
        Returns:
            Download URL (https://)
        """
        if not filename:
            filename = self.settings.calendar.filename
        
        base_url = self.settings.calendar.base_url
        if not base_url:
            logger.warning("Calendar base URL not configured")
            return ""
        
        return urljoin(base_url, f"calendars/{filename}")
    
    def create_personal_calendar(
        self,
        schedules: List[ScheduleData],
        person_name: str
    ) -> Tuple[Path, str, str]:
        """
        Create a personalized calendar for a specific volunteer
        
        Args:
            schedules: All schedule data
            person_name: Name of the person
            
        Returns:
            Tuple of (file_path, subscription_url, download_url)
        """
        # Filter schedules for this person
        personal_schedules = []
        for schedule in schedules:
            # Check if person is assigned to any role in this schedule
            personal_roles = {
                role: person for role, person in schedule.roles.items()
                if person == person_name
            }
            
            if personal_roles:
                # Create a new schedule with only this person's roles
                personal_schedule = ScheduleData(
                    date=schedule.date,
                    time=schedule.time,
                    location=schedule.location,
                    roles=personal_roles,
                    notes=schedule.notes
                )
                personal_schedules.append(personal_schedule)
        
        if not personal_schedules:
            logger.warning(f"No schedules found for {person_name}")
            return None, "", ""
        
        # Generate filename
        safe_name = "".join(c for c in person_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"ministry_schedule_{safe_name.replace(' ', '_')}.ics"
        
        # Generate calendar
        calendar_name = f"恩典尔湾长老教会 - {person_name} 事工安排"
        file_path = self.generate_calendar_from_schedules(
            personal_schedules,
            filename,
            calendar_name
        )
        
        # Generate URLs
        subscription_url = self.get_subscription_url(filename)
        download_url = self.get_download_url(filename)
        
        logger.info(f"Created personal calendar for {person_name}: {file_path}")
        return file_path, subscription_url, download_url
    
    def create_role_based_calendar(
        self,
        schedules: List[ScheduleData],
        service_types: List[str]
    ) -> Tuple[Path, str, str]:
        """
        Create a calendar filtered by service types
        
        Args:
            schedules: All schedule data
            service_types: List of service types to include
            
        Returns:
            Tuple of (file_path, subscription_url, download_url)
        """
        # Filter schedules for specified service types
        filtered_schedules = []
        for schedule in schedules:
            # Filter roles to only include specified service types
            filtered_roles = {
                role: person for role, person in schedule.roles.items()
                if role in service_types and person
            }
            
            if filtered_roles:
                filtered_schedule = ScheduleData(
                    date=schedule.date,
                    time=schedule.time,
                    location=schedule.location,
                    roles=filtered_roles,
                    notes=schedule.notes
                )
                filtered_schedules.append(filtered_schedule)
        
        if not filtered_schedules:
            logger.warning(f"No schedules found for service types: {service_types}")
            return None, "", ""
        
        # Generate filename
        service_types_str = "_".join(service_types)
        filename = f"ministry_schedule_{service_types_str}.ics"
        
        # Generate calendar
        calendar_name = f"恩典尔湾长老教会 - {', '.join(service_types)} 事工安排"
        file_path = self.generate_calendar_from_schedules(
            filtered_schedules,
            filename,
            calendar_name
        )
        
        # Generate URLs
        subscription_url = self.get_subscription_url(filename)
        download_url = self.get_download_url(filename)
        
        logger.info(f"Created role-based calendar for {service_types}: {file_path}")
        return file_path, subscription_url, download_url
    
    def validate_calendar_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate a generated calendar file
        
        Args:
            file_path: Path to calendar file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'rb') as f:
                calendar_data = f.read()
            
            # Try to parse the calendar
            Calendar.from_ical(calendar_data)
            
            return True, "Calendar file is valid"
            
        except Exception as e:
            return False, f"Invalid calendar file: {e}"
    
    def get_calendar_statistics(self, schedules: List[ScheduleData]) -> Dict[str, Any]:
        """
        Get statistics about the calendar data
        
        Args:
            schedules: List of schedule data
            
        Returns:
            Dictionary with statistics
        """
        if not schedules:
            return {
                "total_events": 0,
                "date_range": None,
                "unique_volunteers": 0,
                "service_types": [],
                "locations": []
            }
        
        events = self.generate_calendar_events(schedules)
        
        # Calculate statistics
        dates = [s.date for s in schedules]
        all_volunteers = set()
        all_service_types = set()
        all_locations = set()
        
        for schedule in schedules:
            all_volunteers.update(schedule.roles.values())
            all_service_types.update(schedule.roles.keys())
            all_locations.add(schedule.location)
        
        return {
            "total_events": len(events),
            "total_schedules": len(schedules),
            "date_range": f"{min(dates)} to {max(dates)}",
            "unique_volunteers": len(all_volunteers),
            "service_types": sorted(list(all_service_types)),
            "locations": sorted(list(all_locations)),
            "volunteers": sorted(list(all_volunteers))
        }
    
    def cleanup_old_calendars(self, days_old: int = 30) -> int:
        """
        Clean up old calendar files
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            Number of files removed
        """
        cutoff_time = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        
        try:
            for file_path in self.output_dir.glob("*.ics"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"Removed old calendar file: {file_path}")
            
            logger.info(f"Cleaned up {removed_count} old calendar files")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old calendars: {e}")
            return 0
