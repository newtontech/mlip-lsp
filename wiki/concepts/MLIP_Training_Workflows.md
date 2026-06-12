# MLIP 训练工作流 / MLIP Training Workflows

## 定义 / Definition

不同的MLIP框架有不同的训练工作流。本页面总结各框架的典型训练流程和最佳实践。

## 通用训练流程 / General Training Pipeline

1. **数据准备**: 从DFT计算收集训练数据（能量、力、应力）
2. **数据格式化**: 转换为目标框架的输入格式
3. **模型配置**: 设置模型架构和超参数
4. **训练**: 运行训练算法
5. **验证**: 在测试集上评估模型精度
6. **部署**: 导出模型用于模拟

---

## MACE 训练工作流

### 基本训练
```bash
mace_run_train \
    --name="MACE_model" \
    --train_file="train.xyz" \
    --valid_fraction=0.05 \
    --model="MACE" \
    --hidden_irreps='128x0e + 128x1o' \
    --r_max=5.0 \
    --batch_size=10 \
    --max_num_epochs=1500 \
    --device=cuda
```

### 微调基础模型
```bash
mace_run_train \
    --foundation_model="small" \
    --train_file="train.xyz" \
    --E0s="average" \
    --lr=0.01 \
    --max_num_epochs=6
```

### 最佳实践
- 推荐 `hidden_irreps='256x0e'` 或 `'128x0e + 128x1o'`
- 精度不足时可增加通道数或阶数
- 梯度更新总量建议保持约200,000次
- 使用 `--stage_two` 可降低能量误差

---

## NEP 训练工作流

### 配置 nep.in
```
type        2 Te Pb
version     4
cutoff      8 4
neuron      30
batch       1000
population  50
generation  100000
```

### 运行训练
```bash
nep  # 自动读取 nep.in，需要 train.xyz
```

### 最佳实践
- 核心超参数: `l_max`, `num_layers`, `neuron`
- l_max: 1=快, 2=更准确, 3=最准确但慢
- batch_size 可设为整个数据集大小

---

## MTP (MLIP-2) 主动学习工作流

### 循环流程
```bash
# 1. 训练
mlp train curr.mtp train.cfg --max-iter=500 --force-weight=5e-3

# 2. 评估
mlp calc-grade curr.mtp train.cfg train.cfg temp.cfg

# 3. 弛豫
mlp relax mlip.ini --cfg-filename=catalog.cfg

# 4. 选择
mlp select-add curr.mtp train.cfg selected.cfg diff.cfg --select-threshold=3.0

# 5. DFT计算 + 添加到训练集
# 6. 重复
```

---

## DeePMD-kit 训练工作流

### 流程
```bash
# 1. 准备数据 (dpdata转换)
# 2. 训练
dp train input.json
# 3. 冻结模型
dp freeze -o graph.pb
# 4. 压缩 (可选, 4-15x加速)
dp compress -i graph.pb -o compressed.pb
# 5. 测试
dp test -m graph.pb -s data/
```

---

## NequIP/Allegro 训练工作流

### 配置 YAML
使用Hydra格式YAML配置文件，定义数据、训练器、模型等。

### 命令
```bash
nequip-train config.yaml          # 训练
nequip-evaluate config.yaml       # 评估
nequip-deploy build config.yaml   # 部署
```

---

## ASE 集成 / ASE Integration

所有主要MLIP框架都提供ASE计算器接口：

```python
from ase import Atoms, build
from ase.optimize import BFGS

# MACE
from mace.calculators import mace_mp
calc = mace_mp(model="medium", device='cuda')

# DeePMD
from deepmd.DeepPot import DP
calc = DP('model.pb')

# NequIP
from nequip.ase import NequIPCalculator
calc = NequIPCalculator.from_deployed_model("model.pth")

# 通用ASE使用
atoms = build.molecule('H2O')
atoms.calc = calc
opt = BFGS(atoms)
opt.run(fmax=0.05)
```

## 相关文件 / Related Files

- `raw/assets/mlip-examples.md` - 详细训练示例
- `raw/assets/mlip-cli-reference.md` - CLI命令参考
- `raw/assets/mlip-input-format.md` - 输入格式参考
- `wiki/entities/MLIP_Models.md` - 模型族对比
