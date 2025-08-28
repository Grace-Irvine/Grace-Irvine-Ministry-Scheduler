# 邮件模板调试指南

## 问题描述
部署的scheduler可以发送邮件，但是邮件内容是空的。

## 问题原因
1. **模板路径问题**: `email_sender.py` 中的模板路径使用了相对路径 `Path(__file__).parent.parent`，在云函数环境中无法正确定位模板目录。
2. **导入问题**: cloud_functions目录中存在的占位符文件导致相对导入失败。

## 解决方案

### 1. 修复模板路径
更新 `src/email_sender.py` 中的 `_setup_template_engine` 方法，支持多种可能的模板位置：

```python
def _setup_template_engine(self):
    """设置Jinja2模板引擎"""
    # Try multiple possible template locations
    possible_dirs = [
        Path(__file__).parent.parent / "templates" / "email",  # Local development
        Path(__file__).parent / "templates" / "email",  # Cloud function deployment
        Path("templates") / "email",  # Current directory
        Path("/workspace/templates/email"),  # Cloud Run
    ]
    
    template_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            template_dir = dir_path
            logger.info(f"Found template directory at: {template_dir}")
            break
```

### 2. 修复导入问题
- 删除 `cloud_functions/email_sender.py` 和 `cloud_functions/scheduler.py` 占位符文件
- 更新 `src/scheduler.py` 中的相对导入，添加异常处理：

```python
try:
    from .template_manager import get_default_template_manager
except ImportError:
    # For cloud functions deployment
    from template_manager import get_default_template_manager
```

### 3. 确保模板文件被正确部署
在 `deploy_to_gcp.sh` 中确保复制模板文件：

```bash
# 复制模板文件
cp -r templates cloud_functions_deploy/
```

## 测试验证

### 1. 本地测试
```bash
python3 test_email_generation.py
```

### 2. 部署后测试
```bash
# 测试周三确认通知
curl -X POST https://send-weekly-confirmation-wu7uk5rgdq-uc.a.run.app

# 测试周六提醒通知  
curl -X POST https://send-sunday-reminder-wu7uk5rgdq-uc.a.run.app
```

### 3. 查看日志
```bash
# 查看函数日志
gcloud functions logs read send-weekly-confirmation --region=us-central1 --limit=20

# 检查模板加载
gcloud functions logs read send-weekly-confirmation --region=us-central1 | grep "template"
```

## 验证成功标志
1. 日志中显示：`Found template directory at: /workspace/templates/email`
2. 邮件发送成功且包含正确的HTML内容
3. WeChat消息模板正确渲染

## 预防措施
1. 在部署前本地测试所有功能
2. 确保所有必需文件都包含在部署包中
3. 使用绝对导入而非相对导入在云函数中
4. 添加详细的日志记录以便调试
