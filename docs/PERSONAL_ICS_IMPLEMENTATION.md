# 个人ICS订阅系统 - 实施指南

## 📚 文档概述

本文档详细说明了个人ICS订阅系统的实施步骤和修改内容。

## ✅ 已完成的工作

### 1. 核心代码文件

#### ✅ `src/personal_ics_manager.py` (新建)
**功能**：个人ICS日历管理核心类

**主要方法**：
- `extract_all_workers()` - 从事工安排中提取所有同工名单
- `filter_worker_assignments()` - 筛选特定同工的服事安排
- `generate_personal_ics()` - 为单个同工生成个人ICS文件
- `generate_all_personal_ics()` - 批量生成所有同工的个人ICS
- `get_ics_stats()` - 获取ICS文件统计信息
- `get_subscription_url()` - 获取订阅URL

**特色功能**：
- ✅ 视频剪辑角色特殊处理（靖铮专属）
  - 不显示彩排时间
  - 显示剪辑截止时间（周一晚8点）
  - 提前1天提醒
  
- ✅ 其他角色标准处理
  - 彩排事件（包含到场时间）
  - 正式服事事件
  - 提前60分钟/30分钟提醒

### 2. 示例文件

#### ✅ `calendars/personal/靖铮_grace_irvine_example.ics` (新建)
**内容**：靖铮的个人ICS文件示例

**包含事件**：
- 视频剪辑截止提醒（10月和11月共5次）
- 音控服事（11/09）包括彩排和正式服事

**特点**：
- 每个事件都有详细描述
- 包含完整的服事团队信息
- 设置了合理的提醒时间
- 符合ICS 2.0标准

### 3. 设计文档

#### ✅ `docs/PERSONAL_ICS_DESIGN.md` (新建)
**内容**：完整的系统设计方案

**包含章节**：
- 需求概述
- 核心功能设计
- 文件修改清单
- 工作流程图
- 数据结构定义
- 前端UI设计
- 实施步骤
- 安全考虑
- 后续优化方向

## 📋 待实施的修改

### 阶段一：增强现有代码（必须）

#### 1. 修改 `src/cloud_storage_manager.py`

```python
# 在 CloudStorageManager 类中添加以下方法

def upload_personal_ics(self, worker_name: str, ics_content: str) -> bool:
    """上传个人ICS文件到云存储
    
    Args:
        worker_name: 同工姓名
        ics_content: ICS文件内容
        
    Returns:
        是否上传成功
    """
    filename = f"{worker_name}_grace_irvine.ics"
    cloud_path = f"calendars/personal/{filename}"
    
    try:
        blob = self.bucket.blob(cloud_path)
        blob.upload_from_string(ics_content, content_type='text/calendar')
        blob.cache_control = 'no-cache'
        blob.patch()
        
        logger.info(f"✅ 已上传 {worker_name} 的个人ICS到云端：{cloud_path}")
        return True
    except Exception as e:
        logger.error(f"❌ 上传 {worker_name} 的个人ICS失败: {e}")
        return False

def list_personal_ics_files(self) -> List[Dict]:
    """列出所有个人ICS文件
    
    Returns:
        文件信息列表
    """
    try:
        blobs = self.bucket.list_blobs(prefix='calendars/personal/')
        files = []
        
        for blob in blobs:
            if blob.name.endswith('.ics'):
                # 提取同工姓名
                filename = Path(blob.name).name
                worker_name = filename.replace('_grace_irvine.ics', '')
                
                files.append({
                    'worker_name': worker_name,
                    'filename': filename,
                    'size': blob.size,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'url': blob.public_url
                })
        
        logger.info(f"📋 找到 {len(files)} 个个人ICS文件")
        return files
    except Exception as e:
        logger.error(f"❌ 列出个人ICS文件失败: {e}")
        return []

def get_personal_ics_url(self, worker_name: str) -> Optional[str]:
    """获取个人ICS的公开URL
    
    Args:
        worker_name: 同工姓名
        
    Returns:
        公开URL或None
    """
    filename = f"{worker_name}_grace_irvine.ics"
    cloud_path = f"calendars/personal/{filename}"
    
    try:
        blob = self.bucket.blob(cloud_path)
        if blob.exists():
            return blob.public_url
        else:
            logger.warning(f"⚠️ {worker_name} 的个人ICS文件不存在")
            return None
    except Exception as e:
        logger.error(f"❌ 获取 {worker_name} 的ICS URL失败: {e}")
        return None

def delete_personal_ics(self, worker_name: str) -> bool:
    """删除个人ICS文件
    
    Args:
        worker_name: 同工姓名
        
    Returns:
        是否删除成功
    """
    filename = f"{worker_name}_grace_irvine.ics"
    cloud_path = f"calendars/personal/{filename}"
    
    try:
        blob = self.bucket.blob(cloud_path)
        if blob.exists():
            blob.delete()
            logger.info(f"🗑️ 已删除 {worker_name} 的个人ICS")
            return True
        else:
            logger.warning(f"⚠️ {worker_name} 的个人ICS文件不存在")
            return False
    except Exception as e:
        logger.error(f"❌ 删除 {worker_name} 的个人ICS失败: {e}")
        return False
```

