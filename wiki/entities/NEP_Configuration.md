# NEP 配置文件 / NEP Configuration

## 定义 / Definition

NEP（Neuroevolution Potential）配置文件 (`nep.in`) 用于训练GPUMD引擎的神经进化势函数。支持NEP3和NEP4版本。

Source: https://gpumd.org/nep/input_files/nep_in.html

## 文件格式 / File Format

- 空行和以 `#` 开头的行被忽略
- 参数行格式: `keyword parameter_1 parameter_2 ...`
- 关键字可按任意顺序出现（`type_weight` 必须在 `type` 之后）
- `type` 是必需关键字，其他有默认值

## 完整参数参考 / Complete Parameter Reference

### 必需参数

| 关键字 | 描述 |
|--------|------|
| `type` | 原子类型数量和化学元素列表（必需） |

### 模型参数

| 关键字 | 默认值 | 描述 |
|--------|--------|------|
| `version` | 4 | NEP版本 (3 或 4) |
| `model_type` | 0 | 0=势函数, 1=偶极矩, 2=极化率 |
| `charge_mode` | - | 势函数模型的电荷模式 |
| `prediction` | - | 训练或预测（推理）模式 |
| `zbl` | - | ZBL普适排斥势外截断距离 |
| `use_typewise_cutoff_zbl` | - | 为ZBL部分启用类型截断 |

### 描述符参数

| 关键字 | 默认值 | 描述 |
|--------|--------|------|
| `cutoff` | 8 4 | 径向和角度截断距离 |
| `n_max` | 4 4 | 径向和角度基的大小 |
| `basis_size` | 8 8 | 径向和角度基函数数量 |
| `l_max` | 4 2 0 | 角度项的展开阶数 |
| `neuron` | 30 | 隐藏层神经元数量 |

### 损失函数参数

| 关键字 | 默认值 | 描述 |
|--------|--------|------|
| `lambda_1` | - | L1正则化权重 |
| `lambda_2` | - | L2正则化权重 |
| `lambda_e` | 1.0 | 能量损失权重 |
| `lambda_f` | 1.0 | 力损失权重 |
| `lambda_v` | 0.1 | 维里损失权重 |
| `lambda_q` | - | 电荷损失权重 |
| `lambda_z` | - | 偶极矩损失权重 |
| `lambda_shear` | - | 剪切应力损失权重 |
| `force_delta` | - | 使小力更准确的偏置项 |
| `atomic_v` | - | 原子或全局维里拟合 |

### 训练参数

| 关键字 | 默认值 | 描述 |
|--------|--------|------|
| `batch` | 1000 | 训练批次大小 |
| `population` | 50 | SNES算法种群大小 |
| `generation` | 100000 | SNES算法代数 |

### 其他参数

| 关键字 | 描述 |
|--------|------|
| `save_potential` | 定期保存势函数 |
| `output_descriptor` | 输出描述符值 |
| `fine_tune` | 从已有模型微调 |
| `type_weight` | 不同原子类型的力权重 |

## 示例配置 / Example Configuration

### 完整示例（所有默认值）
```
type        2 Te Pb       # 必需关键字
version     4              # NEP版本
cutoff      8 4            # 径向和角度截断
n_max       4 4            # 基大小
basis_size  8 8            # 基函数数量
l_max       4 2 0          # 角度展开阶数
neuron      30             # 隐藏层神经元
lambda_e    1.0            # 能量权重
lambda_f    1.0            # 力权重
lambda_v    0.1            # 维里权重
batch       1000           # 批次大小
population  50             # 种群大小
generation  100000         # 训练代数
```

### 带ZBL排斥势的示例
```
type        1 Si
version     4
zbl         1.0 2.0
cutoff      5 5
n_max       4 4
basis_size  8 8
l_max       4 2 0
neuron      30
batch       1000
population  50
generation  100000
```

### 预测（推理）模式
```
type        2 Te Pb
version     4
prediction  1
```

## 训练数据格式 / Training Data Format

- `train.xyz` — 训练数据集 (Extended XYZ格式，必需)
- `test.xyz` — 测试数据集 (Extended XYZ格式，可选)

## 输出文件 / Output Files

- `nep.txt` — 训练好的NEP模型
- `nep.restart` — 重启文件
- `loss.out` — 训练损失日志

## 格式特点 / Format Characteristics

- 使用键值对格式
- 支持对齐格式化（键左对齐）
- 支持 `#` 开头的注释行

## LSP支持 / LSP Support

mlip-lsp支持对NEP配置文件的：
- 格式化（对齐键值对）
- 关键字补全
- 参数值验证
- 悬停文档

## 相关文件 / Related Files

- `raw/assets/nep_config.txt` - NEP配置示例
- `raw/assets/mlip-input-format.md` - 输入格式完整参考
- `raw/assets/mlip-examples.md` - NEP训练示例
- `wiki/entities/MLIP_Models.md` - NEP模型信息
