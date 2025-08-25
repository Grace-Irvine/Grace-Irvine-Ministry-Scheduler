"""
Grace Irvine Ministry Scheduler - Main FastAPI Application

This is the main entry point for the ministry scheduler application.
"""
import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

from app.core.config import get_settings
from app.api import schedules, notifications, calendars
from app.core.database import create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Grace Irvine Ministry Scheduler",
    description="Automated ministry schedule notification and calendar system",
    version="1.0.0",
    docs_url="/docs" if settings.features.enable_api else None,
    redoc_url="/redoc" if settings.features.enable_api else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
if settings.features.enable_api:
    app.include_router(
        schedules.router,
        prefix="/api/v1/schedules",
        tags=["schedules"]
    )
    app.include_router(
        notifications.router,
        prefix="/api/v1/notifications",
        tags=["notifications"]
    )
    app.include_router(
        calendars.router,
        prefix="/api/v1/calendars",
        tags=["calendars"]
    )

# Mount static files for calendar downloads
calendars_dir = Path(settings.calendar.output_directory)
calendars_dir.mkdir(parents=True, exist_ok=True)
app.mount("/calendars", StaticFiles(directory=str(calendars_dir)), name="calendars")

# Mount web UI if enabled
if settings.features.enable_web_ui:
    # This would mount a React/Vue frontend
    # For now, we'll serve a simple status page
    pass


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Grace Irvine Ministry Scheduler...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Create required directories
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    Path(settings.calendar.output_directory).mkdir(parents=True, exist_ok=True)
    
    logger.info("Grace Irvine Ministry Scheduler started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Grace Irvine Ministry Scheduler...")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic information"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Grace Irvine Ministry Scheduler</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #2E5984; }}
            .status {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 4px; margin: 20px 0; }}
            .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
            .feature {{ border: 1px solid #dee2e6; padding: 15px; border-radius: 4px; }}
            .links {{ margin: 20px 0; }}
            .links a {{ display: inline-block; margin: 5px 10px 5px 0; padding: 8px 16px; background-color: #2E5984; color: white; text-decoration: none; border-radius: 4px; }}
            .links a:hover {{ background-color: #1e3a5f; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>恩典尔湾长老教会 - 事工管理系统</h1>
            <h2>Grace Irvine Ministry Scheduler</h2>
            
            <div class="status">
                ✅ <strong>系统状态:</strong> 运行正常 | <strong>启动时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            
            <h3>🎯 系统功能</h3>
            <div class="features">
                <div class="feature">
                    <h4>📊 数据提取</h4>
                    <p>从 Google Sheets 自动提取事工排班数据</p>
                </div>
                <div class="feature">
                    <h4>📧 智能通知</h4>
                    <p>自动生成和发送邮件/短信通知</p>
                </div>
                <div class="feature">
                    <h4>📅 日历同步</h4>
                    <p>生成 .ics 日历文件和订阅链接</p>
                </div>
                <div class="feature">
                    <h4>⏰ 定时任务</h4>
                    <p>周三、周六、月初自动发送通知</p>
                </div>
            </div>
            
            <h3>🔗 快速链接</h3>
            <div class="links">
                {f'<a href="/docs">API 文档</a>' if settings.features.enable_api else ''}
                <a href="/calendars/ministry_schedule.ics">下载日历</a>
                <a href="/health">系统状态</a>
            </div>
            
            <h3>📱 日历订阅</h3>
            <p>订阅以下链接到您的日历应用（iPhone、Google Calendar、Outlook 等）：</p>
            <code>webcal://{settings.calendar.base_url or 'your-domain.com'}/calendars/ministry_schedule.ics</code>
            
            <hr style="margin: 30px 0;">
            <p style="text-align: center; color: #666; font-size: 14px;">
                Powered by Grace Irvine Ministry Scheduler v1.0.0<br>
                © 2024 Grace Irvine Presbyterian Church
            </p>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "features": {
            "api_enabled": settings.features.enable_api,
            "web_ui_enabled": settings.features.enable_web_ui,
            "webhooks_enabled": settings.features.enable_webhooks,
            "analytics_enabled": settings.features.enable_analytics,
        }
    }


@app.get("/calendar-subscription")
async def calendar_subscription_info():
    """Get calendar subscription information"""
    from app.services.calendar_service import CalendarService
    
    calendar_service = CalendarService()
    
    return {
        "calendar_name": settings.calendar.calendar_name,
        "subscription_url": calendar_service.get_subscription_url(),
        "download_url": calendar_service.get_download_url(),
        "instructions": {
            "iphone": "在 iPhone 设置 > 日历 > 账户 > 添加账户 > 其他 > 添加已订阅的日历，输入订阅链接",
            "google_calendar": "在 Google Calendar 左侧 > 其他日历 > + > 通过网址 > 输入订阅链接",
            "outlook": "在 Outlook > 日历 > 添加日历 > 从 Web 订阅 > 输入订阅链接"
        }
    }


# Simple manual trigger endpoints for testing
@app.post("/trigger/weekly-confirmation")
async def trigger_weekly_confirmation():
    """Manually trigger weekly confirmation notification"""
    if not settings.features.enable_api:
        raise HTTPException(status_code=404, detail="API not enabled")
    
    try:
        # Import here to avoid circular imports
        from app.services.scheduler_service import SchedulerService
        
        scheduler = SchedulerService()
        result = await scheduler.send_weekly_confirmation()
        
        return {
            "status": "success",
            "message": "Weekly confirmation notification triggered",
            "details": result
        }
    except Exception as e:
        logger.error(f"Failed to trigger weekly confirmation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/sunday-reminder")
async def trigger_sunday_reminder():
    """Manually trigger Sunday reminder notification"""
    if not settings.features.enable_api:
        raise HTTPException(status_code=404, detail="API not enabled")
    
    try:
        from app.services.scheduler_service import SchedulerService
        
        scheduler = SchedulerService()
        result = await scheduler.send_sunday_reminder()
        
        return {
            "status": "success",
            "message": "Sunday reminder notification triggered",
            "details": result
        }
    except Exception as e:
        logger.error(f"Failed to trigger Sunday reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/monthly-overview")
async def trigger_monthly_overview():
    """Manually trigger monthly overview notification"""
    if not settings.features.enable_api:
        raise HTTPException(status_code=404, detail="API not enabled")
    
    try:
        from app.services.scheduler_service import SchedulerService
        
        scheduler = SchedulerService()
        result = await scheduler.send_monthly_overview()
        
        return {
            "status": "success",
            "message": "Monthly overview notification triggered",
            "details": result
        }
    except Exception as e:
        logger.error(f"Failed to trigger monthly overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refresh-calendar")
async def refresh_calendar():
    """Manually refresh calendar files"""
    if not settings.features.enable_api:
        raise HTTPException(status_code=404, detail="API not enabled")
    
    try:
        from app.services.calendar_service import CalendarService
        from app.services.data_extractor import DataExtractor
        from datetime import date, timedelta
        
        # Extract latest data
        extractor = DataExtractor()
        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=365)
        
        schedules = extractor.extract_schedule_data(start_date, end_date)
        
        # Generate calendar
        calendar_service = CalendarService()
        file_path = calendar_service.generate_calendar_from_schedules(schedules)
        
        return {
            "status": "success",
            "message": "Calendar refreshed successfully",
            "file_path": str(file_path),
            "schedules_count": len(schedules),
            "subscription_url": calendar_service.get_subscription_url()
        }
    except Exception as e:
        logger.error(f"Failed to refresh calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level="info" if not settings.app.debug else "debug"
    )