#### 2. 修改 `app_unified.py` - 自动更新逻辑

在 `automatic_ics_update()` 函数中添加个人ICS生成：

```python
async def automatic_ics_update():
    """自动更新ICS文件的核心函数"""
    try:
        # ... 现有步骤 1-3 ...
        
        # 4. 生成个人ICS文件（新增）
        logger.info("Step 4: Generating personal ICS files")
        from src.personal_ics_manager import PersonalICSManager
        
        personal_manager = PersonalICSManager()
        personal_files = personal_manager.generate_all_personal_ics(schedules)
        
        # 5. 上传个人ICS文件到云端（新增）
        logger.info("Step 5: Uploading personal ICS files to cloud storage")
        uploaded_count = 0
        
        for worker_name, file_path in personal_files.items():
            try:
                # 读取ICS文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    ics_content = f.read()
                
                # 上传到云端
                success = storage_manager.upload_personal_ics(worker_name, ics_content)
                if success:
                    uploaded_count += 1
            except Exception as e:
                logger.error(f"处理 {worker_name} 的ICS文件时出错: {e}")
        
        logger.info(f"✅ 已上传 {uploaded_count}/{len(personal_files)} 个个人ICS文件")
        
        return {
            "success": True,
            "message": "ICS calendars updated successfully",
            "personal_ics_generated": len(personal_files),
            "personal_ics_uploaded": uploaded_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Automatic ICS update failed: {e}")
        return {
            "success": False,
            "message": str(e)
        }
```

#### 3. 修改 `app_unified.py` - 添加前端页面

在 `main()` 函数中添加新页面：

```python
def main():
    """主应用入口"""
    # ... 现有代码 ...
    
    # 在侧边栏菜单中添加
    menu_options = [
        "📅 日历总览",
        "📋 事工安排管理",
        "📧 通知模板管理",
        "📨 发送通知",
        "⚙️ 提醒时间配置",
        "📅 ICS日历管理",
        "👥 个人日历管理",  # 新增
        "📊 系统状态",
        "🔧 云端配置"
    ]
    
    # ... 现有页面逻辑 ...
    
    elif selected_page == "👥 个人日历管理":
        show_personal_calendar_management()
```

添加个人日历管理页面函数：

