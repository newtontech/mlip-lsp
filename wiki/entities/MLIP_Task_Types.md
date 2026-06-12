# MLIP 任务类型 / MLIP Task Types

## 定义 / Definition

MLIP任务类型指定使用MLIP模型执行的计算类型，每个任务可能有特定的参数要求。

## 支持的任务 / Supported Tasks

### optimize
- **描述**: 结构优化（几何优化）
- **必需参数**: 无
- **说明**: 优化原子位置以达到局部能量最小值

### md (Molecular Dynamics)
- **描述**: 分子动力学模拟
- **推荐参数**: `temperature`, `steps`
- **说明**: 在给定温度下进行时间演化的动力学模拟

### static
- **描述**: 静态单点计算
- **必需参数**: 无
- **说明**: 计算固定构型的能量和力

### relax
- **描述**: 结构弛豫
- **必需参数**: 无
- **说明**: 类似于optimize，优化原子位置和晶胞参数

### phonon
- **描述**: 声子谱计算
- **必需参数**: 无
- **说明**: 计算晶格振动性质

### neb
- **描述**: 微动弹性带（Nudged Elastic Band）
- **必需参数**: 无
- **说明**: 计算反应路径和能垒

### transition_state
- **描述**: 过渡态搜索
- **必需参数**: 无
- **说明**: 寻找化学反应的过渡态

## 诊断代码 / Diagnostic Codes

- **MLIP-E083**: `mlip.manifest.missing_task` - manifest缺少必需的'task'键
- **MLIP-E083** (warning): 未知任务类型
- **MLIP-E083** (warning): 任务缺少推荐参数

## 参数验证规则 / Parameter Validation Rules

```python
TASK_REQUIREMENTS: dict[str, list[str]] = {
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

- `raw/assets/matmaster_rules.py` - 任务要求定义
- `wiki/entities/MLIP_Manifest.md` - 任务在manifest中的使用
