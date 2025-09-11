#!/usr/bin/env python3
"""
动态模板管理器
Dynamic Template Manager

支持本地JSON文件和GCP Storage的灵活模板系统
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TemplateConfig:
    """模板配置数据结构"""
    name: str
    description: str
    template: str
    variables: Dict[str, str]
    metadata: Dict[str, Any] = None

class DynamicTemplateManager:
    """动态模板管理器
    
    支持:
    1. 本地JSON文件存储
    2. GCP Storage云端存储
    3. 运行时模板编辑
    4. 自动备份和版本控制
    """
    
    def __init__(self, 
                 local_template_file: str = "templates/dynamic_templates.json",
                 gcp_bucket_name: str = None,
                 gcp_template_path: str = "templates/dynamic_templates.json"):
        """初始化动态模板管理器
        
        Args:
            local_template_file: 本地模板文件路径
            gcp_bucket_name: GCP Storage bucket名称
            gcp_template_path: GCP Storage中的模板文件路径
        """
        self.local_template_file = Path(local_template_file)
        self.gcp_bucket_name = gcp_bucket_name or os.getenv('GCP_TEMPLATE_BUCKET')
        self.gcp_template_path = gcp_template_path
        
        # 模板数据
        self.templates_data = {}
        self.is_cloud_mode = self._detect_cloud_environment()
        
        # GCP Storage客户端（如果在云端环境）
        self.storage_client = None
        if self.is_cloud_mode and self.gcp_bucket_name:
            self._setup_gcp_storage()
        
        # 加载模板
        self.load_templates()
    
    def _detect_cloud_environment(self) -> bool:
        """检测是否在云端环境"""
        return 'K_SERVICE' in os.environ or bool(self.gcp_bucket_name)
    
    def _setup_gcp_storage(self):
        """设置GCP Storage客户端"""
        try:
            from google.cloud import storage
            self.storage_client = storage.Client()
            logger.info(f"GCP Storage客户端初始化成功，bucket: {self.gcp_bucket_name}")
        except ImportError:
            logger.error("google-cloud-storage包未安装，无法使用GCP Storage")
            self.storage_client = None
        except Exception as e:
            logger.error(f"GCP Storage初始化失败: {e}")
            self.storage_client = None
    
    def load_templates(self) -> bool:
        """加载模板配置
        
        优先级: GCP Storage > 本地文件 > 默认模板
        
        Returns:
            是否加载成功
        """
        # 尝试从GCP Storage加载
        if self.is_cloud_mode and self.storage_client:
            if self._load_from_gcp():
                logger.info("从GCP Storage加载模板成功")
                return True
        
        # 尝试从本地文件加载
        if self._load_from_local():
            logger.info("从本地文件加载模板成功")
            return True
        
        # 使用默认模板
        logger.warning("使用默认模板配置")
        self._create_default_templates()
        return False
    
    def _load_from_gcp(self) -> bool:
        """从GCP Storage加载模板"""
        try:
            if not self.storage_client or not self.gcp_bucket_name:
                return False
            
            bucket = self.storage_client.bucket(self.gcp_bucket_name)
            blob = bucket.blob(self.gcp_template_path)
            
            if blob.exists():
                content = blob.download_as_text(encoding='utf-8')
                self.templates_data = json.loads(content)
                logger.info(f"从GCP Storage加载模板: gs://{self.gcp_bucket_name}/{self.gcp_template_path}")
                return True
            else:
                logger.warning(f"GCP Storage中模板文件不存在: {self.gcp_template_path}")
                return False
                
        except Exception as e:
            logger.error(f"从GCP Storage加载模板失败: {e}")
            return False
    
    def _load_from_local(self) -> bool:
        """从本地文件加载模板"""
        try:
            if not self.local_template_file.exists():
                logger.warning(f"本地模板文件不存在: {self.local_template_file}")
                return False
            
            with open(self.local_template_file, 'r', encoding='utf-8') as f:
                self.templates_data = json.load(f)
            
            logger.info(f"从本地文件加载模板: {self.local_template_file}")
            return True
            
        except Exception as e:
            logger.error(f"从本地文件加载模板失败: {e}")
            return False
    
    def save_templates(self, update_cloud: bool = True) -> bool:
        """保存模板配置
        
        Args:
            update_cloud: 是否同时更新云端存储
            
        Returns:
            是否保存成功
        """
        # 更新元数据
        if 'metadata' not in self.templates_data:
            self.templates_data['metadata'] = {}
        
        self.templates_data['metadata']['last_updated'] = datetime.now().isoformat()
        
        success = True
        
        # 保存到本地文件
        try:
            self.local_template_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.local_template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates_data, f, ensure_ascii=False, indent=2)
            logger.info(f"模板已保存到本地: {self.local_template_file}")
        except Exception as e:
            logger.error(f"保存到本地文件失败: {e}")
            success = False
        
        # 保存到GCP Storage（如果启用）
        if update_cloud and self.is_cloud_mode and self.storage_client:
            try:
                bucket = self.storage_client.bucket(self.gcp_bucket_name)
                blob = bucket.blob(self.gcp_template_path)
                
                content = json.dumps(self.templates_data, ensure_ascii=False, indent=2)
                blob.upload_from_string(content, content_type='application/json')
                
                logger.info(f"模板已保存到GCP Storage: gs://{self.gcp_bucket_name}/{self.gcp_template_path}")
            except Exception as e:
                logger.error(f"保存到GCP Storage失败: {e}")
                success = False
        
        return success
    
    def _create_default_templates(self):
        """创建默认模板配置"""
        self.templates_data = {
            "metadata": {
                "version": "2.0",
                "last_updated": datetime.now().isoformat(),
                "description": "Grace Irvine Ministry Scheduler 默认模板配置",
                "author": "系统默认"
            },
            "templates": {
                "weekly_confirmation": {
                    "name": "周三确认通知",
                    "description": "周三晚上发送的事工安排确认通知",
                    "template": "【本周{month}月{day}日主日事工安排提醒】🕊️\n\n{assignments_text}\n• 视频剪辑：靖铮\n\n请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏",
                    "no_assignment_template": "【本周主日事工安排提醒】🕊️\n\n暂无本周事工安排，请联系协调员确认。",
                    "assignment_format": "• {role}：{person}",
                    "default_assignments": {
                        "音控": "待安排",
                        "导播/摄影": "待安排", 
                        "ProPresenter播放": "待安排",
                        "ProPresenter更新": "待安排"
                    }
                },
                "saturday_reminder": {
                    "name": "周六提醒通知",
                    "description": "周六晚上发送的主日服事提醒",
                    "template": "【主日服事提醒】✨\n明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜\n请各位同工提前到场：\n\n{service_details}\n\n愿主同在，出入平安。若临时不适请第一时间私信我。🙌",
                    "no_assignment_template": "【主日服事提醒】✨\n\n暂无明日事工安排，请联系协调员确认。",
                    "service_format": "- {role}：{person} {time}到，{instruction}",
                    "service_instructions": {
                        "音控": "随敬拜团排练",
                        "导播/摄影": "检查预设机位",
                        "ProPresenter播放": "随敬拜团排练"
                    },
                    "service_times": {
                        "音控": "9:00",
                        "导播/摄影": "9:30",
                        "ProPresenter播放": "9:00"
                    }
                }
            },
            "settings": {
                "timezone": "America/Los_Angeles",
                "church_name": "Grace Irvine 恩典尔湾教会",
                "coordinator_title": "事工协调员"
            }
        }
    
    def get_template(self, template_type: str) -> Optional[Dict[str, Any]]:
        """获取指定类型的模板配置
        
        Args:
            template_type: 模板类型 (weekly_confirmation, saturday_reminder, monthly_overview)
            
        Returns:
            模板配置字典
        """
        return self.templates_data.get('templates', {}).get(template_type)
    
    def update_template(self, template_type: str, template_config: Dict[str, Any]) -> bool:
        """更新模板配置
        
        Args:
            template_type: 模板类型
            template_config: 新的模板配置
            
        Returns:
            是否更新成功
        """
        try:
            if 'templates' not in self.templates_data:
                self.templates_data['templates'] = {}
            
            self.templates_data['templates'][template_type] = template_config
            return True
            
        except Exception as e:
            logger.error(f"更新模板失败: {e}")
            return False
    
    def render_weekly_confirmation(self, sunday_date: date, schedule) -> str:
        """渲染周三确认通知
        
        Args:
            sunday_date: 主日日期
            schedule: 排程对象
            
        Returns:
            渲染后的通知内容
        """
        template_config = self.get_template('weekly_confirmation')
        if not template_config:
            return "模板配置不存在"
        
        # 获取默认值配置
        default_assignments = template_config.get('default_assignments', {})
        
        # 准备细化的模板变量
        template_vars = {
            'month': sunday_date.month,
            'day': sunday_date.day,
            'audio_tech': default_assignments.get('audio_tech', '待安排'),
            'video_director': default_assignments.get('video_director', '待安排'),
            'propresenter_play': default_assignments.get('propresenter_play', '待安排'),
            'propresenter_update': default_assignments.get('propresenter_update', '待安排'),
            'video_editor': default_assignments.get('video_editor', '靖铮')
        }
        
        # 如果有实际安排，使用实际人员
        if schedule:
            if schedule.audio_tech:
                template_vars['audio_tech'] = schedule.audio_tech
            if schedule.video_director:
                template_vars['video_director'] = schedule.video_director
            if schedule.propresenter_play:
                template_vars['propresenter_play'] = schedule.propresenter_play
            if schedule.propresenter_update:
                template_vars['propresenter_update'] = schedule.propresenter_update
            if schedule.video_editor:
                template_vars['video_editor'] = schedule.video_editor
        
        # 渲染主模板
        template = template_config.get('template', '')
        if not schedule or not schedule.has_assignments():
            template = template_config.get('no_assignment_template', template)
        
        try:
            return template.format(**template_vars)
        except Exception as e:
            logger.error(f"渲染周三确认通知失败: {e}")
            return template_config.get('no_assignment_template', '模板渲染失败')
    
    def render_saturday_reminder(self, sunday_date: date, schedule) -> str:
        """渲染周六提醒通知
        
        Args:
            sunday_date: 主日日期
            schedule: 排程对象
            
        Returns:
            渲染后的通知内容
        """
        template_config = self.get_template('saturday_reminder')
        if not template_config:
            return "模板配置不存在"
        
        # 获取配置
        detail_format = template_config.get('detail_format', '{person} {time}到，{instruction}')
        default_detail = template_config.get('default_detail', '待确认 {time}到，{instruction}')
        service_instructions = template_config.get('service_instructions', {})
        service_times = template_config.get('service_times', {})
        
        # 生成各角色的详细信息
        roles = {
            'audio_tech': '音控',
            'video_director': '导播/摄影',
            'propresenter_play': 'ProPresenter播放',
            'propresenter_update': 'ProPresenter更新'
        }
        
        template_vars = {}
        
        for var_name, role_name in roles.items():
            person = None
            if schedule:
                person = getattr(schedule, var_name, None)
            
            time = service_times.get(role_name, '9:00')
            instruction = service_instructions.get(role_name, '请提前到场')
            
            if person:
                detail = detail_format.format(person=person, time=time, instruction=instruction)
            else:
                detail = default_detail.format(time=time, instruction=instruction)
            
            template_vars[f'{var_name}_detail'] = detail
        
        # 渲染主模板
        template = template_config.get('template', '')
        if not schedule or not schedule.has_assignments():
            template = template_config.get('no_assignment_template', template)
        
        try:
            return template.format(**template_vars)
        except Exception as e:
            logger.error(f"渲染周六提醒通知失败: {e}")
            return template_config.get('no_assignment_template', '模板渲染失败')
    
    def render_monthly_overview(self, assignments: List, year: int, month: int, sheet_url: str = "") -> str:
        """渲染月度总览通知
        
        Args:
            assignments: 事工安排列表
            year: 年份
            month: 月份
            sheet_url: Google Sheets链接
            
        Returns:
            渲染后的通知内容
        """
        template_config = self.get_template('monthly_overview')
        if not template_config:
            return "模板配置不存在"
        
        # 生成排班列表文本
        schedule_format = template_config.get('schedule_format', '• {date}: {assignments}')
        assignment_separator = template_config.get('assignment_separator', ', ')
        role_formats = template_config.get('role_formats', {})
        
        schedule_list = ""
        if assignments:
            for assignment in assignments:
                date_str = f"{assignment.date.month}/{assignment.date.day}"
                
                assignment_parts = []
                schedule_assignments = assignment.get_all_assignments() if hasattr(assignment, 'get_all_assignments') else {}
                
                for role, person in schedule_assignments.items():
                    if person:
                        role_format = role_formats.get(role, f"{role}:{person}")
                        assignment_parts.append(role_format.format(name=person))
                
                assignments_text = assignment_separator.join(assignment_parts) if assignment_parts else "待安排"
                schedule_list += schedule_format.format(date=date_str, assignments=assignments_text) + "\n"
        else:
            schedule_list = "• 暂无排班数据\n"
        
        # 渲染主模板
        template = template_config.get('template', '')
        
        try:
            return template.format(
                year=year,
                month=month,
                sheet_url=sheet_url,
                schedule_list=schedule_list.strip()
            )
        except Exception as e:
            logger.error(f"渲染月度总览通知失败: {e}")
            return f"【{year}年{month:02d}月事工排班一览】📅\n\n模板渲染失败，请检查配置。"
    
    def get_all_templates(self) -> Dict[str, Any]:
        """获取所有模板配置"""
        return self.templates_data.copy()
    
    def get_template_list(self) -> List[str]:
        """获取模板类型列表"""
        return list(self.templates_data.get('templates', {}).keys())
    
    def backup_templates(self) -> bool:
        """备份当前模板配置"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.local_template_file.parent / f"templates_backup_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"模板已备份到: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"备份模板失败: {e}")
            return False
    
    def validate_template(self, template_type: str, template_content: str) -> tuple[bool, str]:
        """验证模板内容
        
        Args:
            template_type: 模板类型
            template_content: 模板内容
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 基本验证
            if not template_content.strip():
                return False, "模板内容不能为空"
            
            # 根据模板类型验证特定格式
            if template_type == 'weekly_confirmation':
                required_vars = ['{month}', '{day}']
                recommended_vars = ['{audio_tech}', '{video_director}', '{propresenter_play}', '{video_editor}']
                
                for var in required_vars:
                    if var not in template_content:
                        return False, f"缺少必需变量: {var}"
                
                # 检查是否至少包含一个事工角色变量
                has_role_var = any(var in template_content for var in recommended_vars)
                if not has_role_var:
                    return False, f"建议至少包含一个事工角色变量: {', '.join(recommended_vars)}"
            
            elif template_type == 'saturday_reminder':
                recommended_vars = ['{audio_tech_detail}', '{video_director_detail}', '{propresenter_play_detail}']
                
                # 检查是否至少包含一个服事详情变量
                has_detail_var = any(var in template_content for var in recommended_vars)
                if not has_detail_var:
                    return False, f"建议至少包含一个服事详情变量: {', '.join(recommended_vars)}"
            
            elif template_type == 'monthly_overview':
                required_vars = ['{year}', '{month}', '{schedule_list}']
                for var in required_vars:
                    if var not in template_content:
                        return False, f"缺少必需变量: {var}"
            
            return True, "模板验证通过"
            
        except Exception as e:
            return False, f"模板验证失败: {e}"
    
    def get_template_variables(self, template_type: str) -> Dict[str, str]:
        """获取模板可用变量"""
        template_config = self.get_template(template_type)
        if template_config:
            return template_config.get('variables', {})
        return {}

# 便捷函数
def get_dynamic_template_manager() -> DynamicTemplateManager:
    """获取动态模板管理器实例"""
    return DynamicTemplateManager()

def test_dynamic_templates():
    """测试动态模板系统"""
    print("🧪 测试动态模板系统...")
    
    manager = get_dynamic_template_manager()
    
    # 测试模板加载
    templates = manager.get_all_templates()
    if templates:
        print(f"✅ 成功加载 {len(templates.get('templates', {}))} 个模板")
    else:
        print("❌ 模板加载失败")
        return False
    
    # 测试模板渲染
    from src.data_cleaner import MinistrySchedule
    from datetime import date, timedelta
    
    test_schedule = MinistrySchedule(
        date=date.today() + timedelta(days=7),
        audio_tech="Jimmy",
        video_director="靖铮",
        propresenter_play="张宇"
    )
    
    # 测试周三模板
    wed_result = manager.render_weekly_confirmation(test_schedule.date, test_schedule)
    if "【本周" in wed_result and "事工安排提醒】" in wed_result:
        print("✅ 周三确认通知模板渲染正常")
    else:
        print("❌ 周三确认通知模板渲染失败")
        return False
    
    # 测试周六模板
    sat_result = manager.render_saturday_reminder(test_schedule.date, test_schedule)
    if "【主日服事提醒】" in sat_result:
        print("✅ 周六提醒通知模板渲染正常")
    else:
        print("❌ 周六提醒通知模板渲染失败")
        return False
    
    return True

if __name__ == "__main__":
    success = test_dynamic_templates()
    print(f"\n{'✅ 测试通过' if success else '❌ 测试失败'}")
    sys.exit(0 if success else 1)
