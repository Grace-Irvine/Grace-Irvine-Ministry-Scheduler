#!/usr/bin/env python3
"""
Streamlit Cloud Configuration
云环境专用配置模块
"""

import os
import logging
from pathlib import Path
from google.cloud import secretmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_cloud_environment():
    """设置云环境配置"""
    
    # 检查是否在云环境中运行
    if is_cloud_environment():
        logger.info("检测到云环境，加载 Secret Manager 配置")
        load_secrets_from_gcp()
    else:
        logger.info("本地环境，使用 .env 文件配置")
        load_local_env()

def is_cloud_environment():
    """检查是否在云环境中运行"""
    # 检查 Cloud Run 环境变量
    return (
        os.getenv('K_SERVICE') is not None or  # Cloud Run
        os.getenv('GAE_APPLICATION') is not None or  # App Engine
        os.getenv('FUNCTION_NAME') is not None  # Cloud Functions
    )

def load_secrets_from_gcp():
    """从 Google Cloud Secret Manager 加载配置"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = "ai-for-god"
        
        secrets = {
            'GOOGLE_SPREADSHEET_ID': 'google-spreadsheet-id',
            'SENDER_EMAIL': 'sender-email',
            'SENDER_NAME': 'sender-name',
            'EMAIL_PASSWORD': 'email-password',
            'RECIPIENT_EMAILS': 'recipient-emails'
        }
        
        for env_var, secret_name in secrets.items():
            try:
                name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                secret_value = response.payload.data.decode("UTF-8")
                os.environ[env_var] = secret_value
                logger.info(f"成功加载密钥: {secret_name}")
            except Exception as e:
                logger.error(f"加载密钥 {secret_name} 失败: {e}")
        
        # 设置服务账号认证
        setup_service_account_auth(client, project_id)
        
    except Exception as e:
        logger.error(f"加载 GCP 密钥失败: {e}")
        # 回退到环境变量
        logger.info("回退到环境变量配置")

def setup_service_account_auth(client, project_id):
    """设置服务账号认证"""
    try:
        # 从 Secret Manager 获取服务账号密钥
        name = f"projects/{project_id}/secrets/google-service-account-key/versions/latest"
        response = client.access_secret_version(request={"name": name})
        service_account_key = response.payload.data.decode("UTF-8")
        
        # 写入临时文件
        import tempfile
        temp_dir = tempfile.mkdtemp()
        service_account_path = os.path.join(temp_dir, 'service_account.json')
        
        with open(service_account_path, 'w') as f:
            f.write(service_account_key)
        
        # 设置环境变量
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
        logger.info("服务账号认证配置完成")
        
    except Exception as e:
        logger.error(f"服务账号认证配置失败: {e}")

def load_local_env():
    """加载本地环境变量"""
    try:
        from dotenv import load_dotenv
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info("本地 .env 文件加载完成")
        else:
            logger.warning(".env 文件不存在")
    except ImportError:
        logger.warning("python-dotenv 未安装，跳过 .env 文件加载")
    except Exception as e:
        logger.error(f"加载本地环境变量失败: {e}")

def get_cloud_run_info():
    """获取 Cloud Run 部署信息"""
    info = {}
    
    # Cloud Run 环境变量
    cloud_run_vars = [
        'K_SERVICE',        # 服务名称
        'K_REVISION',       # 修订版本
        'K_CONFIGURATION',  # 配置名称
        'PORT',             # 端口
        'GOOGLE_CLOUD_PROJECT'  # 项目ID
    ]
    
    for var in cloud_run_vars:
        value = os.getenv(var)
        if value:
            info[var] = value
    
    return info

# 在模块导入时自动设置环境
setup_cloud_environment()
