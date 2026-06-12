# ASE 原子模拟环境 / ASE Atomistic Simulation Environment

## 定义 / Definition

ASE（Atomic Simulation Environment）是Python中用于原子模拟的库，提供原子结构表示、计算器接口和优化算法等功能。

## 在MLIP工作流中的角色 / Role in MLIP Workflows

ASE是MLIP Python脚本的核心依赖，提供：

1. **Atoms对象**: 表示原子结构和位置
2. **Calculator接口**: 连接MLIP计算器
3. **优化器**: BFGS, LBFGS, FIRE等

## 必需符号 / Required Symbols

### structure
- **描述**: ASE Atoms对象，用于MLIP工作流
- **要求**: 应具有`.calc`属性（附加的计算器）
- **诊断代码**: MLIP-E085 (缺少时)

## 常用导入 / Common Imports

```python
from ase import Atoms
from ase.optimize import BFGS, LBFGS, FIRE
from mlip import MLIPCalculator
```

## 典型工作流 / Typical Workflow

```python
from ase import Atoms
from ase.optimize import BFGS
from mlip import MLIPCalculator

# 创建结构
structure = Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])

# 附加MLIP计算器
calc = MLIPCalculator(model="DPA3.1-3M")
structure.calc = calc

# 运行优化
opt = BFGS(structure)
opt.run(fmax=0.01)
```

## 诊断代码 / Diagnostic Codes

- **MLIP-W080**: `mlip.python.missing_ase_import` - Python脚本缺少ASE导入
- **MLIP-E085**: `mlip.python.missing_structure_symbol` - Python脚本缺少'structure'符号

## ASE计算器属性 / ASE Calculator Attribute

### calc
- **描述**: 附加到Atoms对象上的计算器
- **用途**: 进行DFT或MLIP计算
- **工作流**: `structure.calc = MLIPCalculator(...)`

## 相关文件 / Related Files

- `raw/assets/valid_ase_script.py` - 有效ASE脚本示例
- `wiki/entities/MLIP_Models.md` - 支持的MLIP模型
