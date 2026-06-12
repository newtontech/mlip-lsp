# NEP 配置文件 / NEP Configuration

## 定义 / Definition

NEP（Neuroevolution Potential）配置文件是用于训练GPUMD引擎神经进化势函数的文本格式配置文件。

## 典型配置项 / Typical Configuration Items

### 训练参数
- `generation`: 训练代数（如: 200000）
- `population`: 种群大小（如: 50）
- `batch`: 批次大小（如: 10）

### 网络结构
- `neuron`: 神经元数量（如: 30）
- `cutoff`: 截断半径（如: 5.0）

### 正则化
- `lambda_1`: 正则化参数1（如: 0.1）
- `lambda_2`: 正则化参数2（如: 0.1）

## 示例配置 / Example Configuration

```
# NEP training configuration
generation     200000
population     50
batch          10
neuron         30
cutoff         5.0
lambda_1       0.1
lambda_2       0.1
```

## 格式特点 / Format Characteristics

- 使用键值对格式
- 支持对齐格式化（键左对齐24字符）
- 支持`#`、`!`、`;`开头的注释行

## LSP支持 / LSP Support

mlip-lsp支持对NEP配置文件的：
- 格式化（对齐键值对）
- 基本文本分析

## 相关文件 / Related Files

- `raw/assets/nep_config.txt` - NEP配置示例
- `wiki/entities/MLIP_Models.md` - NEP模型信息
