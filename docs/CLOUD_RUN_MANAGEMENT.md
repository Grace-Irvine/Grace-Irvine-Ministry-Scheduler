# Cloud Run 管理指南

## 🌐 Web 管理界面

你的 Streamlit 管理界面现已部署到 Cloud Run，可以在任何地方通过浏览器访问！

### 🔗 访问地址
**https://grace-irvine-scheduler-wu7uk5rgdq-uc.a.run.app**

## ✨ 功能特性

### 📊 数据管理
- **实时数据查看**: 查看从 Google Sheets 提取的最新排班数据
- **数据质量监控**: 实时检查数据完整性和准确性
- **数据清洗**: 自动清洗和标准化数据格式

### 📝 通知管理
- **模板生成**: 一键生成微信群通知模板
- **内容预览**: 实时预览通知内容
- **模板编辑**: 在线编辑和自定义通知模板

### 📧 邮件功能
- **邮件测试**: 测试邮件发送功能
- **收件人管理**: 管理邮件收件人列表
- **发送历史**: 查看邮件发送记录

### 📈 统计分析
- **服事统计**: 查看各项事工的参与情况
- **时间分析**: 分析排班时间分布
- **数据导出**: 支持 Excel 和 CSV 格式导出

## 🔧 管理操作

### 查看服务状态
```bash
gcloud run services describe grace-irvine-scheduler --region=us-central1
```

### 查看实时日志
```bash
gcloud run services logs read grace-irvine-scheduler --region=us-central1 --follow
```

### 更新服务
```bash
# 重新部署最新版本
./deploy_streamlit_to_cloudrun.sh
```

### 配置管理
```bash
# 查看当前配置
gcloud run services describe grace-irvine-scheduler --region=us-central1 --format="export"

# 更新环境变量
gcloud run services update grace-irvine-scheduler \
    --region=us-central1 \
    --set-env-vars="NEW_VAR=value"
```

## 🚀 性能优化

### 当前配置
- **CPU**: 1 vCPU
- **内存**: 1 GB
- **并发**: 80 个请求
- **最大实例**: 10 个
- **超时**: 1 小时

### 扩容配置
如果需要处理更多用户，可以调整配置：

```bash
gcloud run services update grace-irvine-scheduler \
    --region=us-central1 \
    --memory=2Gi \
    --cpu=2 \
    --concurrency=100 \
    --max-instances=20
```

## 🔒 安全配置

### 访问控制
当前配置为允许未经身份验证的访问。如需限制访问：

```bash
# 要求身份验证
gcloud run services update grace-irvine-scheduler \
    --region=us-central1 \
    --no-allow-unauthenticated

# 添加IAM权限
gcloud run services add-iam-policy-binding grace-irvine-scheduler \
    --region=us-central1 \
    --member="user:your-email@example.com" \
    --role="roles/run.invoker"
```

### 自定义域名
配置自定义域名：

```bash
# 映射域名
gcloud run domain-mappings create \
    --service=grace-irvine-scheduler \
    --domain=scheduler.graceirvine.org \
    --region=us-central1
```

## 📊 监控和告警

### Cloud Monitoring
- 访问 [Google Cloud Console](https://console.cloud.google.com)
- 导航到 "监控" → "指标浏览器"
- 选择 "Cloud Run" 资源类型
- 监控关键指标：
  - 请求计数
  - 请求延迟
  - 内存使用率
  - CPU 使用率

### 设置告警
```bash
# 创建告警策略（示例）
gcloud alpha monitoring policies create \
    --policy-from-file=alert-policy.yaml
```

## 💰 成本管理

### 当前成本结构
- **基础费用**: 每月前 180,000 次请求免费
- **计算费用**: 按 vCPU 秒计费
- **内存费用**: 按 GB 秒计费
- **网络费用**: 按出站流量计费

### 成本优化建议
1. **合理设置最小实例数**: 通常设为 0 以节省成本
2. **优化并发数**: 根据实际需求调整
3. **监控使用情况**: 定期检查使用统计

## 🔄 版本管理

### 查看版本历史
```bash
gcloud run revisions list --service=grace-irvine-scheduler --region=us-central1
```

### 回滚到上一版本
```bash
# 获取上一版本名称
PREVIOUS_REVISION=$(gcloud run revisions list --service=grace-irvine-scheduler --region=us-central1 --format="value(metadata.name)" --limit=2 | tail -n 1)

# 回滚
gcloud run services update-traffic grace-irvine-scheduler \
    --region=us-central1 \
    --to-revisions=$PREVIOUS_REVISION=100
```

## 🛠️ 故障排除

### 常见问题

#### 1. 应用启动缓慢
**原因**: 冷启动延迟
**解决**: 
```bash
# 设置最小实例数
gcloud run services update grace-irvine-scheduler \
    --region=us-central1 \
    --min-instances=1
```

#### 2. 内存不足错误
**原因**: 应用内存使用超限
**解决**:
```bash
# 增加内存配置
gcloud run services update grace-irvine-scheduler \
    --region=us-central1 \
    --memory=2Gi
```

#### 3. 超时错误
**原因**: 请求处理时间过长
**解决**:
```bash
# 增加超时时间
gcloud run services update grace-irvine-scheduler \
    --region=us-central1 \
    --timeout=1800  # 30分钟
```

### 调试工具
```bash
# 查看详细日志
gcloud run services logs read grace-irvine-scheduler \
    --region=us-central1 \
    --limit=50

# 连接到容器（调试模式）
gcloud run services describe grace-irvine-scheduler \
    --region=us-central1 \
    --format="value(status.url)"
```

## 📱 移动端访问

Web 界面已针对移动设备优化，可以在手机或平板电脑上正常使用。

### 添加到主屏幕
在移动浏览器中：
1. 访问应用URL
2. 点击浏览器菜单
3. 选择"添加到主屏幕"
4. 设置应用图标和名称

## 🔄 自动化部署

### GitHub Actions（可选）
可以设置 GitHub Actions 实现自动部署：

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ai-for-god
      - run: ./deploy_streamlit_to_cloudrun.sh
```

---

**🎯 现在你可以在任何地方管理你的事工排班系统了！**
