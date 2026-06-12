# 结构文件格式 / Structure File Formats

## 定义 / Definition

MLIP工作流支持多种结构文件格式，用于描述原子系统的几何构型。

## 支持的格式 / Supported Formats

| 扩展名 | 描述 | 常用场景 |
|--------|------|----------|
| .cif | Crystallographic Information File | 晶体结构 |
| .xyz | XYZ坐标格式 | 分子结构 |
| .poscar | VASP POSCAR格式 | 表面和块体材料 |
| .contcar | VASP CONTCAR格式 | 优化后的结构 |
| .json | JSON格式结构 | 程序化生成 |
| .yaml | YAML格式结构 | 配置文件 |

## 诊断规则 / Diagnostic Rules

### MLIP-E084 (warning)
- **名称**: `mlip.manifest.missing_structure`
- **描述**: manifest缺少必需的'structure'键
- **修复建议**: 添加缺失的'structure'键

### MLIP-E084 (warning) - 扩展名验证
- **描述**: 结构文件具有不支持的扩展名
- **有效扩展名**: `.cif`, `.xyz`, `.poscar`, `.contcar`, `.json`, `.yaml`, `.yml`
- **修复建议**: `check_structure_extension`

## MLIP-E086 路径引用检查
- **名称**: `mlip.files.missing_path_reference`
- **描述**: manifest引用的文件不存在
- **严重性**: warning
- **检查内容**:
  - `structure`键：总是检查文件是否存在
  - `model`键：仅在看起来像文件路径时检查

## 示例 / Example

```json
{
  "model": "DPA3.1-3M",
  "structure": "input.cif",
  "task": "optimize"
}
```

## 相关文件 / Related Files

- `raw/assets/matmaster_rules.py` - 结构扩展名定义
- `wiki/entities/MLIP_Manifest.md` - 清单文件结构
