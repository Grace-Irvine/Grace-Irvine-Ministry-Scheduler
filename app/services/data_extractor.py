"""
Google Sheets Data Extraction Service

Based on the Grace-Irvine-Ministry-data-visualizer pattern but optimized for
notification scheduling needs.
"""
import logging
from datetime import datetime, date, time
from typing import List, Dict, Optional, Any, Tuple
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import re
from dataclasses import dataclass

from app.models.schedule import MinistrySchedule, ScheduleData, ServiceType
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ColumnConfig:
    """Configuration for Google Sheets columns"""
    date: str
    time: str
    location: str
    roles: List[Dict[str, str]]  # [{"key": "D", "service_type": "主席"}, ...]
    notes: str


class DataExtractor:
    """
    Extract ministry schedule data from Google Sheets
    
    This class handles:
    1. Google Sheets API authentication
    2. Data extraction with configurable column mapping
    3. Data cleaning and standardization
    4. Converting to structured ScheduleData objects
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.spreadsheet = None
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Initialize Google Sheets client"""
        try:
            # Use service account credentials
            credentials = Credentials.from_service_account_file(
                self.settings.google_sheets.service_account_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(
                self.settings.google_sheets.spreadsheet_id
            )
            
            logger.info(f"Successfully connected to Google Sheets: {self.settings.google_sheets.spreadsheet_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets client: {e}")
            raise
    
    def _get_column_config(self) -> ColumnConfig:
        """Get column configuration from settings"""
        columns = self.settings.google_sheets.columns
        return ColumnConfig(
            date=columns.date,
            time=columns.get("time", "B"),
            location=columns.get("location", "C"),
            roles=columns.roles,
            notes=columns.notes
        )
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse various date formats from Google Sheets
        
        Supports formats like:
        - 2024/1/14
        - 2024-01-14
        - 1/14/2024
        - Jan 14, 2024
        """
        if not date_str or pd.isna(date_str):
            return None
        
        date_str = str(date_str).strip()
        if not date_str:
            return None
        
        # Common date patterns
        patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # 2024/1/14 or 2024-01-14
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # 1/14/2024 or 01-14-2024
        ]
        
        for pattern in patterns:
            match = re.match(pattern, date_str)
            if match:
                parts = [int(x) for x in match.groups()]
                
                # Determine order based on pattern
                if len(str(parts[0])) == 4:  # Year first
                    year, month, day = parts
                else:  # Year last
                    month, day, year = parts
                
                try:
                    return date(year, month, day)
                except ValueError:
                    continue
        
        # Try pandas date parsing as fallback
        try:
            parsed_date = pd.to_datetime(date_str, infer_datetime_format=True)
            return parsed_date.date()
        except:
            logger.warning(f"Could not parse date: {date_str}")
            return None
    
    def _parse_time(self, time_str: str) -> Optional[time]:
        """
        Parse time from Google Sheets
        
        Supports formats like:
        - 10:00
        - 10:00 AM
        - 22:00
        """
        if not time_str or pd.isna(time_str):
            return None
        
        time_str = str(time_str).strip()
        if not time_str:
            return None
        
        # Remove AM/PM and convert to 24-hour format
        is_pm = 'PM' in time_str.upper() or 'pm' in time_str
        is_am = 'AM' in time_str.upper() or 'am' in time_str
        time_str = re.sub(r'[APap][Mm]', '', time_str).strip()
        
        # Parse time
        try:
            if ':' in time_str:
                hour, minute = map(int, time_str.split(':'))
            else:
                hour = int(time_str)
                minute = 0
            
            # Convert to 24-hour format
            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0
            
            return time(hour, minute)
        except ValueError:
            logger.warning(f"Could not parse time: {time_str}")
            return None
    
    def _clean_person_name(self, name: str) -> Optional[str]:
        """Clean and standardize person names"""
        if not name or pd.isna(name):
            return None
        
        name = str(name).strip()
        if not name or name in ['', '-', 'N/A', 'TBD', '待定']:
            return None
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name)
        
        return name
    
    def _extract_roles_from_row(self, row_data: Dict[str, Any], column_config: ColumnConfig) -> Dict[str, str]:
        """Extract role assignments from a single row"""
        roles = {}
        
        for role_config in column_config.roles:
            column_key = role_config["key"]
            service_type = role_config["service_type"]
            
            # Get person name from the specified column
            person_name = row_data.get(column_key)
            cleaned_name = self._clean_person_name(person_name)
            
            if cleaned_name:
                roles[service_type] = cleaned_name
        
        return roles
    
    def extract_raw_data(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Extract raw data from Google Sheets as DataFrame
        
        Args:
            sheet_name: Name of the sheet to extract from
            
        Returns:
            DataFrame with raw sheet data
        """
        if not sheet_name:
            sheet_name = self.settings.google_sheets.sheet_name
        
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            
            # Get all values from the sheet
            all_values = worksheet.get_all_values()
            
            if not all_values:
                logger.warning(f"No data found in sheet: {sheet_name}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            # First row as headers
            headers = all_values[0]
            data = all_values[1:]
            
            df = pd.DataFrame(data, columns=headers)
            
            # Create column mapping based on position
            column_mapping = {}
            for i, header in enumerate(headers):
                column_letter = chr(ord('A') + i)
                column_mapping[column_letter] = header
            
            # Add column letters as additional columns for easier access
            for letter, header in column_mapping.items():
                if header in df.columns:
                    df[letter] = df[header]
            
            logger.info(f"Extracted {len(df)} rows from sheet: {sheet_name}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to extract data from sheet {sheet_name}: {e}")
            raise
    
    def extract_schedule_data(
        self, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sheet_name: Optional[str] = None
    ) -> List[ScheduleData]:
        """
        Extract and process ministry schedule data
        
        Args:
            start_date: Filter schedules from this date (inclusive)
            end_date: Filter schedules to this date (inclusive)
            sheet_name: Name of the sheet to extract from
            
        Returns:
            List of ScheduleData objects
        """
        # Get raw data
        df = self.extract_raw_data(sheet_name)
        if df.empty:
            return []
        
        column_config = self._get_column_config()
        schedule_data = []
        
        for index, row in df.iterrows():
            try:
                # Parse date
                parsed_date = self._parse_date(row.get(column_config.date))
                if not parsed_date:
                    continue  # Skip rows without valid dates
                
                # Apply date filter
                if start_date and parsed_date < start_date:
                    continue
                if end_date and parsed_date > end_date:
                    continue
                
                # Parse time
                parsed_time = self._parse_time(row.get(column_config.time))
                if not parsed_time:
                    parsed_time = time(10, 0)  # Default to 10:00 AM
                
                # Parse location
                location = str(row.get(column_config.location, "")).strip()
                if not location:
                    location = "主堂"  # Default location
                
                # Extract roles
                roles = self._extract_roles_from_row(row.to_dict(), column_config)
                
                # Only include rows with at least one role assignment
                if not roles:
                    continue
                
                # Parse notes
                notes = str(row.get(column_config.notes, "")).strip()
                if not notes or notes in ['', '-', 'N/A']:
                    notes = None
                
                # Create ScheduleData object
                schedule = ScheduleData(
                    date=parsed_date,
                    time=parsed_time,
                    location=location,
                    roles=roles,
                    notes=notes
                )
                
                schedule_data.append(schedule)
                
            except Exception as e:
                logger.warning(f"Error processing row {index}: {e}")
                continue
        
        # Sort by date and time
        schedule_data.sort(key=lambda x: (x.date, x.time))
        
        logger.info(f"Successfully extracted {len(schedule_data)} valid schedules")
        return schedule_data
    
    def convert_to_database_records(self, schedule_data: List[ScheduleData]) -> List[MinistrySchedule]:
        """
        Convert ScheduleData objects to database records
        
        Args:
            schedule_data: List of ScheduleData objects
            
        Returns:
            List of MinistrySchedule database objects
        """
        records = []
        
        for schedule in schedule_data:
            # Create a separate record for each role assignment
            for service_type, person_name in schedule.roles.items():
                record = MinistrySchedule(
                    date=schedule.date,
                    time=schedule.time,
                    location=schedule.location,
                    service_type=service_type,
                    person_name=person_name,
                    notes=schedule.notes
                )
                records.append(record)
        
        return records
    
    def get_data_summary(self, schedule_data: List[ScheduleData]) -> Dict[str, Any]:
        """
        Get summary statistics for the extracted data
        
        Args:
            schedule_data: List of ScheduleData objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not schedule_data:
            return {
                "total_services": 0,
                "total_assignments": 0,
                "unique_volunteers": 0,
                "date_range": None,
                "service_types": [],
                "locations": []
            }
        
        # Calculate statistics
        all_assignments = []
        all_volunteers = set()
        all_service_types = set()
        all_locations = set()
        
        for schedule in schedule_data:
            all_assignments.extend(schedule.get_all_assignments())
            all_volunteers.update(schedule.roles.values())
            all_service_types.update(schedule.roles.keys())
            all_locations.add(schedule.location)
        
        # Date range
        dates = [s.date for s in schedule_data]
        date_range = f"{min(dates)} to {max(dates)}" if dates else None
        
        return {
            "total_services": len(schedule_data),
            "total_assignments": len(all_assignments),
            "unique_volunteers": len(all_volunteers),
            "date_range": date_range,
            "service_types": sorted(list(all_service_types)),
            "locations": sorted(list(all_locations)),
            "volunteers": sorted(list(all_volunteers))
        }
    
    def test_connection(self) -> bool:
        """Test the Google Sheets connection"""
        try:
            # Try to access the spreadsheet metadata
            sheet_info = self.spreadsheet.fetch_sheet_metadata()
            logger.info(f"Connection test successful. Sheet title: {sheet_info.get('properties', {}).get('title', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
