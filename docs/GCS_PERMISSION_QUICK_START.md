# GCS 权限快速设置指南

## 🎯 目标

从 GCS bucket (`grace-irvine-ministry-data`) 读取 JSON 数据，并生成 ICS 文件到 `grace-irvine-ministry-scheduler` bucket。

## ⚡ 快速设置（3 步）

### 步骤 1: 获取服务账号邮箱

```bash
# 查看服务账号邮箱
cat configs/service_account.json | jq -r '.client_email'
```

或者使用 Python:
```python
import json
with open('configs/service_account.json') as f:
    sa = json.load(f)
    print(sa['client_email'])
```

### 步骤 2: 设置权限（方法 1：使用脚本）

```bash
# 运行自动设置脚本
./scripts/setup_gcs_permissions.sh
```

### 步骤 2: 设置权限（方法 2：手动设置）

```bash
# 替换 YOUR_SERVICE_ACCOUNT_EMAIL 为实际的服务账号邮箱

# 设置数据源 bucket 权限
gsutil iam ch serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL:roles/storage.objectViewer gs://grace-irvine-ministry-data
gsutil iam ch serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL:roles/storage.legacyBucketReader gs://grace-irvine-ministry-data

# 设置 ICS 存储 bucket 权限
gsutil iam ch serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL:roles/storage.objectCreator gs://grace-irvine-ministry-scheduler
gsutil iam ch serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL:roles/storage.objectViewer gs://grace-irvine-ministry-scheduler
```

### 步骤 3: 验证权限

```bash
# 运行权限测试
python3 scripts/test_gcs_permissions.py
```

如果看到 ✅ 标记，说明权限设置成功！

## 📋 需要的权限

### 数据源 Bucket (`grace-irvine-ministry-data`)

| 权限 | 角色 | 用途 |
|------|------|------|
| 读取对象 | `roles/storage.objectViewer` | 读取 JSON 文件 |
| 列出对象 | `roles/storage.legacyBucketReader` | 列出 bucket 内容（可选） |

### ICS 存储 Bucket (`grace-irvine-ministry-scheduler`)

| 权限 | 角色 | 用途 |
|------|------|------|
| 创建对象 | `roles/storage.objectCreator` | 写入 ICS 文件 |
| 读取对象 | `roles/storage.objectViewer` | 读取已存在的 ICS 文件 |

## ✅ 验证测试

运行测试脚本验证权限：

```bash
python3 scripts/test_gcs_permissions.py
```

应该看到：
- ✅ 可以读取 bucket: grace-irvine-ministry-data
- ✅ 可以读取文件: domains/sermon/latest.json
- ✅ 可以读取文件: domains/volunteer/latest.json
- ✅ 可以写入 bucket: grace-irvine-ministry-scheduler

## 🚀 生成 ICS 文件

权限设置完成后，运行：

```bash
python3 scripts/generate_local_ics.py
```

现在应该能够：
- ✅ 从 GCS bucket 读取 JSON 数据
- ✅ 生成 ICS 文件
- ✅ 保存到本地 `calendars/` 目录

## 🐛 常见问题

### 问题 1: 403 Forbidden

**错误**: `❌ GCS初始化失败: 403 Forbidden`

**解决**: 
1. 检查服务账号是否有正确权限
2. 运行 `python3 scripts/test_gcs_permissions.py` 查看详细错误

### 问题 2: 找不到 bucket

**错误**: `❌ Bucket不存在: grace-irvine-ministry-data`

**解决**:
1. 确认 bucket 名称正确
2. 检查项目 ID 是否正确：`ai-for-god`

### 问题 3: 无法读取文件

**错误**: `❌ 文件不存在: domains/sermon/latest.json`

**解决**:
1. 检查文件路径是否正确
2. 确认文件在 bucket 中确实存在
3. 验证服务账号有 `Storage Object Viewer` 权限

## 📚 更多信息

详细说明请参考：
- [GCS 权限设置完整指南](GCS_PERMISSION_SETUP.md)
- [GCP IAM 文档](https://cloud.google.com/iam/docs/overview)

