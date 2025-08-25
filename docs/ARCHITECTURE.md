# Grace Irvine Ministry Scheduler - 项目架构设计

## 🎯 核心目标

1. **自动化数据提取**: 从 Google Sheets 提取事工排班数据
2. **智能通知生成**: 自动生成规范化通知文案
3. **多渠道分发**: 通过邮件/短信发送给通知负责人
4. **日历同步**: 生成可订阅的 .ics 日历文件（含提醒）

## 🏗️ 系统架构

### 整体架构图
系统采用模块化设计，主要包含数据层、核心服务层、通知渠道层和输出层。

### 核心组件

#### 1. 数据层 (Data Layer)
- **Google Sheets API**: 数据源接口
- **SQLite Database**: 本地数据缓存和历史记录
- **Configuration Files**: 系统配置和模板定义

#### 2. 核心服务层 (Core Services)
- **Data Extractor**: 数据提取服务
- **Template Engine**: 模板渲染引擎
- **Scheduler Service**: 定时任务调度器
- **Calendar Generator**: 日历文件生成器

#### 3. 通知渠道层 (Notification Channels)
- **Email Service**: 邮件发送服务 (SMTP/SendGrid)
- **SMS Service**: 短信发送服务 (Twilio/AWS SNS)

#### 4. 输出层 (Output)
- **.ics Calendar Files**: 日历文件
- **Calendar Subscription URLs**: 订阅链接
- **Logs & Analytics**: 日志和分析数据

## 🔄 业务流程

### 主要业务流程

1. **数据提取流程**
   ```
   Google Sheets → API读取 → 数据清洗 → 存储到本地数据库
   ```

2. **通知生成流程**
   ```
   定时触发 → 查询数据库 → 模板渲染 → 多渠道发送
   ```

3. **日历生成流程**
   ```
   数据变更 → 触发生成 → 创建.ics文件 → 更新订阅URL
   ```

### 通知时间表

| 通知类型 | 发送时间 | 内容描述 | 目标受众 |
|---------|---------|---------|---------|
| **周三确认** | 周三 20:00 | 当周事工安排（供确认/调换） | 通知负责人 |
| **主日提醒** | 周六 20:00 | 主日服事提醒（最终确认/到场时间） | 通知负责人 |
| **月度总览** | 每月1日 09:00 | 当月排班一览（长表） | 通知负责人 |

## 📊 数据模型

### 核心数据结构

```python
@dataclass
class MinistrySchedule:
    date: datetime
    time: str
    location: str
    role: str
    person: str
    notes: str
    created_at: datetime
    updated_at: datetime

@dataclass
class NotificationTemplate:
    template_id: str
    name: str
    trigger_type: str  # weekly_wed, weekly_sat, monthly
    subject_template: str
    body_template: str
    recipients: List[str]

@dataclass
class NotificationLog:
    log_id: str
    template_id: str
    sent_at: datetime
    status: str  # success, failed, retrying
    channel: str  # email, sms
    recipient: str
    error_message: Optional[str]
```

## 🛠️ 技术栈

### 后端技术
- **Python 3.11+**: 主要开发语言
- **FastAPI**: Web框架和API服务
- **SQLite**: 轻量级数据库
- **SQLAlchemy**: ORM框架
- **Celery + Redis**: 异步任务队列
- **APScheduler**: 定时任务调度

### 数据处理
- **Google Sheets API**: 数据源集成
- **Pandas**: 数据处理和清洗
- **Jinja2**: 模板引擎
- **iCalendar (icalendar)**: 日历文件生成

### 通知服务
- **SendGrid**: 邮件发送服务
- **Twilio**: 短信发送服务
- **SMTP**: 备用邮件发送

### 部署和运维
- **Docker**: 容器化部署
- **Docker Compose**: 本地开发环境
- **Google Cloud Run**: 云端部署
- **GitHub Actions**: CI/CD流水线

## 📁 项目结构

```
Grace-Irvine-Ministry-Scheduler/
├── app/                          # 应用主目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── api/                      # API路由
│   │   ├── __init__.py
│   │   ├── schedules.py          # 排班相关API
│   │   ├── notifications.py     # 通知相关API
│   │   └── calendars.py          # 日历相关API
│   ├── core/                     # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── database.py           # 数据库连接
│   │   └── security.py           # 安全认证
│   ├── services/                 # 业务服务
│   │   ├── __init__.py
│   │   ├── data_extractor.py     # 数据提取服务
│   │   ├── template_engine.py    # 模板引擎
│   │   ├── notification_service.py # 通知服务
│   │   ├── calendar_service.py   # 日历服务
│   │   └── scheduler_service.py  # 调度服务
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── schedule.py           # 排班模型
│   │   ├── notification.py       # 通知模型
│   │   └── calendar.py           # 日历模型
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── google_sheets.py      # Google Sheets客户端
│       ├── email_client.py       # 邮件客户端
│       ├── sms_client.py         # 短信客户端
│       └── validators.py         # 数据验证
├── templates/                    # 通知模板
│   ├── email/
│   │   ├── weekly_confirmation.html
│   │   ├── sunday_reminder.html
│   │   └── monthly_overview.html
│   └── sms/
│       ├── weekly_confirmation.txt
│       ├── sunday_reminder.txt
│       └── monthly_overview.txt
├── configs/                      # 配置文件
│   ├── settings.yaml             # 主配置文件
│   ├── notification_templates.yaml # 通知模板配置
│   └── service_account.json      # Google服务账号密钥
├── data/                         # 数据目录
│   ├── database.db               # SQLite数据库
│   └── calendars/                # 生成的日历文件
│       └── ministry_schedule.ics
├── scripts/                      # 脚本工具
│   ├── setup_database.py         # 数据库初始化
│   ├── test_notifications.py     # 通知测试
│   └── migrate_data.py           # 数据迁移
├── tests/                        # 测试文件
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── test_utils/
├── deployment/                   # 部署配置
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── deploy.sh
├── docs/                         # 文档
│   ├── API.md                    # API文档
│   ├── DEPLOYMENT.md             # 部署指南
│   └── USER_GUIDE.md             # 用户指南
├── .env.example                  # 环境变量示例
├── .gitignore
├── README.md
└── ARCHITECTURE.md               # 本文档
```

