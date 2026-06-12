# 安全格式化 / Safe Formatting

## 概述 / Overview

mlip-lsp提供安全的文档格式化功能，确保格式化操作永远不会抛出异常，并保持幂等性。

## 保证 / Guarantees

1. **永不抛出** - 任何解析/格式化失败时返回原始文本
2. **幂等性** - `format(format(text)) == format(text)`
3. **保留换行约定** - 保留原始文件的尾随换行符

## 支持的格式 / Supported Formats

### JSON格式化
- **函数**: `format_json(text)`
- **行为**:
  - 解析失败时返回原文本
  - 使用2空格缩进
  - 键按字母顺序排序
  - 确保ASCII可读性
  - 添加尾随换行符

### YAML格式化
- **函数**: `format_yaml(text)`
- **行为**:
  - 解析失败时返回原文本
  - 使用默认流样式
  - 键按字母顺序排序
  - 允许Unicode
  - 保留YAML dump的默认换行

### 文本格式化
- **函数**: `format_text(text)`
- **行为**:
  - 对齐键值对格式
  - 键左对齐24字符
  - 保留注释行（以#、!、;开头）
  - 保留空行
  - 添加尾随换行符

## 格式化调度 / Formatting Dispatch

```python
def safe_format(text: str, file_suffix: str) -> str:
    """根据文件类型分派格式化。永不抛出。"""
    suffix = file_suffix.lower()
    if suffix == ".json":
        return format_json(text)
    if suffix in (".yaml", ".yml"):
        return format_yaml(text)
    return format_text(text)
```

## 幂等性检查 / Idempotency Check

```python
def is_idempotent(text: str, file_suffix: str) -> bool:
    """检查格式化是否幂等。"""
    first = safe_format(text, file_suffix)
    second = safe_format(first, file_suffix)
    return first == second
```

## NEP配置示例 / NEP Configuration Example

原始输入：
```
# NEP training configuration
generation = 200000
population = 50
```

格式化后：
```
# NEP training configuration
generation                = 200000
population                = 50
```

## 相关文件 / Related Files

- `src/mlip_lsp/features/formatter.py` - 格式化器实现
- `raw/assets/nep_config.txt` - NEP配置示例
