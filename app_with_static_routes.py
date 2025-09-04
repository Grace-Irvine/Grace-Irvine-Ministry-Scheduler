#!/usr/bin/env python3
"""
Grace Irvine Ministry Scheduler - FastAPI + Streamlit 混合应用
支持静态文件路由和ICS日历订阅
"""

import os
import sys
import uvicorn
import threading
import time
import subprocess
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json

# 创建FastAPI应用
app = FastAPI(title="Grace Irvine Ministry Scheduler")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/calendars/{filename}")
async def serve_calendar(filename: str):
    """提供ICS日历文件下载"""
    try:
        calendar_dir = Path("calendars")
        if not calendar_dir.exists():
            raise HTTPException(status_code=404, detail="Calendar directory not found")
        
        file_path = calendar_dir / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Calendar file {filename} not found")
        
        if not filename.endswith('.ics'):
            raise HTTPException(status_code=400, detail="Only ICS files are allowed")
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type='text/calendar; charset=utf-8',
            filename=filename,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache, must-revalidate",
                "Pragma": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving calendar file: {str(e)}")

@app.post("/api/update-calendars")
async def update_calendars():
    """API端点：更新ICS日历文件"""
    try:
        # 调用真实的日历生成逻辑
        import subprocess
        
        result = subprocess.run([
            'python3', 'generate_real_calendars.py'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return {
                'success': True,
                'message': 'Calendar files updated successfully',
                'timestamp': datetime.now().isoformat(),
                'output': result.stdout
            }
        else:
            return {
                'success': False,
                'message': 'Calendar update failed',
                'error': result.stderr,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """API端点：获取系统状态"""
    try:
        calendar_dir = Path("calendars")
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'Grace Irvine Ministry Scheduler',
            'environment': 'Cloud Run' if 'K_SERVICE' in os.environ else 'Local',
            'working_directory': str(Path.cwd()),
            'calendars': {}
        }
        
        if calendar_dir.exists():
            for ics_file in calendar_dir.glob("*.ics"):
                try:
                    stat = ics_file.stat()
                    with open(ics_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    status['calendars'][ics_file.name] = {
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'events': content.count("BEGIN:VEVENT"),
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'valid_ics': content.startswith('BEGIN:VCALENDAR') and content.endswith('END:VCALENDAR')
                    }
                except Exception as e:
                    status['calendars'][ics_file.name] = {
                        'error': str(e)
                    }
        else:
            status['calendar_directory'] = 'Not found'
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Grace Irvine Ministry Scheduler'
    }

@app.get("/debug")
async def debug_info():
    """调试信息端点"""
    try:
        # 运行调试脚本
        result = subprocess.run([
            'python3', 'debug_calendar_files.py'
        ], capture_output=True, text=True, timeout=30)
        
        return {
            'debug_output': result.stdout,
            'debug_errors': result.stderr,
            'return_code': result.returncode,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def start_streamlit():
    """启动Streamlit应用"""
    try:
        # 启动Streamlit应用
        subprocess.run([
            'streamlit', 'run', 'streamlit_app.py',
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--server.headless=true',
            '--server.fileWatcherType=none',
            '--browser.gatherUsageStats=false'
        ], check=True)
    except Exception as e:
        print(f"Streamlit启动失败: {e}")

def main():
    """主函数"""
    print("🚀 启动Grace Irvine Ministry Scheduler")
    print("=" * 50)
    
    # 检查环境
    if 'K_SERVICE' in os.environ:
        print("✅ 运行在Cloud Run环境")
        port = int(os.getenv('PORT', 8080))
    else:
        print("ℹ️ 运行在本地环境")
        port = 8080
    
    # 创建日历目录
    calendar_dir = Path("calendars")
    calendar_dir.mkdir(exist_ok=True)
    print(f"📁 日历目录: {calendar_dir.absolute()}")
    
    # 在后台启动Streamlit（仅在本地环境）
    if 'K_SERVICE' not in os.environ:
        streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
        streamlit_thread.start()
        time.sleep(2)
        print("✅ Streamlit应用已启动在端口8501")
    
    # 启动FastAPI服务器
    print(f"🌐 启动FastAPI服务器在端口{port}")
    print(f"📅 日历订阅URL:")
    print(f"   负责人日历: http://localhost:{port}/calendars/grace_irvine_coordinator.ics")
    print(f"   同工日历: http://localhost:{port}/calendars/grace_irvine_workers.ics")
    print(f"📊 API状态: http://localhost:{port}/api/status")
    print(f"🔍 调试信息: http://localhost:{port}/debug")
    print("=" * 50)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")

if __name__ == "__main__":
    main()
