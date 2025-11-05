# GCS 权限设置指南

## 📋 概述

为了从 GCS bucket (`grace-irvine-ministry-data`) 读取 JSON 数据并生成 ICS 文件，需要配置正确的服务账号权限。

## 🔑 需要的权限

### 数据源 Bucket (`grace-irvine-ministry-data`)

服务账号需要以下权限来读取 JSON 数据：

1. **Storage Object Viewer** (`roles/storage.objectViewer`)

   - 读取 bucket 中的对象（JSON 文件）
   - 列出 bucket 中的对象
2. **Storage Legacy Bucket Reader** (`roles/storage.legacyBucketReader`) - 可选

   - 如果需要列出 bucket 内容

### ICS 存储 Bucket (`grace-irvine-ministry-scheduler`)

服务账号需要以下权限来写入 ICS 文件：

1. **Storage Object Creator** (`roles/storage.objectCreator`)

   - 创建新对象（ICS 文件）
2. **Storage Object Viewer** (`roles/storage.objectViewer`)

   - 读取已存在的对象

## 🛠️ 设置权限的方法

### 方法 1: 使用 gcloud 命令（推荐）

#### 1. 获取服务账号邮箱

首先，检查服务账号文件：

```bash
# 查看服务账号文件
cat configs/service_account.json | jq -r '.client_email'
```

#### 2. 授予数据源 Bucket 权限

```bash
# 授予 Storage Object Viewer 权限
gsutil iam ch serviceAccount:scheduler-service@ai-for-god.iam.gserviceaccount.com:roles/storage.objectViewer gs://grace-irvine-ministry-data

# 可选：授予 Storage Legacy Bucket Reader 权限
gsutil iam ch serviceAccount:scheduler-service@ai-for-god.iam.gserviceaccount.com:roles/storage.legacyBucketReader gs://grace-irvine-ministry-data
```

#### 3. 授予 ICS 存储 Bucket 权限

```bash
# 授予 Storage Object Creator 权限
gsutil iam ch serviceAccount:scheduler-service@ai-for-god.iam.gserviceaccount.com:roles/storage.objectCreator gs://grace-irvine-ministry-scheduler

# 授予 Storage Object Viewer 权限
gsutil iam ch serviceAccount:scheduler-service@ai-for-god.iam.gserviceaccount.com:roles/storage.objectViewer gs://grace-irvine-ministry-scheduler
```

### 方法 2: 使用 GCP Console

1. **访问 IAM & Admin**

   - 打开 [GCP Console](https://console.cloud.google.com/)
   - 导航到 **IAM & Admin** > **IAM**
2. **找到服务账号**

   - 在 IAM 页面中搜索服务账号邮箱
   - 点击服务账号行右侧的 **编辑** 按钮
3. **添加权限**

   - 点击 **添加另一个角色**
   - 为数据源 bucket 添加：
     - `Storage Object Viewer`
     - `Storage Legacy Bucket Reader` (可选)
   - 为 ICS 存储 bucket 添加：
     - `Storage Object Creator`
     - `Storage Object Viewer`
4. **保存更改**

### 方法 3: 使用 Bucket IAM 策略

#### 设置数据源 Bucket (`grace-irvine-ministry-data`)

```bash
# 获取当前 bucket IAM 策略
gsutil iam get gs://grace-irvine-ministry-data > bucket-iam-policy.json

# 编辑 bucket-iam-policy.json，添加服务账号权限
# 然后应用策略
gsutil iam set bucket-iam-policy.json gs://grace-irvine-ministry-data
```

IAM 策略示例：

```json
{
  "bindings": [
    {
      "role": "roles/storage.objectViewer",
      "members": [
        "serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL"
      ]
    }
  ]
}
```

## ✅ 验证权限

### 使用测试脚本

运行测试脚本验证权限：

```bash
python3 scripts/test_gcs_permissions.py
```

### 手动测试

```bash
# 测试读取数据源 bucket
python3 scripts/test_bucket_access.py grace-irvine-ministry-data

# 测试读取 ICS 存储 bucket
python3 scripts/test_bucket_access.py grace-irvine-ministry-scheduler
```

### 测试生成 ICS 文件

```bash
# 生成 ICS 文件（会从 GCS 读取数据）
python3 scripts/generate_local_ics.py
```

## 🔍 检查当前权限

### 查看服务账号权限

```bash
# 查看数据源 bucket 的 IAM 策略
gsutil iam get gs://grace-irvine-ministry-data

# 查看 ICS 存储 bucket 的 IAM 策略
gsutil iam get gs://grace-irvine-ministry-scheduler
```

### 查看服务账号在项目中的角色

```bash
# 列出服务账号的所有角色
gcloud projects get-iam-policy ai-for-god \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" \
  --format="table(bindings.role)"
```

## 🐛 常见问题

### 问题 1: 403 Forbidden 错误

**错误信息**:

```
❌ GCS初始化失败: 403 Forbidden
```

**解决方案**:

1. 检查服务账号是否有正确的权限
2. 确认 bucket 名称正确
3. 验证服务账号文件路径是否正确设置

### 问题 2: 找不到 bucket

**错误信息**:

```
❌ Bucket不存在: grace-irvine-ministry-data
```

**解决方案**:

1. 检查 bucket 名称是否正确
2. 确认项目 ID 正确
3. 验证服务账号是否有权限访问该 bucket

### 问题 3: 无法读取文件

**错误信息**:

```
❌ 文件不存在: domains/sermon/latest.json
```

**解决方案**:

1. 检查文件路径是否正确
2. 确认文件在 bucket 中确实存在
3. 验证服务账号有 `Storage Object Viewer` 权限

## 📚 相关文档

- [GCP IAM 权限文档](https://cloud.google.com/iam/docs/overview)
- [GCS IAM 权限文档](https://cloud.google.com/storage/docs/access-control/iam)
- [gsutil iam 命令文档](https://cloud.google.com/storage/docs/gsutil/commands/iam)

## 🔐 安全建议

1. **最小权限原则**: 只授予必要的权限
2. **定期审查**: 定期检查服务账号权限
3. **使用服务账号**: 不要使用个人账号进行生产操作
4. **密钥保护**: 不要将服务账号密钥提交到代码仓库
