# MatMaster 执行约定 / MatMaster Execution Contract

## 概述 / Overview

MatMaster执行约定编码了MatMaster在调度MLIP作业时期望的结构验证规则。这些规则确保manifest符合自动执行的要求。

## 约定内容 / Contract Contents

### 1. 必需字段验证
所有manifest必须包含：
- `model`: MLIP模型标识符
- `task`: 计算任务类型
- `structure`: 输入结构文件路径

### 2. 模型验证
- 验证模型名称是否在已知模型族中
- 提供已知模型列表作为建议
- 标记未知模型但不阻止执行

### 3. 任务验证
- 验证任务类型是否有效
- 检查任务所需的推荐参数
- 提供有效任务类型列表

### 4. 结构文件验证
- 验证结构文件扩展名是否支持
- 提供有效扩展名列表
- 标记不支持的扩展名

### 5. 跨文件引用检查
- 验证引用的文件是否存在
- 检查`structure`字段（总是检查）
- 检查`model`字段（仅在看起来像文件路径时）

## 诊断映射 / Diagnostic Mapping

| 约定违反 | 诊断代码 | 严重性 |
|---------|---------|--------|
| 缺少model | MLIP-E082 | error |
| 缺少task | MLIP-E083 | error |
| 缺少structure | MLIP-E084 | error |
| 未知模型 | MLIP-E082 | warning |
| 未知任务 | MLIP-E083 | warning |
| 缺少任务参数 | MLIP-E083 | warning |
| 不支持的扩展名 | MLIP-E084 | warning |
| 文件不存在 | MLIP-E086 | warning |

## 模型族定义 / Model Family Definitions

```python
MODEL_FAMILIES = {
    "DPA3.1-3M": {"engine": "dp", "requires_model_file": True},
    "DPA2": {"engine": "dp", "requires_model_file": True},
    "MACE": {"engine": "mace", "requires_model_file": True},
    "NEP": {"engine": "gpumd", "requires_model_file": True},
    "CHGNet": {"engine": "chgnet", "requires_model_file": True},
    "M3GNet": {"engine": "m3gnet", "requires_model_file": True},
    "SevenNet": {"engine": "sevenn", "requires_model_file": True},
    "ORB": {"engine": "orb", "requires_model_file": True},
}
```

## 任务参数要求 / Task Parameter Requirements

```python
TASK_REQUIREMENTS = {
    "optimize": [],
    "md": ["temperature", "steps"],
    "static": [],
    "relax": [],
    "phonon": [],
    "neb": [],
    "transition_state": [],
}
```

## 相关文件 / Related Files

- `raw/assets/matmaster_rules.py` - 完整约定实现
- `wiki/entities/MLIP_Manifest.md` - Manifest结构
