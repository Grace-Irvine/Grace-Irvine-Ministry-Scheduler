# 配置文件目录

这个目录用于存放敏感的配置文件。

## 必需文件

### service_account.json
Google Cloud 服务账号的 JSON 密钥文件。

**获取步骤：**
1. 在 Google Cloud Console 创建服务账号
2. 下载 JSON 密钥文件
3. 重命名为 `service_account.json`
4. 放在这个目录下

**注意：** 此文件包含敏感信息，已在 .gitignore 中排除，不会提交到版本控制。

## 文件结构

```
configs/
├── README.md                 # 本文件
├── service_account.json      # Google 服务账号密钥 (需要自行添加)
├── settings.yaml             # 完整版系统配置 (可选)
└── notification_templates.yaml  # 通知模板配置 (可选)
```

## 安全提醒

- 不要将 `service_account.json` 文件提交到 Git
- 不要在公开场所分享这些文件
- 定期轮换服务账号密钥