```python
def show_personal_calendar_management():
    """显示个人日历管理页面"""
    st.title("👥 个人日历管理")
    st.markdown("为每个同工生成独立的可订阅ICS日历文件")
    
    # 按钮：生成所有个人ICS
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🔄 生成所有个人ICS", use_container_width=True):
            with st.spinner("正在生成个人ICS文件..."):
                try:
                    # 获取数据
                    cleaner = FocusedDataCleaner()
                    raw_df = cleaner.download_data()
                    focused_df = cleaner.extract_focused_columns(raw_df)
                    schedules = cleaner.clean_focused_data(focused_df)
                    
                    # 生成个人ICS
                    from src.personal_ics_manager import PersonalICSManager
                    manager = PersonalICSManager()
                    personal_files = manager.generate_all_personal_ics(schedules)
                    
                    # 上传到云端
                    from src.cloud_storage_manager import get_storage_manager
                    storage_manager = get_storage_manager()
                    
                    uploaded = 0
                    for worker_name, file_path in personal_files.items():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            ics_content = f.read()
                        if storage_manager.upload_personal_ics(worker_name, ics_content):
                            uploaded += 1
                    
                    st.success(f"✅ 成功生成并上传 {uploaded}/{len(personal_files)} 个个人ICS文件")
                except Exception as e:
                    st.error(f"❌ 生成失败: {e}")
    
    with col2:
        if st.button("📊 查看统计", use_container_width=True):
            st.session_state.show_stats = True
    
    with col3:
        st.button("🔄 刷新", use_container_width=True)
    
    st.divider()
    
    # 获取所有个人ICS文件列表
    try:
        from src.cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        personal_files = storage_manager.list_personal_ics_files()
        
        if not personal_files:
            st.info("📭 暂无个人ICS文件，请先点击"生成所有个人ICS"")
            return
        
        st.subheader(f"📋 同工列表 ({len(personal_files)})")
        
        # 显示统计信息
        if st.session_state.get('show_stats', False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("同工总数", len(personal_files))
            with col2:
                total_size = sum(f['size'] for f in personal_files)
                st.metric("总文件大小", f"{total_size / 1024:.2f} KB")
            with col3:
                if personal_files:
                    latest_update = max(f['updated'] for f in personal_files if f['updated'])
                    st.metric("最后更新", latest_update[:10])
        
        # 显示每个同工的ICS信息
        for file_info in sorted(personal_files, key=lambda x: x['worker_name']):
            with st.expander(f"👤 {file_info['worker_name']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **文件信息**
                    - 文件名：`{file_info['filename']}`
                    - 文件大小：{file_info['size'] / 1024:.2f} KB
                    - 更新时间：{file_info['updated'][:19] if file_info['updated'] else '未知'}
                    """)
                    
                    # 订阅链接
                    st.markdown("**📎 订阅链接**")
                    st.code(file_info['url'], language=None)
                    
                    if st.button(f"📋 复制链接", key=f"copy_{file_info['worker_name']}"):
                        st.toast("✅ 链接已复制到剪贴板")
                
                with col2:
                    st.markdown("**操作**")
                    if st.button("⬇️ 下载", key=f"download_{file_info['worker_name']}", use_container_width=True):
                        # 下载逻辑
                        st.toast("开始下载...")
                    
                    if st.button("🔄 重新生成", key=f"regen_{file_info['worker_name']}", use_container_width=True):
                        # 重新生成逻辑
                        st.toast("正在重新生成...")
    
    except Exception as e:
        st.error(f"❌ 获取个人ICS文件列表失败: {e}")
```

#### 4. 修改 `configs/reminder_settings.json`

添加个人日历提醒配置：

```json
{
  "version": "1.0",
  "last_updated": "2025-10-03T12:00:00",
  "description": "Grace Irvine Ministry Scheduler - 提醒时间配置",
  "reminder_configs": {
    "weekly_confirmation": {
      ...现有配置...
    },
    "saturday_reminder": {
      ...现有配置...
    },
    "monthly_overview": {
      ...现有配置...
    },
    "personal_calendar": {
      "event_type": "personal_calendar",
      "name": "个人日历提醒",
      "description": "同工个人服事日历的提醒设置",
      "reminders": {
        "rehearsal": {
          "minutes_before": 60,
          "description": "彩排提醒（提前1小时）"
        },
        "service": {
          "minutes_before": 30,
          "description": "服事提醒（提前30分钟）"
        },
        "video_editing": {
          "minutes_before": 1440,
          "description": "视频剪辑提醒（提前1天）"
        }
      },
      "enabled": true
    }
  }
}
```

### 阶段二：API端点（可选）

#### 添加API端点到 `app_unified.py`

