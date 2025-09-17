#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - API Service
纯API服务启动脚本，专门处理定时任务和API调用
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import json

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入项目模块
from src.models import MinistryAssignment, ServiceRole
from src.data_cleaner import FocusedDataCleaner
from src.template_manager import NotificationTemplateManager
from src.dynamic_template_manager import DynamicTemplateManager
from src.scheduler import GoogleSheetsExtractor, NotificationGenerator
from src.email_sender import EmailSender, EmailRecipient
from src.calendar_generator import generate_coordinator_calendar
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Grace Irvine Ministry Scheduler API",
    description="恩典尔湾长老教会事工排程管理系统 API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 认证令牌验证
def verify_auth_token(x_auth_token: str = Header(None)):
    """验证认证令牌"""
    expected_token = os.getenv("SCHEDULER_AUTH_TOKEN", "grace-irvine-scheduler-2025")
    if x_auth_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return True

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Grace Irvine Ministry Scheduler API"
    }

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Grace Irvine Ministry Scheduler API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "update_ics": "/api/update-ics",
            "calendar": "/calendar.ics"
        }
    }

@app.post("/api/update-ics")
async def update_ics_calendar(auth: bool = Depends(verify_auth_token)):
    """更新ICS日历文件 - 由Cloud Scheduler定时调用"""
    try:
        logger.info("开始更新ICS日历文件...")
        
        # 直接使用generate_coordinator_calendar函数，它会自己处理数据获取
        logger.info("生成负责人日历...")
        
        # 在异步上下文中运行日历生成
        success = await asyncio.to_thread(generate_coordinator_calendar)
        
        if success:
            logger.info("ICS日历生成成功")
            return {
                "status": "success",
                "message": "ICS calendar updated successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("ICS日历生成失败")
            return {
                "status": "error",
                "message": "Failed to generate ICS calendar",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"更新ICS日历失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update ICS calendar: {str(e)}")

@app.get("/calendar.ics")
async def serve_calendar():
    """提供ICS日历文件下载"""
    calendar_file = Path("calendars") / "grace_irvine_coordinator.ics"
    
    if not calendar_file.exists():
        raise HTTPException(status_code=404, detail="Calendar file not found")
    
    return FileResponse(
        path=str(calendar_file),
        media_type="text/calendar",
        filename="grace_irvine_coordinator.ics"
    )

@app.get("/api/status")
async def get_service_status():
    """获取服务状态信息"""
    calendar_file = Path("calendars") / "grace_irvine_coordinator.ics"
    
    status = {
        "service": "Grace Irvine Ministry Scheduler API",
        "timestamp": datetime.now().isoformat(),
        "calendar_file_exists": calendar_file.exists(),
        "storage_mode": os.getenv("STORAGE_MODE", "local"),
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "not_set"),
        "bucket": os.getenv("GCP_STORAGE_BUCKET", "not_set")
    }
    
    if calendar_file.exists():
        stat = calendar_file.stat()
        status["calendar_last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        status["calendar_size_bytes"] = stat.st_size
    
    return status

def main():
    """启动API服务"""
    port = int(os.getenv("PORT", 8080))
    
    logger.info(f"启动Grace Irvine Ministry Scheduler API服务...")
    logger.info(f"端口: {port}")
    logger.info(f"存储模式: {os.getenv('STORAGE_MODE', 'local')}")
    logger.info(f"项目ID: {os.getenv('GOOGLE_CLOUD_PROJECT', 'not_set')}")
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
