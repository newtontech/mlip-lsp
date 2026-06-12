# MTP 文档 / MTP Documentation

## 定义 / Definition

矩张量势（Moment Tensor Potential, MTP）是由Skoltech Alexander Shapeev团队开发的系统可改进的原子间势方法。MLIP包实现了MTP的训练、主动学习和MPI并行计算。

Source: https://gitlab.com/ashapeev/mlip-2, https://mlip.skoltech.ru/

## CLI 工具 (mlp)

### train — 训练势函数
```bash
mlp train potential.mtp train.cfg [options]
```
| 选项 | 描述 |
|------|------|
| `--max-iter=<int>` | 最大训练迭代次数 |
| `--trained-pot-name=<file>` | 输出势函数文件 |
| `--curr-pot-name=<file>` | 输入势函数文件 |
| `--energy-weight=<double>` | 能量损失权重 |
| `--force-weight=<double>` | 力损失权重 |
| `--stress-weight=<double>` | 应力损失权重 |

### calc-grade — 计算MaxVol评分
```bash
mlp calc-grade curr.mtp train.cfg train.cfg temp.cfg --nbh-weight=0.0 --energy-weight=1.0
```

### relax — 弛豫结构
```bash
mlp relax mlip.ini --force-tolerance=1e-3 --cfg-filename=catalog.cfg
```

### select-add — 主动学习选择
```bash
mlp select-add curr.mtp train.cfg selected.cfg diff.cfg --select-threshold=3.0
```

## 文件格式

| 格式 | 扩展名 | 用途 |
|------|--------|------|
| MTP势函数 | `.mtp` | 训练参数 |
| 训练数据 | `.cfg` | 原子结构+从头算数据 |
| 配置 | `mlip.ini` | MLIP运行配置 |

## 主动学习工作流

1. 初始化小训练集 (`train.cfg`)
2. 训练: `mlp train curr.mtp train.cfg`
3. 计算评分: `mlp calc-grade`
4. 弛豫候选结构: `mlp relax`
5. 选择新结构: `mlp select-add`
6. 从头算计算选中结构
7. 添加到训练集，重复步骤2

## 数学背景

MTP使用体序展开的矩张量描述符，系统捕获多体相互作用。关键参数：
- `levmax`: 最大级别（体序）
- `NQ`: 径向基函数数量

## 参考 / References

- Shapeev, Multiscale Modeling & Simulation 14(3), 1153-1173 (2016)
- Novikov et al., Mach. Learn.: Sci. Technol. 2, 025002 (2021)

## 相关文件 / Related Files

- `raw/assets/mtp-documentation.md` - MTP完整文档
- `raw/assets/mlip-cli-reference.md` - CLI参考
- `wiki/entities/MLIP_Models.md` - MTP模型信息