## 🔧 核心功能详解

### 1. 数据提取服务 (Data Extractor)

**功能**: 从Google Sheets按日期范围提取排班数据

**关键特性**:
- 支持多种日期格式解析
- 自动数据清洗和验证
- 增量更新机制
- 错误处理和重试机制

**实现要点**:
```python
class DataExtractor:
    def extract_schedule_data(self, date_range: DateRange) -> List[MinistrySchedule]:
        # 1. 连接Google Sheets API
        # 2. 根据日期范围筛选数据
        # 3. 数据清洗和标准化
        # 4. 返回结构化数据
```

### 2. 模板引擎 (Template Engine)

**功能**: 将数据渲染为规范化通知文案

**支持的模板类型**:
- **周三确认通知**: 当周事工安排，支持确认和调换
- **周六提醒通知**: 主日服事最终确认
- **月度总览通知**: 当月完整排班表

**模板特性**:
- 支持HTML和纯文本格式
- 动态数据绑定
- 条件渲染
- 多语言支持

### 3. 通知分发服务 (Notification Service)

**支持的通道**:
- **邮件**: SMTP、SendGrid
- **短信**: Twilio、AWS SNS

**关键功能**:
- 批量发送
- 发送状态追踪
- 失败重试机制
- 发送限流控制

### 4. 日历生成器 (Calendar Generator)

**功能**: 生成包含提醒的.ics日历文件

**特性**:
- 符合iCalendar标准
- 支持VALARM提醒设置
- 自动更新机制
- 订阅URL生成

**日历特性**:
- 事件标题、描述、时间、地点
- 多级提醒设置（30分钟前、1天前）
- 重复事件支持
- 时区处理

## 🚀 部署策略

### 开发环境
```bash
# 使用Docker Compose快速启动
docker-compose up -d

# 或本地开发
pip install -r requirements.txt
python app/main.py
```

### 生产环境部署选项

#### 选项1: Google Cloud Run (推荐)
- **优势**: 自动扩缩容、按需付费
- **适用**: 中小型教会，访问量不大
- **成本**: 低成本运营

#### 选项2: VPS部署
- **优势**: 完全控制、固定成本
- **适用**: 有技术团队的教会
- **工具**: Docker + Nginx + Let's Encrypt

#### 选项3: 本地部署
- **优势**: 数据完全本地化
- **适用**: 对数据安全要求极高的场景
- **要求**: 需要稳定的网络和硬件

## 📈 监控和维护

### 关键监控指标
- 数据提取成功率
- 通知发送成功率
- API响应时间
- 系统资源使用情况

### 日志管理
- 结构化日志记录
- 错误追踪和告警
- 性能分析
- 审计日志

### 备份策略
- 数据库定期备份
- 配置文件版本控制
- 日历文件备份
- 灾难恢复计划

## 🔒 安全考虑

### 数据安全
- Google API密钥安全存储
- 数据库加密
- 敏感信息脱敏
- 访问权限控制

### 通信安全
- HTTPS/TLS加密
- API认证和授权
- 请求限流
- 输入验证

## 🎯 实施路线图

### Phase 1: 核心功能 (4-6周)
- [ ] Google Sheets数据提取
- [ ] 基础模板引擎
- [ ] 邮件通知功能
- [ ] 简单的.ics生成

### Phase 2: 增强功能 (3-4周)
- [ ] 短信通知功能
- [ ] 高级模板功能
- [ ] 日历订阅URL
- [ ] Web管理界面

### Phase 3: 生产就绪 (2-3周)
- [ ] 监控和日志
- [ ] 错误处理优化
- [ ] 性能优化
- [ ] 部署自动化

### Phase 4: 高级功能 (按需)
- [ ] 多教会支持
- [ ] 移动应用集成
- [ ] 高级分析功能
- [ ] AI智能调度建议

## 💡 扩展计划

### 未来可能的功能
- **智能冲突检测**: 自动检测排班冲突
- **移动端应用**: 原生移动应用
- **微信集成**: 直接发送到微信群
- **数据分析**: 服事参与度分析
- **多语言支持**: 英文、中文界面切换

这个架构设计为Grace Irvine Ministry Scheduler提供了一个完整、可扩展的解决方案，既满足了当前的需求，也为未来的功能扩展留下了空间。
