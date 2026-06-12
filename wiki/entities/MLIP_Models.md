# MLIP 模型族 / MLIP Model Families

## 定义 / Definition

机器学习原子间势（Machine Learning Interatomic Potentials, MLIP）模型是用机器学习方法训练的原子间势函数，用于替代传统的DFT计算，在保持较高精度的同时大幅提升计算速度。

## 已支持的模型 / Supported Models

### DPA (Deep Potential - Atom)
- **DPA3.1-3M**: DeepMD模型，3M参数规模
- **DPA2**: Deep Potential Architecture 第二代
- **DPA-1**: se_atten descriptor
- 引擎: `dp` (DeePMD-kit)
- 需要模型文件: `.pb` (frozen protocol buffer)
- 训练数据格式: `.npy` (NumPy) 或 `.h5` (HDF5)
- 输入参数格式: JSON 或 YAML
- 数据转换工具: `dpdata`
- 特点: 支持TensorFlow/PyTorch/JAX/Paddle多后端，MPI和GPU支持

### MACE (Multi-Atomic Cluster Expansion)
- 引擎: `mace` (`mace-torch` PyPI包)
- 需要模型文件: `.model`
- 训练数据格式: Extended XYZ (`.xyz`) 或 HDF5 (`.h5`)
- 配置格式: CLI参数或YAML
- 特点: 高阶等变消息传递，支持预训练基础模型
- 基础模型: MACE-MP-0 (89元素), MACE-OFF23 (有机), MACE-MH (跨域)
- ASE集成: `from mace.calculators import mace_mp, mace_off`
- LAMMPS集成: `pair_style mace`
- 参考: Batatia et al., NeurIPS 2022

### NEP (Neuroevolution Potential)
- 引擎: `gpumd` / `nep`
- 需要模型文件: `nep.txt` (训练输出)
- 训练配置: `nep.in` (键值对格式)
- 训练数据格式: Extended XYZ (`train.xyz`, `test.xyz`)
- 输出文件: `nep.txt`, `nep.restart`, `loss.out`
- 版本: NEP3, NEP4 (推荐)
- 特点: GPU原生训练，SNES进化算法，支持ZBL排斥势
- 参考: Fan et al., Phys. Rev. B 104, 104309 (2021)

### MTP (Moment Tensor Potential)
- 引擎: `mlp` (MLIP-2/3包)
- 需要模型文件: `.mtp`
- 训练数据格式: `.cfg` (MLIP内部格式)
- 配置格式: `mlip.ini` (INI格式)
- 特点: 主动学习（MaxVol选择），MPI支持
- 关键命令: `mlp train`, `mlp select-add`, `mlp relax`, `mlp calc-grade`
- 来源: Skoltech (mlip.skoltech.ru), GitLab: ashapeev/mlip-2
- 参考: Novikov et al., Mach. Learn.: Sci. Technol. 2, 025002 (2021)

### NequIP (Neural Equivariant Interatomic Potential)
- 引擎: `nequip`
- 需要模型文件: PyTorch `.pth`
- 配置格式: Hydra YAML
- 特点: E(3)-等变图神经网络，支持编译训练和推理
- ASE集成: `NequIPCalculator`
- LAMMPS集成: `pair_style nequip/allegro`
- 参考: Batzner et al., Nature Communications 13, 2453 (2022)

### Allegro
- 引擎: NequIP框架扩展包 (`nequip-allegro`)
- 需要模型文件: PyTorch `.pth`
- 配置格式: Hydra YAML (与NequIP相同)
- 特点: 严格局部等变架构，支持Kokkos加速和MPI
- 参考: Musaelian et al., Nature Communications 14, 579 (2023)

### ACE (Atomic Cluster Expansion)
- 引擎: Julia (`ACEpotentials.jl`)
- 需要模型文件: JSON
- 训练数据格式: Extended XYZ
- 特点: 体序展开的系统可改进方法
- 依赖: ACE1.jl, ACEfit.jl, ExtXYZ.jl, Polynomials4ML.jl
- 参考: Witt et al., J. Chem. Phys. 159, 164101 (2023)

### CHGNet
- 引擎: `chgnet`
- 需要模型文件: 是
- 晶体图神经网络

### M3GNet
- 引擎: `m3gnet`
- 需要模型文件: 是
- 材料图网络

### SevenNet
- 引擎: `sevenn`
- 需要模型文件: 是

### ORB
- 引擎: `orb`
- 需要模型文件: 是

### MALA (Materials Learning Algorithms)
- 引擎: Python (`mala`包)
- 特点: DFT计算的ML代理模型，非势函数方法
- 集成: Quantum ESPRESSO
- 参考: Computer Physics Communications (2025)

## 模型对比 / Model Comparison

| 模型 | 语言 | 等变性 | 体序 | 主动学习 | LAMMPS |
|------|------|--------|------|---------|--------|
| DPA | Python/C++ | 部分 | 无限 | 否 | pair_deepmd |
| MACE | Python | E(3) | 有界 | 是 | pair_mace |
| NEP | C++/CUDA | 部分 | 有界 | 否 | GPUMD |
| MTP | C++ | 无 | 有界 | 是 (MaxVol) | pair_mlip |
| NequIP | Python | E(3) | 有界 | 否 | pair_nequip |
| Allegro | Python | E(3) | 有界 | 否 | pair_nequip |
| ACE | Julia | SO(3) | 有界 | 否 | LAMMPS ML-IAP |

## 诊断代码 / Diagnostic Codes

- **MLIP-E082**: `mlip.manifest.missing_model` - manifest缺少必需的'model'键
- **MLIP-E082** (warning): 未知MLIP模型名称

## 相关文件 / Related Files

- `raw/assets/matmaster_rules.py` - 模型族定义
- `raw/assets/mlip-readme.md` - 各MLIP项目README合集
- `raw/assets/mtp-documentation.md` - MTP文档
- `raw/assets/mlip-cli-reference.md` - CLI工具参考
- `wiki/entities/MLIP_Manifest.md` - 模型在manifest中的使用
