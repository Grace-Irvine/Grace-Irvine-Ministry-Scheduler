#!/usr/bin/env python3
"""
Calendar Scheduler - 日历自动同步调度器
负责定期同步Google Sheets数据并更新ICS日历文件

功能：
1. 定期检查Google Sheets更新
2. 自动生成和更新ICS日历文件
3. 管理同步状态和日志
4. 支持手动触发同步
"""

import os
import time
import logging
import threading
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import schedule

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CalendarScheduler:
    """日历同步调度器"""
    
    def __init__(self, 
                 ics_manager=None,
                 scheduler_instance=None,
                 config_path: str = "configs/calendar_config.yaml"):
        """初始化调度器
        
        Args:
            ics_manager: ICS管理器实例
            scheduler_instance: 数据提取器实例
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = None
        self.ics_manager = ics_manager
        self.scheduler_instance = scheduler_instance
        self.sync_thread = None
        self.is_running = False
        self.last_sync_time = None
        self.sync_status = "未开始"
        
        # 加载配置
        self.load_config()
        
        # 初始化组件
        if not self.ics_manager:
            from .ics_manager import ICSManager
            self.ics_manager = ICSManager(config_path)
        
        if not self.scheduler_instance:
            from .scheduler import GoogleSheetsExtractor
            spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID') or self.config.get('sync_settings', {}).get('google_sheets_id', '')
            if spreadsheet_id:
                self.scheduler_instance = GoogleSheetsExtractor(spreadsheet_id)
            else:
                logger.error("No Google Sheets ID configured")
    
    def load_config(self) -> bool:
        """加载配置文件
        
        Returns:
            是否加载成功
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Config file not found: {self.config_path}")
                return False
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Successfully loaded scheduler config from {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load scheduler config: {e}")
            return False
    
    def save_sync_status(self) -> bool:
        """保存同步状态到配置文件
        
        Returns:
            是否保存成功
        """
        try:
            if self.config and 'sync_settings' in self.config:
                self.config['sync_settings']['last_sync'] = self.last_sync_time.isoformat() if self.last_sync_time else None
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False, indent=2)
                
                return True
        except Exception as e:
            logger.error(f"Failed to save sync status: {e}")
            return False
    
    def sync_calendars(self) -> bool:
        """同步日历数据
        
        Returns:
            是否同步成功
        """
        try:
            logger.info("开始同步日历数据...")
            self.sync_status = "同步中"
            
            # 检查必要组件
            if not self.scheduler_instance:
                logger.error("Google Sheets extractor not initialized")
                self.sync_status = "同步失败 - 数据提取器未初始化"
                return False
            
            if not self.ics_manager:
                logger.error("ICS manager not initialized")
                self.sync_status = "同步失败 - ICS管理器未初始化"
                return False
            
            # 从Google Sheets获取最新数据
            logger.info("正在获取Google Sheets数据...")
            assignments = self.scheduler_instance.parse_ministry_data()
            
            if not assignments:
                logger.warning("No ministry assignments found")
                self.sync_status = "同步完成 - 无数据"
                return True
            
            logger.info(f"成功获取 {len(assignments)} 条事工安排")
            
            # 生成负责人日历
            logger.info("正在生成负责人日历...")
            coordinator_calendar_path = self.ics_manager.generate_coordinator_calendar(
                assignments,
                start_date=date.today() - timedelta(days=30),  # 包含过去30天
                end_date=date.today() + timedelta(days=90)     # 未来90天
            )
            logger.info(f"负责人日历已生成: {coordinator_calendar_path}")
            
            # 生成综合同工日历
            logger.info("正在生成同工日历...")
            worker_calendar_path = self.ics_manager.generate_worker_calendar(assignments)
            logger.info(f"同工日历已生成: {worker_calendar_path}")
            
            # 生成个人同工日历
            self._generate_personal_calendars(assignments)
            
            # 更新同步状态
            self.last_sync_time = datetime.now()
            self.sync_status = f"同步成功 - {self.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}"
            self.save_sync_status()
            
            logger.info("日历同步完成！")
            return True
            
        except Exception as e:
            logger.error(f"日历同步失败: {e}")
            self.sync_status = f"同步失败 - {str(e)}"
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_personal_calendars(self, assignments: List) -> None:
        """为每个同工生成个人日历
        
        Args:
            assignments: 事工安排列表
        """
        try:
            # 收集所有同工名单
            workers = set()
            for assignment in assignments:
                if assignment.audio_tech and assignment.audio_tech != "待安排":
                    workers.add(assignment.audio_tech)
                if assignment.screen_operator and assignment.screen_operator != "待安排":
                    workers.add(assignment.screen_operator)
                if assignment.camera_operator and assignment.camera_operator != "待安排":
                    workers.add(assignment.camera_operator)
                if assignment.propresenter and assignment.propresenter != "待安排":
                    workers.add(assignment.propresenter)
            
            logger.info(f"发现 {len(workers)} 位同工，正在生成个人日历...")
            
            # 为每位同工生成个人日历
            for worker in workers:
                try:
                    personal_calendar_path = self.ics_manager.generate_worker_calendar(assignments, worker)
                    logger.info(f"已生成 {worker} 的个人日历: {personal_calendar_path}")
                except Exception as e:
                    logger.error(f"生成 {worker} 个人日历时出错: {e}")
            
        except Exception as e:
            logger.error(f"生成个人日历时出错: {e}")
    
    def start_auto_sync(self) -> bool:
        """启动自动同步
        
        Returns:
            是否启动成功
        """
        try:
            if self.is_running:
                logger.warning("Auto sync is already running")
                return False
            
            # 检查配置
            sync_settings = self.config.get('sync_settings', {})
            if not sync_settings.get('auto_sync_enabled', False):
                logger.warning("Auto sync is disabled in config")
                return False
            
            sync_frequency = sync_settings.get('sync_frequency_hours', 12)
            
            # 设置定时任务
            schedule.clear()  # 清除之前的任务
            schedule.every(sync_frequency).hours.do(self.sync_calendars)
            
            # 启动调度线程
            self.is_running = True
            self.sync_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.sync_thread.start()
            
            logger.info(f"自动同步已启动，同步频率: 每 {sync_frequency} 小时")
            
            # 立即执行一次同步
            self.sync_calendars()
            
            return True
            
        except Exception as e:
            logger.error(f"启动自动同步失败: {e}")
            return False
    
    def stop_auto_sync(self) -> bool:
        """停止自动同步
        
        Returns:
            是否停止成功
        """
        try:
            if not self.is_running:
                logger.warning("Auto sync is not running")
                return False
            
            self.is_running = False
            schedule.clear()
            
            if self.sync_thread and self.sync_thread.is_alive():
                # 等待线程结束
                self.sync_thread.join(timeout=5)
            
            logger.info("自动同步已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止自动同步失败: {e}")
            return False
    
    def _run_scheduler(self) -> None:
        """运行调度器（在单独线程中）"""
        logger.info("调度器线程已启动")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器运行出错: {e}")
                time.sleep(60)
        
        logger.info("调度器线程已停止")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态信息
        
        Returns:
            同步状态字典
        """
        return {
            'is_running': self.is_running,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_status': self.sync_status,
            'next_sync_time': self._get_next_sync_time(),
            'sync_frequency_hours': self.config.get('sync_settings', {}).get('sync_frequency_hours', 12),
            'auto_sync_enabled': self.config.get('sync_settings', {}).get('auto_sync_enabled', False)
        }
    
    def _get_next_sync_time(self) -> Optional[str]:
        """获取下次同步时间
        
        Returns:
            下次同步时间的ISO格式字符串，如果未运行则返回None
        """
        if not self.is_running or not self.last_sync_time:
            return None
        
        try:
            sync_frequency = self.config.get('sync_settings', {}).get('sync_frequency_hours', 12)
            next_sync = self.last_sync_time + timedelta(hours=sync_frequency)
            return next_sync.isoformat()
        except:
            return None
    
    def force_sync(self) -> bool:
        """强制立即同步
        
        Returns:
            是否同步成功
        """
        logger.info("手动触发日历同步...")
        return self.sync_calendars()
    
    def cleanup_old_calendars(self, days_to_keep: int = 7) -> int:
        """清理旧的日历文件
        
        Args:
            days_to_keep: 保留的天数
            
        Returns:
            清理的文件数量
        """
        try:
            output_dir = Path(self.config.get('output_directory', 'calendars/'))
            if not output_dir.exists():
                return 0
            
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            for file_path in output_dir.glob('*.ics'):
                try:
                    if file_path.stat().st_mtime < cutoff_time.timestamp():
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"已清理旧日历文件: {file_path.name}")
                except Exception as e:
                    logger.warning(f"清理文件 {file_path.name} 时出错: {e}")
            
            if cleaned_count > 0:
                logger.info(f"共清理了 {cleaned_count} 个旧日历文件")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧日历文件时出错: {e}")
            return 0

def main():
    """测试函数"""
    try:
        # 初始化调度器
        scheduler = CalendarScheduler()
        
        print("日历调度器测试")
        print("=" * 50)
        
        # 显示当前状态
        status = scheduler.get_sync_status()
        print(f"当前状态: {status}")
        
        # 手动同步测试
        print("\n执行手动同步测试...")
        success = scheduler.force_sync()
        print(f"手动同步结果: {'成功' if success else '失败'}")
        
        # 显示更新后的状态
        status = scheduler.get_sync_status()
        print(f"同步后状态: {status}")
        
        # 清理测试
        print("\n执行清理测试...")
        cleaned_count = scheduler.cleanup_old_calendars(days_to_keep=1)
        print(f"清理了 {cleaned_count} 个旧文件")
        
        print("\n调度器测试完成！")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
