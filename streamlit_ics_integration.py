#!/usr/bin/env python3
"""
Streamlit + ICS集成方案
在现有Streamlit应用基础上添加ICS文件服务功能

部署到Cloud Run后：
1. Streamlit Web界面正常工作
2. 提供/calendars/路径下的ICS文件访问
3. Cloud Scheduler可以调用API更新ICS文件
"""

import streamlit as st
import os
import sys
from pathlib import Path

# 检查是否为特殊路径请求
if hasattr(st, 'experimental_get_query_params'):
    query_params = st.experimental_get_query_params()
else:
    query_params = st.query_params

# 获取URL路径
try:
    # 在Cloud Run中，可以通过这种方式获取路径
    request_path = os.environ.get('REQUEST_URI', '')
    if not request_path:
        # 本地开发时的备用方法
        request_path = '/'
except:
    request_path = '/'

# 处理ICS文件请求
if '/calendars/' in request_path and request_path.endswith('.ics'):
    try:
        # 设置正确的响应头
        st.set_page_config(page_title="ICS Calendar", layout="centered")
        
        # 根据请求的文件名决定生成哪种日历
        if 'coordinator' in request_path:
            st.markdown("## 📅 负责人日历")
            calendar_type = 'coordinator'
        elif 'workers' in request_path:
            st.markdown("## 👥 同工日历") 
            calendar_type = 'workers'
        else:
            st.error("❌ 未知的日历类型")
            st.stop()
        
        # 生成ICS内容
        with st.spinner("正在生成日历文件..."):
            try:
                sys.path.append(str(Path(__file__).parent))
                from src.scheduler import GoogleSheetsExtractor
                from src.template_manager import get_default_template_manager
                
                spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
                extractor = GoogleSheetsExtractor(spreadsheet_id)
                assignments = extractor.parse_ministry_data()
                template_manager = get_default_template_manager()
                
                if calendar_type == 'coordinator':
                    ics_content = generate_coordinator_ics_simple(assignments, template_manager)
                    filename = 'grace_irvine_coordinator.ics'
                else:
                    ics_content = generate_workers_ics_simple(assignments)
                    filename = 'grace_irvine_workers.ics'
                
                if ics_content:
                    # 提供下载
                    st.download_button(
                        label=f"📥 下载{calendar_type}日历",
                        data=ics_content,
                        file_name=filename,
                        mime="text/calendar",
                        use_container_width=True
                    )
                    
                    # 显示预览
                    event_count = ics_content.count('BEGIN:VEVENT')
                    st.success(f"✅ 日历生成成功！包含 {event_count} 个事件")
                    
                    with st.expander("📋 日历内容预览"):
                        st.text(ics_content[:1000] + "..." if len(ics_content) > 1000 else ics_content)
                else:
                    st.error("❌ 生成日历失败")
                
            except Exception as e:
                st.error(f"❌ 生成日历时出错: {e}")
        
        st.stop()
        
    except Exception as e:
        st.error(f"❌ 处理ICS请求失败: {e}")
        st.stop()

# 处理API更新请求
elif '/api/update-calendars' in request_path:
    st.set_page_config(page_title="API Response", layout="centered")
    st.markdown("## 🔄 ICS日历更新API")
    
    try:
        with st.spinner("正在更新ICS日历..."):
            sys.path.append(str(Path(__file__).parent))
            from src.scheduler import GoogleSheetsExtractor
            from src.template_manager import get_default_template_manager
            
            spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
            extractor = GoogleSheetsExtractor(spreadsheet_id)
            assignments = extractor.parse_ministry_data()
            template_manager = get_default_template_manager()
            
            # 生成ICS文件
            coordinator_ics = generate_coordinator_ics_simple(assignments, template_manager)
            workers_ics = generate_workers_ics_simple(assignments)
            
            # 保存到临时目录（Cloud Run中）
            calendar_dir = Path('/tmp/calendars')
            calendar_dir.mkdir(exist_ok=True)
            
            files_updated = []
            
            if coordinator_ics:
                with open(calendar_dir / 'grace_irvine_coordinator.ics', 'w', encoding='utf-8') as f:
                    f.write(coordinator_ics)
                files_updated.append(f"负责人日历 ({coordinator_ics.count('BEGIN:VEVENT')} 事件)")
            
            if workers_ics:
                with open(calendar_dir / 'grace_irvine_workers.ics', 'w', encoding='utf-8') as f:
                    f.write(workers_ics)
                files_updated.append(f"同工日历 ({workers_ics.count('BEGIN:VEVENT')} 事件)")
            
            # 显示结果
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'files_updated': files_updated,
                'assignments_processed': len(assignments)
            }
            
            st.success("✅ ICS日历更新成功！")
            st.json(result)
    
    except Exception as e:
        st.error(f"❌ 更新失败: {e}")
        st.json({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })
    
    st.stop()

