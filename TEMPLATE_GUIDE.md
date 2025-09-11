# 📝 动态模板系统使用指南

## 🎯 概述

Grace Irvine Ministry Scheduler 现在支持完全可编辑的动态模板系统，解决了以下问题：
- ✅ **灵活编辑**: 模板存储在JSON文件中，可随时修改
- ✅ **云端存储**: 支持GCP Storage，部署后仍可编辑
- ✅ **细化变量**: 每个事工角色都是独立变量，支持自定义格式
- ✅ **实时预览**: Web界面支持实时预览模板效果

## 📋 可用的模板变量

### 周三确认通知模板

| 变量名 | 描述 | 示例值 |
|--------|------|---------|
| `{month}` | 月份 | `9` |
| `{day}` | 日期 | `14` |
| `{audio_tech}` | 音控人员 | `Jimmy` |
| `{video_director}` | 导播/摄影人员 | `靖铮` |
| `{propresenter_play}` | ProPresenter播放人员 | `张宇` |
| `{propresenter_update}` | ProPresenter更新人员 | `Daniel` |
| `{video_editor}` | 视频剪辑人员 | `靖铮` |

### 周六提醒通知模板

| 变量名 | 描述 | 示例值 |
|--------|------|---------|
| `{audio_tech_detail}` | 音控详细安排 | `Jimmy 9:00到，随敬拜团排练` |
| `{video_director_detail}` | 导播/摄影详细安排 | `靖铮 9:30到，检查预设机位` |
| `{propresenter_play_detail}` | ProPresenter播放详细安排 | `张宇 9:00到，随敬拜团排练` |
| `{propresenter_update_detail}` | ProPresenter更新详细安排 | `Daniel 提前到，提前准备内容` |

### 月度总览通知模板

| 变量名 | 描述 | 示例值 |
|--------|------|---------|
| `{year}` | 年份 | `2025` |
| `{month}` | 月份 | `09` |
| `{sheet_url}` | Google Sheets链接 | `https://docs.google.com/...` |
| `{schedule_list}` | 排班列表（自动生成） | 包含整月的排班安排 |

## 🛠️ 模板编辑示例

### 周三确认通知的不同格式

#### 1. 标准格式（当前默认）
```
【本周{month}月{day}日主日事工安排提醒】🕊️

• 音控：{audio_tech}
• 导播/摄影：{video_director}
• ProPresenter播放：{propresenter_play}
• ProPresenter更新：{propresenter_update}
• 视频剪辑：{video_editor}

请大家确认时间，若有冲突请尽快私信我，感谢摆上 🙏
```

#### 2. 简洁格式
```
【{month}月{day}日事工安排】
音控：{audio_tech}，导播：{video_director}，播放：{propresenter_play}
请确认时间 🙏
```

#### 3. 详细格式
```
🕊️ 本周{month}月{day}日主日安排：

🎤 音控同工：{audio_tech}
📹 导播摄影：{video_director}
🖥️ ProPresenter播放：{propresenter_play}
🔄 ProPresenter更新：{propresenter_update}
🎬 视频剪辑：{video_editor}

请确认时间，如有冲突请联系协调员 🙏
```

#### 4. 表格格式
```
【主日事工安排 - {month}/{day}】
┌─────────────┬─────────────┐
│ 音控        │ {audio_tech}       │
│ 导播/摄影   │ {video_director}   │
│ PP播放      │ {propresenter_play}│
│ PP更新      │ {propresenter_update}│
│ 视频剪辑    │ {video_editor}     │
└─────────────┴─────────────┘
```

#### 5. 分组格式
```
【{month}月{day}日主日事工】

📺 媒体技术组：
  • 音控：{audio_tech}
  • 导播/摄影：{video_director}

💻 ProPresenter组：
  • 播放：{propresenter_play}
  • 更新：{propresenter_update}

🎬 后期制作：
  • 视频剪辑：{video_editor}

请各位同工确认时间 🙏
```

## 🌐 使用方法

### 本地编辑
1. 启动应用：`python3 start.py`
2. 访问：`http://localhost:8501`
3. 进入："🛠️ 模板编辑器"页面
4. 选择要编辑的模板类型
5. 在"编辑模板"标签页中修改内容
6. 在"预览效果"标签页中查看效果
7. 点击"应用更改"和"保存到本地"

### 云端编辑（部署后）
1. 访问部署的应用URL
2. 进入："🛠️ 模板编辑器"页面
3. 编辑模板内容
4. 点击"保存到云端"
5. 模板会自动保存到GCP Storage
6. 下次生成时会使用新模板

## 📁 文件结构

```
templates/
├── dynamic_templates.json      # 主模板配置文件
├── notification_templates.yaml # 旧模板（向后兼容）
└── email/                      # 邮件HTML模板
    ├── weekly_confirmation_wechat.html
    └── sunday_reminder_wechat.html
```

## ⚙️ 云端配置

### GCP Storage设置
```bash
# 1. 创建存储桶
gsutil mb gs://grace-irvine-templates

# 2. 上传初始模板
gsutil cp templates/dynamic_templates.json gs://grace-irvine-templates/templates/

# 3. 设置环境变量
export GCP_TEMPLATE_BUCKET=grace-irvine-templates
```

### Cloud Run环境变量
```yaml
env_vars:
  GCP_TEMPLATE_BUCKET: grace-irvine-templates
  GOOGLE_CLOUD_PROJECT: ai-for-god
  TEMPLATE_STORAGE_MODE: cloud
```

## 🔧 高级功能

### 模板验证
- 自动检查必需变量是否存在
- 验证模板语法正确性
- 提供详细的错误信息

### 自动备份
- 每次保存时自动创建备份
- 带时间戳的备份文件
- 支持版本回滚

### 实时预览
- 有安排时的效果预览
- 无安排时的效果预览
- 支持测试数据预览

## 💡 最佳实践

1. **变量使用**：
   - 必需变量：`{month}`, `{day}`
   - 推荐包含至少一个角色变量
   - 使用描述性的格式

2. **模板设计**：
   - 保持简洁明了
   - 使用合适的emoji
   - 考虑微信群显示效果

3. **版本管理**：
   - 重要修改前先创建备份
   - 在预览中充分测试
   - 逐步应用更改

4. **云端部署**：
   - 设置正确的GCP权限
   - 定期备份云端模板
   - 监控模板加载状态

## 📝 周六提醒通知编辑示例

### 不同格式示例

#### 1. 标准格式（当前默认）
```
【主日服事提醒】✨
明天 8:30布置/ 9:00彩排 / 10:00 正式敬拜
请各位同工提前到场：

- 音控：{audio_tech_detail}
- 导播/摄影：{video_director_detail}
- ProPresenter播放：{propresenter_play_detail}

愿主同在，出入平安。若临时不适请第一时间私信我。🙌
```

#### 2. 时间重点版
```
🔔 明日服事提醒：

⏰ 9:00 到场：{audio_tech_detail}
⏰ 9:30 到场：{video_director_detail}
⏰ 9:00 到场：{propresenter_play_detail}

愿主同在！
```

#### 3. emoji版
```
✨ 明日主日 ✨
🎤 {audio_tech_detail}
📹 {video_director_detail}
🖥️ {propresenter_play_detail}

🙏 请提前到场
```

#### 4. 简洁版
```
【明日主日】
音控：{audio_tech_detail}
导播：{video_director_detail}
播放：{propresenter_play_detail}
```

---

**Grace Irvine Ministry Scheduler v2.0** - 动态模板系统
Made with ❤️ for Grace Irvine Presbyterian Church