```python
@api_app.get("/api/personal-ics/list")
async def list_personal_ics():
    """获取所有个人ICS文件列表"""
    try:
        from src.cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        files = storage_manager.list_personal_ics_files()
        
        return {
            "success": True,
            "count": len(files),
            "files": files
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@api_app.get("/api/personal-ics/{worker_name}")
async def get_personal_ics(worker_name: str):
    """获取特定同工的ICS文件URL"""
    try:
        from src.cloud_storage_manager import get_storage_manager
        storage_manager = get_storage_manager()
        url = storage_manager.get_personal_ics_url(worker_name)
        
        if url:
            return {
                "success": True,
                "worker_name": worker_name,
                "url": url
            }
        else:
            return {
                "success": False,
                "error": "ICS file not found"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@api_app.post("/api/personal-ics/generate")
async def generate_personal_ics(
    worker_name: Optional[str] = None,
    auth_token: str = Header(None, alias="X-Auth-Token")
):
    """生成个人ICS文件（所有或指定同工）"""
    # 验证token
    expected_token = os.getenv("API_AUTH_TOKEN")
    if expected_token and auth_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # 获取数据
        cleaner = FocusedDataCleaner()
        raw_df = cleaner.download_data()
        focused_df = cleaner.extract_focused_columns(raw_df)
        schedules = cleaner.clean_focused_data(focused_df)
        
        from src.personal_ics_manager import PersonalICSManager
        from src.cloud_storage_manager import get_storage_manager
        
        manager = PersonalICSManager()
        storage_manager = get_storage_manager()
        
        if worker_name:
            # 生成单个同工的ICS
            file_path = manager.generate_personal_ics(schedules, worker_name)
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    ics_content = f.read()
                success = storage_manager.upload_personal_ics(worker_name, ics_content)
                
                return {
                    "success": success,
                    "worker_name": worker_name,
                    "file_path": file_path
                }
            else:
                return {
                    "success": False,
                    "error": f"No assignments found for {worker_name}"
                }
        else:
            # 生成所有同工的ICS
            personal_files = manager.generate_all_personal_ics(schedules)
            uploaded = 0
            
            for worker, file_path in personal_files.items():
                with open(file_path, 'r', encoding='utf-8') as f:
                    ics_content = f.read()
                if storage_manager.upload_personal_ics(worker, ics_content):
                    uploaded += 1
            
            return {
                "success": True,
                "total": len(personal_files),
                "uploaded": uploaded,
                "workers": list(personal_files.keys())
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## 🧪 测试步骤

### 1. 单元测试

```bash
# 测试个人ICS管理器
cd /path/to/project
python -m src.personal_ics_manager
```

预期输出：
- 显示获取的事工安排数量
- 为靖铮生成个人日历
- 显示统计信息（文件大小、事件数、提醒数）
- 批量生成所有同工的日历

### 2. 集成测试

```bash
# 测试完整的自动更新流程
curl -X POST https://your-cloud-run-url/api/update-ics \
  -H "X-Auth-Token: your-auth-token"
```

检查：
- 是否成功生成所有个人ICS
- 是否上传到GCS bucket
- 日志中是否有错误

### 3. 前端测试

1. 启动Streamlit应用
2. 访问"个人日历管理"页面
3. 点击"生成所有个人ICS"
4. 检查是否显示所有同工
5. 展开靖铮的信息
6. 复制订阅链接并在日历应用中测试订阅

## 📝 部署清单

- [ ] 部署更新后的 `src/personal_ics_manager.py`
- [ ] 部署更新后的 `src/cloud_storage_manager.py`
- [ ] 部署更新后的 `app_unified.py`
- [ ] 更新 `configs/reminder_settings.json`
- [ ] 创建 `calendars/personal/` 目录
- [ ] 设置GCS bucket权限（允许公开读取 `calendars/personal/`）
- [ ] 测试Cloud Scheduler定时任务
- [ ] 更新文档和用户指南

## 🔗 相关文件

- **设计文档**: `docs/PERSONAL_ICS_DESIGN.md`
- **核心代码**: `src/personal_ics_manager.py`
- **示例文件**: `calendars/personal/靖铮_grace_irvine_example.ics`
- **配置文件**: `configs/reminder_settings.json`

## 📞 技术支持

如有问题，请参考：
1. 设计文档中的详细说明
2. 代码中的注释和文档字符串
3. 示例ICS文件的格式

---

**文档版本**: 1.0  
**创建日期**: 2025-10-03  
**最后更新**: 2025-10-03

