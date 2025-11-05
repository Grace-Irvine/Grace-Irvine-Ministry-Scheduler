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
from src.multi_calendar_generator import generate_all_calendars, generate_media_team_calendar, generate_children_team_calendar, generate_weekly_overview_calendar
from src.cloud_storage_manager import get_storage_manager
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
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "update_ics": "/api/update-ics",
            "calendars": {
                "media_team": "/calendars/media-team.ics",
                "children_team": "/calendars/children-team.ics",
                "weekly_overview": "/calendars/weekly-overview.ics"
            },
            "status": "/api/status"
        }
    }

@app.post("/api/update-ics")
async def update_ics_calendar(
    auth: bool = Depends(verify_auth_token),
    calendar_types: list = None
):
    """更新ICS日历文件 - 由Cloud Scheduler定时调用
    
    Args:
        calendar_types: 要更新的日历类型列表，如果为None则更新所有类型
                      可选值: ['media-team', 'children-team', 'weekly-overview']
    """
    try:
        logger.info("开始更新ICS日历文件...")
        
        # 生成所有日历
        results = await asyncio.to_thread(generate_all_calendars)
        
        if not results['success']:
            logger.error("部分ICS日历生成失败")
            return {
                "status": "partial_success",
                "message": "Some calendars failed to generate",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        
        # 保存生成的日历到存储
        storage_manager = get_storage_manager()
        saved_files = []
        
        for calendar_type, calendar_result in results['calendars'].items():
            if calendar_result['success'] and calendar_result['content']:
                filename = f"{calendar_type}.ics"
                saved = await asyncio.to_thread(
                    storage_manager.write_ics_calendar,
                    calendar_result['content'],
                    filename
                )
                if saved:
                    saved_files.append(filename)
                    logger.info(f"✅ 日历已保存: {filename}")
        
        logger.info(f"ICS日历生成成功，共保存 {len(saved_files)} 个文件")
        return {
            "status": "success",
            "message": "ICS calendars updated successfully",
            "calendars_generated": len(saved_files),
            "files_saved": saved_files,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
            
    except Exception as e:
        logger.error(f"更新ICS日历失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update ICS calendars: {str(e)}")

@app.get("/calendars/{calendar_type}.ics")
async def serve_calendar(calendar_type: str):
    """提供ICS日历文件下载
    
    Args:
        calendar_type: 日历类型 (media-team, children-team, weekly-overview)
    """
    valid_types = ['media-team', 'children-team', 'weekly-overview']
    
    if calendar_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid calendar type. Valid types: {', '.join(valid_types)}"
        )
    
    filename = f"{calendar_type}.ics"
    calendar_file = Path("calendars") / filename
    
    # 如果本地文件不存在，尝试从GCS读取
    if not calendar_file.exists():
        try:
            storage_manager = get_storage_manager()
            if storage_manager and storage_manager.is_cloud_mode:
                content = storage_manager.read_ics_calendar(filename)
                if content:
                    # 返回内容作为响应
                    from fastapi.responses import Response
                    return Response(
                        content=content,
                        media_type="text/calendar",
                        headers={
                            "Content-Disposition": f'attachment; filename="{filename}"'
                        }
                    )
        except Exception as e:
            logger.warning(f"从GCS读取日历失败: {e}")
    
    if not calendar_file.exists():
        raise HTTPException(status_code=404, detail=f"Calendar file not found: {filename}")
    
    return FileResponse(
        path=str(calendar_file),
        media_type="text/calendar",
        filename=filename
    )

@app.get("/api/status")
async def get_service_status():
    """获取服务状态信息"""
    storage_manager = get_storage_manager()
    calendar_types = ['media-team', 'children-team', 'weekly-overview']
    
    status = {
        "service": "Grace Irvine Ministry Scheduler API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "storage_mode": os.getenv("STORAGE_MODE", "local"),
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "not_set"),
        "bucket": os.getenv("GCP_STORAGE_BUCKET", "not_set"),
        "data_source_bucket": os.getenv("DATA_SOURCE_BUCKET", "grace-irvine-ministry-data"),
        "calendars": {}
    }
    
    # 检查每个日历文件的状态
    for calendar_type in calendar_types:
        filename = f"{calendar_type}.ics"
        calendar_file = Path("calendars") / filename
        
        calendar_status = {
            "exists": False,
            "size_bytes": 0,
            "last_modified": None
        }
        
        # 检查本地文件
        if calendar_file.exists():
            stat = calendar_file.stat()
            calendar_status["exists"] = True
            calendar_status["size_bytes"] = stat.st_size
            calendar_status["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        else:
            # 检查GCS文件
            try:
                if storage_manager and storage_manager.is_cloud_mode:
                    content = storage_manager.read_ics_calendar(filename)
                    if content:
                        calendar_status["exists"] = True
                        calendar_status["size_bytes"] = len(content.encode('utf-8'))
                        calendar_status["source"] = "gcs"
            except Exception as e:
                logger.warning(f"检查GCS日历状态失败: {e}")
        
        status["calendars"][calendar_type] = calendar_status
    
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
