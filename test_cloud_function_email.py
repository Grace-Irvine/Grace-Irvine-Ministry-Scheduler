#!/usr/bin/env python3
"""Test cloud function email generation with mock data"""

import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.email_sender import EmailSender, EmailRecipient
from src.scheduler import MinistryAssignment, NotificationGenerator
from src.template_manager import get_default_template_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email_with_assignment():
    """Test email generation with a mock assignment"""
    print("=" * 60)
    print("Testing Email Generation with Mock Assignment")
    print("=" * 60)
    
    try:
        # Create a mock assignment for this Sunday
        today = date.today()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        
        mock_assignment = MinistryAssignment(
            date=next_sunday,
            audio_tech="张三",
            screen_operator="李四",
            camera_operator="王五",
            propresenter="赵六",
            video_editor="靖铮"
        )
        
        print(f"\n1. Created mock assignment for: {mock_assignment.date}")
        print(f"   Audio Tech: {mock_assignment.audio_tech}")
        print(f"   Screen Operator: {mock_assignment.screen_operator}")
        print(f"   Camera Operator: {mock_assignment.camera_operator}")
        print(f"   ProPresenter: {mock_assignment.propresenter}")
        print(f"   Video Editor: {mock_assignment.video_editor}")
        
        # Initialize components
        print("\n2. Initializing components...")
        email_sender = EmailSender()
        template_manager = get_default_template_manager()
        
        # Test template engine
        print(f"\n3. Template engine status:")
        print(f"   Template environment: {email_sender.template_env is not None}")
        
        # Generate WeChat message using template manager
        print("\n4. Generating WeChat messages...")
        weekly_wechat = template_manager.render_weekly_confirmation(mock_assignment)
        sunday_wechat = template_manager.render_sunday_reminder(mock_assignment)
        
        print(f"\n   Weekly confirmation message:")
        print("   " + "-" * 40)
        print(weekly_wechat)
        
        print(f"\n   Sunday reminder message:")
        print("   " + "-" * 40)
        print(sunday_wechat)
        
        # Test email HTML rendering
        print("\n5. Testing email HTML rendering...")
        
        # Prepare context for weekly confirmation
        week_start = next_sunday - timedelta(days=next_sunday.weekday())
        week_end = week_start + timedelta(days=6)
        week_range = f"{week_start.month}月{week_start.day}日-{week_end.month}月{week_end.day}日"
        
        weekly_context = {
            'wechat_message': weekly_wechat,
            'week_range': week_range,
            'assignment': mock_assignment,
            'total_services': 1,
            'total_assignments': 5,
            'unique_volunteers': 5,
            'volunteer_list': ['张三', '李四', '王五', '赵六', '靖铮'],
            'roles': {
                '音控': mock_assignment.audio_tech,
                '屏幕': mock_assignment.screen_operator,
                '摄像/导播': mock_assignment.camera_operator,
                'ProPresenter制作': mock_assignment.propresenter,
                '视频剪辑': mock_assignment.video_editor
            }
        }
        
        # Render weekly confirmation email
        weekly_html = email_sender.render_template('weekly_confirmation_wechat.html', weekly_context)
        print(f"   Weekly confirmation HTML length: {len(weekly_html)} characters")
        
        # Prepare context for Sunday reminder
        sunday_context = {
            'wechat_message': sunday_wechat,
            'service_date': next_sunday,
            'service_time': '10:00',
            'arrival_time': '09:30',
            'location': 'Grace Irvine 教会',
            'assignment': mock_assignment,
            'assignments_count': 5,
            'roles': {
                '音控': mock_assignment.audio_tech,
                '屏幕': mock_assignment.screen_operator,
                '摄像/导播': mock_assignment.camera_operator,
                'ProPresenter制作': mock_assignment.propresenter,
                '视频剪辑': mock_assignment.video_editor
            }
        }
        
        # Render Sunday reminder email
        sunday_html = email_sender.render_template('sunday_reminder_wechat.html', sunday_context)
        print(f"   Sunday reminder HTML length: {len(sunday_html)} characters")
        
        if weekly_html and sunday_html:
            print("\n   ✅ Both email templates rendered successfully!")
            
            # Save to files for inspection
            with open("test_weekly_email.html", "w", encoding="utf-8") as f:
                f.write(weekly_html)
            print("   Saved weekly email to: test_weekly_email.html")
            
            with open("test_sunday_email.html", "w", encoding="utf-8") as f:
                f.write(sunday_html)
            print("   Saved Sunday email to: test_sunday_email.html")
        else:
            print("\n   ❌ Email template rendering failed")
        
        print("\n" + "=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email_with_assignment()
