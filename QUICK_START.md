# 快速开始 - 微信群通知生成器

## 🎯 核心功能

根据 Google Sheets 中的事工安排数据，自动生成三种微信群通知：

1. **周三确认通知** - 提醒本周安排，允许调换
2. **周六提醒通知** - 最终确认，包含到场时间
3. **月度总览通知** - 整月安排一览，含表格链接

## ⚡ 5分钟快速配置

### 步骤 1: 准备 Google Sheets

确保您的表格格式如下：

| A列（日期） | B列（音控） | C列（屏幕） | D列（摄像/导播） | E列（Propresenter制作） |
|------------|------------|------------|---------------|-------------------|
| 2024/1/14  | 张三       | 李四       | 王五          | 赵六              |
| 2024/1/21  | 钱七       | 孙八       | 周九          | 吴十              |

### 步骤 2: 设置 Google API

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目并启用 Google Sheets API
3. 创建服务账号，下载 JSON 密钥
4. 将密钥重命名为 `service_account.json`，放在 `configs/` 目录

### 步骤 3: 配置环境

```bash
# 复制环境变量文件
cp simple_env_example .env

# 编辑 .env 文件，添加您的 Spreadsheet ID
nano .env
```

在 `.env` 文件中设置：
```
GOOGLE_SPREADSHEET_ID=您的表格ID
```

### 步骤 4: 运行程序

**Windows 用户：**
```
双击运行 run_notifications.bat
```

**macOS/Linux 用户：**
```bash
./run_notifications.sh
```

**或者直接使用 Python：**
```bash
# 安装依赖
pip install -r simple_requirements.txt

# 验证数据
python check_data.py

# 生成通知
python generate_notifications.py weekly   # 周三通知
python generate_notifications.py sunday   # 周六通知
python generate_notifications.py monthly  # 月度通知
python generate_notifications.py all      # 所有通知
```

## 📱 生成的通知示例

### 周三确认通知
```
【本周1月14日主日事工安排提醒】🕊️

• 音控：张三
• 屏幕：李四
• 摄像/导播：王五
• Propresenter 制作：赵六
• 视频剪辑：靖铮

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏
```

### 周六提醒通知
```
【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜  
请各位同工提前到场：  
- 音控：张三 9:00到，随敬拜团排练
- 屏幕：李四 9:00到，随敬拜团排练
- 摄像/导播: 王五 9:30到，检查预设机位

愿主同在，出入平安。若临时不适请第一时间私信我。🙌
```

### 月度总览通知
```
【2024年01月事工排班一览】📅
请各位同工先行预留时间，如有冲突尽快与我沟通：
https://docs.google.com/spreadsheets/d/您的表格ID

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

### 修改表格列位置

如果您的表格列位置不同，编辑 `simple_scheduler.py` 中的这部分：

```python
assignment = MinistryAssignment(
    date=parsed_date,
    audio_tech=self._clean_name(row[1]),        # B列 - 音控
    screen_operator=self._clean_name(row[2]),   # C列 - 屏幕
    camera_operator=self._clean_name(row[3]),   # D列 - 摄像/导播
    propresenter=self._clean_name(row[4]),      # E列 - Propresenter制作
    video_editor="靖铮"  # 固定值
)
```

### 修改通知内容

在 `NotificationGenerator` 类中修改对应的方法：
- `generate_weekly_confirmation()` - 周三通知
- `generate_sunday_reminder()` - 周六通知
- `generate_monthly_overview()` - 月度通知

## ✅ 验证清单

运行 `python check_data.py` 检查：

- [x] Google Sheets 连接成功
- [x] 数据格式正确
- [x] 日期能正确解析
- [x] 人员信息完整
- [x] 至少有一条有效安排

## 🚀 定时自动化（可选）

### Windows 任务计划

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器：
   - 周三 20:00 运行 `python generate_notifications.py weekly`
   - 周六 20:00 运行 `python generate_notifications.py sunday`
   - 每月1日 09:00 运行 `python generate_notifications.py monthly`

### macOS/Linux Cron

```bash
# 编辑 crontab
crontab -e

# 添加任务（调整路径）
0 20 * * 3 cd /path/to/project && python generate_notifications.py weekly
0 20 * * 6 cd /path/to/project && python generate_notifications.py sunday
0 9 1 * * cd /path/to/project && python generate_notifications.py monthly
```

## 🆘 常见问题

### 认证失败
- 确保 `configs/service_account.json` 存在
- 确认服务账号邮箱已添加到 Google Sheets 共享

### 数据为空
- 检查 Spreadsheet ID 是否正确
- 确认工作表名称（默认为"总表"）
- 验证日期格式

### 日期解析错误
- 支持格式：2024/1/14、2024-01-14
- 确保日期列（A列）不为空

## 📞 获取帮助

如遇问题：
1. 运行 `python check_data.py` 进行诊断
2. 查看详细的错误信息
3. 检查网络连接和 API 配额

---

**愿神祝福我们的服事！** 🙏
