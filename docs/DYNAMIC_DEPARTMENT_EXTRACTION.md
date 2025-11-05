# 动态部门提取设计

## 📋 概述

系统已改为动态提取所有部门和岗位，不再硬编码部门名称。这样可以：

1. **更灵活**：添加新部门或岗位时，代码不需要修改
2. **更健壮**：自动适应数据结构变化
3. **更易维护**：减少硬编码，降低维护成本

## 🔄 设计变化

### 之前（硬编码）

```python
# 硬编码部门名称
technical = volunteer.get('technical') or volunteer.get('media', {})
education = volunteer.get('education') or volunteer.get('children', {})
worship = volunteer.get('worship', {})

# 硬编码岗位名称
schedule_dict[date_str]['volunteers']['media'] = {
    'audio_tech': technical.get('audio', ''),
    'video_director': technical.get('video', ''),
    # ...
}
```

### 现在（动态提取）

```python
# 动态提取所有部门
for dept_key, dept_data in volunteer.items():
    if dept_key in excluded_keys:
        continue
    
    if not isinstance(dept_data, dict):
        continue
    
    # 动态提取所有岗位
    dept_roles = {}
    for role_key, role_value in dept_data.items():
        if role_value:
            # 处理不同类型的值（字符串、字典、列表）
            dept_roles[role_key] = extract_role_value(role_value)
    
    if dept_roles:
        schedule_dict[date_str]['volunteers'][dept_key] = dept_roles
```

## 🎯 实现细节

### 1. 数据读取器 (`src/json_data_reader.py`)

**动态提取所有部门**：

```python
# 动态提取所有部门（排除日期字段）
excluded_keys = {'service_date', 'date', 'metadata'}
for dept_key, dept_data in volunteer.items():
    if dept_key in excluded_keys:
        continue
    
    if not isinstance(dept_data, dict):
        continue
    
    # 处理部门数据：提取所有岗位
    dept_roles = {}
    for role_key, role_value in dept_data.items():
        if role_value is None or role_value == '':
            continue
        
        # 处理不同类型的值
        if isinstance(role_value, dict):
            # 如果是字典，提取 name 字段
            role_name = role_value.get('name', '')
        elif isinstance(role_value, list):
            # 如果是列表，转换为逗号分隔的字符串
            role_name = ', '.join([str(v) for v in role_value if v])
        else:
            # 直接使用字符串值
            role_name = str(role_value)
        
        if role_name:
            dept_roles[role_key] = role_name
    
    # 如果有岗位数据，添加到排程中
    if dept_roles:
        schedule_dict[date_str]['volunteers'][dept_key] = dept_roles
```

### 2. ICS 日历生成器 (`src/multi_calendar_generator.py`)

**动态显示所有部门和岗位**：

```python
# 动态提取所有部门和岗位，不硬编码部门名称
volunteers = overview_data.get('volunteers', {})

# 部门名称映射（可选，用于显示友好的中文名称）
dept_name_map = {
    'technical': '媒体部',
    'media': '媒体部',
    'education': '儿童部',
    'children': '儿童部',
    'worship': '敬拜团队',
    'outreach': '外展联络'
}

# 岗位名称映射（可选，用于显示友好的中文名称）
role_name_map = {
    'audio': '音控',
    'video': '导播/摄影',
    'propresenter_play': 'ProPresenter播放',
    # ...
}

# 遍历所有部门
for dept_key, dept_roles in volunteers.items():
    if not dept_roles or not isinstance(dept_roles, dict):
        continue
    
    # 获取部门显示名称
    dept_display_name = dept_name_map.get(dept_key, dept_key)
    description_lines.append(f"{dept_display_name}:")
    
    # 遍历该部门的所有岗位
    for role_key, role_value in dept_roles.items():
        if not role_value:
            continue
        
        # 获取岗位显示名称
        role_display_name = role_name_map.get(role_key, role_key.replace('_', ' '))
        
        # 处理岗位值
        if isinstance(role_value, list):
            for i, val in enumerate(role_value, 1):
                if val:
                    description_lines.append(f"  {role_display_name}{i}: {val}")
        else:
            description_lines.append(f"  {role_display_name}: {role_value}")
```

## ✅ 优势

### 1. **灵活性**
- 添加新部门（如 `outreach`）时，代码自动支持
- 添加新岗位时，无需修改代码
- 适应数据结构变化

### 2. **可维护性**
- 减少硬编码，降低维护成本
- 代码更简洁，逻辑更清晰
- 易于测试和调试

### 3. **健壮性**
- 自动处理缺失的部门或岗位
- 支持多种数据格式（字符串、字典、列表）
- 向后兼容旧的数据结构

## 🔧 配置映射

虽然代码是动态的，但为了显示友好的中文名称，我们保留了可选的映射配置：

### 部门名称映射

```python
dept_name_map = {
    'technical': '媒体部',
    'media': '媒体部',
    'education': '儿童部',
    'children': '儿童部',
    'worship': '敬拜团队',
    'outreach': '外展联络'
}
```

### 岗位名称映射

```python
role_name_map = {
    'audio': '音控',
    'video': '导播/摄影',
    'propresenter_play': 'ProPresenter播放',
    'propresenter_update': 'ProPresenter更新',
    # ...
}
```

**注意**：这些映射是**可选的**，如果 JSON 数据中已经包含中文名称，或者不关心显示名称，可以完全移除这些映射。

## 📊 数据格式支持

系统支持以下数据格式：

### 1. 字符串值

```json
{
  "technical": {
    "audio": "音控人员",
    "video": "导播/摄影人员"
  }
}
```

### 2. 字典值（包含 name 字段）

```json
{
  "technical": {
    "audio": {"name": "音控人员", "id": "123"},
    "video": {"name": "导播/摄影人员", "id": "456"}
  }
}
```

### 3. 列表值

```json
{
  "worship": {
    "team": ["成员1", "成员2", "成员3"]
  }
}
```

## 🚀 未来扩展

如果将来需要添加新的部门或岗位：

1. **在 JSON 数据中添加**：直接添加新的部门或岗位数据
2. **代码自动支持**：无需修改代码，系统会自动提取和显示
3. **可选配置映射**：如果需要友好的显示名称，在映射中添加即可

## 📚 相关文档

- [新 ICS 系统架构设计](NEW_ICS_ARCHITECTURE.md)
- [数据源结构说明](DATA_SOURCE_STRUCTURE.md)

