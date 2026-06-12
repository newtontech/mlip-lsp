# MLIP 模型族 / MLIP Model Families

## 定义 / Definition

机器学习原子间势（Machine Learning Interatomic Potentials, MLIP）模型是用机器学习方法训练的原子间势函数，用于替代传统的DFT计算，在保持较高精度的同时大幅提升计算速度。

## 已支持的模型 / Supported Models

### DPA (Deep Potential - Atom)
- **DPA3.1-3M**: DeepMD模型，3M参数规模
- **DPA2**: Deep Potential Architecture 第二代
- 引擎: `dp`
- 需要模型文件: 是

### MACE (Multi-Atomic Cluster Expansion)
- 引擎: `mace`
- 需要模型文件: 是
- 特点: 高阶不变性原子间势

### NEP (Neuroevolution Potential)
- 引擎: `gpumd`
- 需要模型文件: 是
- 用于GPUMD分子动力学模拟

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
- 第七代势函数网络

### ORB
- 引擎: `orb`
- 需要模型文件: 是

## 诊断代码 / Diagnostic Codes

- **MLIP-E082**: `mlip.manifest.missing_model` - manifest缺少必需的'model'键
- **MLIP-E082** (warning): 未知MLIP模型名称

## 相关文件 / Related Files

- `raw/assets/matmaster_rules.py` - 模型族定义
- `wiki/entities/MLIP_Manifest.md` - 模型在manifest中的使用