def generate_coordinator_ics_simple(assignments, template_manager) -> str:
    """简化版负责人日历生成"""
    try:
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Coordinator Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 事工协调日历",
            "X-WR-CALDESC:事工通知发送提醒日历",
            "X-WR-TIMEZONE:America/Los_Angeles"
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:10]
        
        for assignment in future_assignments:
            # 周三确认通知
            wednesday = assignment.date - timedelta(days=4)
            if wednesday >= today - timedelta(days=7):
                try:
                    content = template_manager.render_weekly_confirmation(assignment)
                    event_ics = create_ics_event(
                        uid=f"weekly_{wednesday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送周末确认通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{content}",
                        start_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20)),
                        end_dt=datetime.combine(wednesday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                except:
                    pass
            
            # 周六提醒通知
            saturday = assignment.date - timedelta(days=1)
            if saturday >= today - timedelta(days=7):
                try:
                    content = template_manager.render_sunday_reminder(assignment)
                    event_ics = create_ics_event(
                        uid=f"sunday_{saturday.strftime('%Y%m%d')}@graceirvine.org",
                        summary=f"发送主日提醒通知 ({assignment.date.month}/{assignment.date.day})",
                        description=f"发送内容：\n\n{content}",
                        start_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20)),
                        end_dt=datetime.combine(saturday, datetime.min.time().replace(hour=20, minute=30)),
                        location="Grace Irvine 教会"
                    )
                    ics_lines.append(event_ics)
                except:
                    pass
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
        
    except Exception as e:
        logger.error(f"生成负责人日历失败: {e}")
        return None

def generate_workers_ics_simple(assignments) -> str:
    """简化版同工日历生成"""
    try:
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Grace Irvine Ministry Scheduler//Workers Calendar//CN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Grace Irvine 同工服事日历",
            "X-WR-CALDESC:同工事工服事安排日历",
            "X-WR-TIMEZONE:America/Los_Angeles"
        ]
        
        today = date.today()
        future_assignments = [a for a in assignments if a.date >= today][:8]
        
        for assignment in future_assignments:
            roles = [
                ("音控", assignment.audio_tech, "09:00"),
                ("导播/摄影", assignment.camera_operator, "09:30"),
                ("ProPresenter播放", assignment.propresenter, "09:00")
            ]
            
            for role_name, person_name, start_time in roles:
                if person_name and person_name.strip():
                    try:
                        start_hour, start_minute = map(int, start_time.split(':'))
                        event_ics = create_ics_event(
                            uid=f"service_{role_name}_{assignment.date.strftime('%Y%m%d')}@graceirvine.org",
                            summary=f"主日服事 - {role_name}",
                            description=f"角色：{role_name}\n负责人：{person_name}\n到场时间：{start_time}",
                            start_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=start_hour, minute=start_minute)),
                            end_dt=datetime.combine(assignment.date, datetime.min.time().replace(hour=12)),
                            location="Grace Irvine 教会"
                        )
                        ics_lines.append(event_ics)
                    except:
                        pass
        
        ics_lines.append("END:VCALENDAR")
        return "\n".join(ics_lines)
        
    except Exception as e:
        logger.error(f"生成同工日历失败: {e}")
        return None

# 如果不是特殊路径，运行正常的Streamlit应用
exec(open('streamlit_app.py').read())
