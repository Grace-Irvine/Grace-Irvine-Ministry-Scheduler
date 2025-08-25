# Grace Irvine Ministry Scheduler - 简化版设置指南

## 🚀 快速开始

这是一个简化版的实现，专门用于生成微信群通知的三个模板。

### 1. 环境准备

```bash
# 安装 Python 依赖
pip install -r simple_requirements.txt

# 复制环境变量文件
cp simple_env_example .env
```

### 2. Google Sheets API 设置

#### 步骤 1: 创建 Google Cloud 项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Google Sheets API

#### 步骤 2: 创建服务账号

1. 在 Google Cloud Console 中，转到 "IAM 和管理" > "服务账号"
2. 点击 "创建服务账号"
3. 填写服务账号详情，点击 "创建并继续"
4. 跳过权限设置，点击 "完成"

#### 步骤 3: 创建密钥

1. 点击刚创建的服务账号
2. 转到 "密钥" 标签页
3. 点击 "添加密钥" > "创建新密钥"
4. 选择 "JSON" 格式
5. 下载 JSON 文件并重命名为 `service_account.json`
6. 将文件放在 `configs/` 目录下

#### 步骤 4: 共享 Google Sheets

1. 打开您的 Google Sheets 文档
2. 点击右上角的 "共享" 按钮
3. 添加服务账号的邮箱地址（在 JSON 文件中的 `client_email` 字段）
4. 设置权限为 "查看者"
5. 取消 "通知用户" 选项，点击 "共享"

### 3. 配置设置

#### 获取 Spreadsheet ID

从您的 Google Sheets URL 中复制 Spreadsheet ID：

```
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        这部分就是 Spreadsheet ID
```

#### 更新 .env 文件

```env
GOOGLE_SPREADSHEET_ID=你的_Spreadsheet_ID
```

### 4. 表格格式要求

确保您的 Google Sheets 有以下列结构：

| A列 | B列 | C列 | D列 | E列 |
|-----|-----|-----|-----|-----|
| 日期 | 音控 | 屏幕 | 摄像/导播 | Propresenter制作 |
| 2024/1/14 | 张三 | 李四 | 王五 | 赵六 |
| 2024/1/21 | ... | ... | ... | ... |

**注意事项：**
- 第一行为标题行，会被跳过
- 日期格式支持：2024/1/14、2024-01-14 等
- 如果某个角色没有安排，可以留空或填写 "-"

### 5. 运行程序

```bash
# 确保在项目根目录
python simple_scheduler.py
```

### 6. 输出示例

程序会生成三个模板的通知内容：

#### 模板1 - 周三确认通知
```
【本周1月14日主日事工安排提醒】🕊️

• 音控：张三
• 屏幕：李四
• 摄像/导播：王五
• Propresenter 制作：赵六
• 视频剪辑：靖铮

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏
```

#### 模板2 - 周六提醒通知
```
【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  
- 音控：张三 9:00到，随敬拜团排练
- 屏幕：李四 9:00到，随敬拜团排练
- 摄像/导播: 王五 9:30到，检查预设机位

愿主同在，出入平安。若临时不适请第一时间私信我。🙌
```

#### 模板3 - 月度总览通知
```
【2024年01月}事工排班一览】📅
请各位同工先行预留时间，如有冲突尽快与我沟通：
https://docs.google.com/spreadsheets/d/your_sheet_id

当月安排预览：
• 1/7: 音控:张三, 屏幕:李四, 摄像:王五
• 1/14: 音控:赵六, 屏幕:钱七, 摄像:孙八
• 1/21: 音控:周九, 屏幕:吴十, 摄像:郑一
• 1/28: 音控:王二, 屏幕:赵三, 摄像:钱四

温馨提示：
- 周三晚发布当周安排（确认/调换）
- 周六晚发布主日提醒（到场时间）
感谢大家同心配搭！🙏
```

## 🔧 自定义调整

### 修改列映射

如果您的表格结构不同，可以在 `simple_scheduler.py` 中修改 `parse_ministry_data` 方法：

```python
assignment = MinistryAssignment(
    date=parsed_date,
    audio_tech=self._clean_name(row[1]),        # 修改这里的索引
    screen_operator=self._clean_name(row[2]),   # 对应您的列位置
    camera_operator=self._clean_name(row[3]),   
    propresenter=self._clean_name(row[4]),      
    video_editor="靖铮"
)
```

### 修改模板内容

在 `NotificationGenerator` 类中修改对应的模板方法：

- `generate_weekly_confirmation()` - 周三通知
- `generate_sunday_reminder()` - 周六通知  
- `generate_monthly_overview()` - 月度通知

## 🐛 故障排除

### 常见错误

1. **认证失败**
   - 检查 `configs/service_account.json` 文件是否存在
   - 确认服务账号邮箱已添加到 Google Sheets 共享列表

2. **找不到工作表**
   - 确认工作表名称是否正确（默认为 "总表"）
   - 检查 Spreadsheet ID 是否正确

3. **日期解析失败**
   - 确认日期格式（支持 2024/1/14、2024-01-14 等）
   - 检查日期列是否有空值

4. **没有数据**
   - 确认表格不为空
   - 检查是否有标题行

### 调试模式

在代码开头添加详细日志：

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📞 获取帮助

如有问题，请检查：
1. Python 版本 (推荐 3.8+)
2. 网络连接
3. Google Cloud API 配额
4. 服务账号权限

---

*愿神祝福我们的事工！*
