# MLIP 清单文件 / MLIP Manifest

## 定义 / Definition

MLIP清单文件是描述MLIP计算任务的JSON或YAML格式配置文件，包含模型、结构和任务类型等必需信息。

## 必需字段 / Required Fields

### model
- **描述**: MLIP模型标识符
- **示例**: `"DPA3.1-3M"`, `"MACE"`, `"NEP"`
- **诊断代码**: MLIP-E082 (缺少时)

### structure
- **描述**: 输入结构文件路径
- **支持格式**: CIF, XYZ, POSCAR, CONTCAR, JSON, YAML
- **诊断代码**: MLIP-E084 (缺少时)

### task
- **描述**: 计算任务类型
- **有效值**: `optimize`, `md`, `static`, `relax`, `phonon`, `neb`, `transition_state`
- **诊断代码**: MLIP-E083 (缺少时)

## 可选字段 / Optional Fields

### parameters
- **描述**: 模拟参数字典
- **示例**: `{"temperature": 300, "steps": 10000}`
- **特定任务要求**:
  - `md` 任务推荐: `temperature`, `steps`

### output
- **描述**: 输出文件路径和选项

## 示例 / Example

```json
{
  "model": "DPA3.1-3M",
  "structure": "input.cif",
  "task": "optimize",
  "parameters": {
    "fmax": 0.01
  }
}
```

## 支持的文件格式 / Supported Formats

- `.json` - JSON格式
- `.yaml`, `.yml` - YAML格式

## 诊断代码 / Diagnostic Codes

| 代码 | 名称 | 严重性 | 描述 |
|------|------|--------|------|
| MLIP-E080 | mlip.json.invalid | error | JSON无法解析 |
| MLIP-E081 | mlip.yaml.invalid | error | YAML无法解析 |
| MLIP-E082 | mlip.manifest.missing_model | error | 缺少model键 |
| MLIP-E083 | mlip.manifest.missing_task | error | 缺少task键 |
| MLIP-E084 | mlip.manifest.missing_structure | error | 缺少structure键 |
| MLIP-E086 | mlip.files.missing_path_reference | warning | 引用的文件不存在 |

## 相关文件 / Related Files

- `raw/assets/valid_manifest.json` - 有效清单示例
- `raw/assets/examples/manifest_md.json` - 带 MD 参数的清单示例
- `wiki/synthesis/openqc-agent-context.md` - OpenQC agent LSP 映射
- `wiki/entities/MLIP_Models.md` - 支持的模型列表
- `wiki/entities/MLIP_Task_Types.md` - 任务类型详解
