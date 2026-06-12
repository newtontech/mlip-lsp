# 输入格式参考 / Input Format Reference

## Manifest格式 / Manifest Formats

### JSON Manifest

**扩展名**: `.json`

**必需字段**:
```json
{
  "model": "DPA3.1-3M",
  "structure": "input.cif",
  "task": "optimize"
}
```

**可选字段**:
```json
{
  "model": "DPA3.1-3M",
  "structure": "input.cif",
  "task": "md",
  "parameters": {
    "temperature": 300,
    "steps": 10000
  },
  "output": {
    "trajectory": "output.xyz",
    "log": "simulation.log"
  }
}
```

### YAML Manifest

**扩展名**: `.yaml`, `.yml`

**格式**:
```yaml
model: DPA3.1-3M
structure: input.cif
task: optimize
parameters:
  fmax: 0.01
```

## Python脚本格式 / Python Script Format

**扩展名**: `.py`

**要求**:
1. 导入`ase`模块
2. 定义`structure`符号（ASE Atoms对象）
3. 附加MLIP计算器

**最小示例**:
```python
from ase import Atoms
from mlip import MLIPCalculator

structure = Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])
calc = MLIPCalculator(model="DPA3.1-3M")
structure.calc = calc
```

**完整工作流示例**:
```python
from ase import Atoms
from ase.optimize import BFGS
from mlip import MLIPCalculator

structure = Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])
calc = MLIPCalculator(model="DPA3.1-3M")
structure.calc = calc
opt = BFGS(structure)
opt.run(fmax=0.01)
```

## 结构文件格式 / Structure File Formats

### CIF (.cif)
Crystallographic Information File格式，用于晶体结构。

### XYZ (.xyz)
简单的XYZ坐标格式：
```
2
H2 molecule comment
H 0.0 0.0 0.0
H 0.0 0.0 0.74
```

### POSCAR/CONTCAR (.poscar, .contcar)
VASP格式，常用于表面和块体材料。

### JSON/YAML (.json, .yaml)
程序化生成的结构格式。

## 配置文件格式 / Configuration File Formats

### NEP配置 (.txt, .nep)
神经进化势训练配置：
```
generation     200000
population     50
batch          10
neuron         30
cutoff         5.0
lambda_1       0.1
lambda_2       0.1
```

## 日志文件格式 / Log File Formats

### 运行时日志 (.log)
包含MLIP计算输出的文本文件，可包含Python tracebacks。

**示例**:
```
Starting MLIP calculation...
Traceback (most recent call last):
  File "run.py", line 5, in <module>
    calc = MLIPCalculator(model='bad')
RuntimeError: Model not found
Done.
```

## 字段验证规则 / Field Validation Rules

### model字段
- **类型**: 字符串
- **有效值**: DPA3.1-3M, DPA2, MACE, NEP, CHGNet, M3GNet, SevenNet, ORB
- **诊断**: MLIP-E082 (缺少), MLIP-E082 (未知模型)

### structure字段
- **类型**: 字符串（文件路径）
- **有效扩展名**: .cif, .xyz, .poscar, .contcar, .json, .yaml, .yml
- **诊断**: MLIP-E084 (缺少), MLIP-E084 (无效扩展名), MLIP-E086 (文件不存在)

### task字段
- **类型**: 字符串
- **有效值**: optimize, md, static, relax, phonon, neb, transition_state
- **诊断**: MLIP-E083 (缺少), MLIP-E083 (未知任务), MLIP-E083 (缺少参数)

### parameters字段
- **类型**: 对象/字典
- **任务特定要求**:
  - `md`: 推荐`temperature`, `steps`
- **诊断**: MLIP-E083 (缺少推荐参数)

## 相关文件 / Related Files

- `raw/assets/valid_manifest.json` - 有效JSON示例
- `raw/assets/valid_manifest.yaml` - 有效YAML示例
- `raw/assets/valid_ase_script.py` - 有效Python示例
