# MLIP-LSP 知识库 / MLIP-LSP Knowledge Base

## 概述 / Overview

mlip-lsp是为MatMaster MLIP工作流设计的语言服务器协议和CLI工具包。本知识库使用Karpathy风格的LLM Wiki模式组织，提供原始证据和综合知识的双向链接。

## 目录结构 / Directory Structure

```
mlip-lsp/
├── raw/assets/           # 原始源证据文件
│   ├── analyzer.py      # 分析器核心逻辑
│   ├── diagnostic_codes.py  # 诊断规则表
│   ├── matmaster_rules.py   # MatMaster约定
│   ├── valid_manifest.json  # 有效清单示例
│   ├── valid_ase_script.py   # 有效Python示例
│   ├── nep_config.txt        # NEP配置示例
│   ├── README.md             # 项目概述
│   ├── mlip-readme.md        # 各MLIP项目README合集
│   ├── mtp-documentation.md  # MTP完整文档
│   ├── mlip-input-format.md  # 输入文件格式参考
│   ├── mlip-examples.md      # 训练脚本和示例
│   ├── mlip-cli-reference.md # CLI工具参考
│   ├── upstream-sources.md   # 官方上游来源清单
│   └── examples/manifest_md.json  # MD任务清单示例
├── wiki/
│   ├── entities/         # MLIP领域实体
│   ├── concepts/         # 跨领域概念
│   └── synthesis/        # API参考和工作流
├── index.md              # 本文件
└── log.md                # 变更日志
```

## 实体 / Entities (领域特定概念)

### [MLIP 模型族 / MLIP Model Families](wiki/entities/MLIP_Models.md)
支持的机器学习原子间势模型（DPA, MACE, NEP等）

### [MLIP 清单文件 / MLIP Manifest](wiki/entities/MLIP_Manifest.md)
描述MLIP计算任务的JSON/YAML配置文件

### [MLIP 任务类型 / MLIP Task Types](wiki/entities/MLIP_Task_Types.md)
计算任务类型（optimize, md, static等）及其参数要求

### [ASE 原子模拟环境 / ASE Atomistic Simulation](wiki/entities/ASE_Atomistic_Simulation.md)
Python原子模拟环境及其在MLIP工作流中的角色

### [结构文件格式 / Structure File Formats](wiki/entities/Structure_File_Formats.md)
支持的结构文件格式（CIF, XYZ, POSCAR等）

### [NEP 配置文件 / NEP Configuration](wiki/entities/NEP_Configuration.md)
神经进化势训练配置文件格式（完整nep.in参数参考）

### [MTP 文档 / MTP Documentation](wiki/entities/MTP_Documentation.md)
矩张量势MLIP-2包文档、CLI命令和主动学习工作流

## 概念 / Concepts (跨领域思想)

### [诊断系统 / Diagnostic System](wiki/concepts/Diagnostic_System.md)
基于newtontech约定的诊断系统，包括严重性策略和分类

### [语言服务器协议 / Language Server Protocol](wiki/concepts/Language_Server_Protocol.md)
mlip-lsp的LSP实现，包括完成、悬停、格式化和代码操作

### [MatMaster 执行约定 / MatMaster Execution Contract](wiki/concepts/MatMaster_Execution_Contract.md)
MatMaster期望的manifest结构和验证规则

### [日志解析 / Log Parsing](wiki/concepts/Log_Parsing.md)
运行时日志中的Python traceback检测

### [安全格式化 / Safe Formatting](wiki/concepts/Safe_Formatting.md)
保证永不抛出的文档格式化

### [MLIP 训练工作流 / MLIP Training Workflows](wiki/concepts/MLIP_Training_Workflows.md)
各MLIP框架的典型训练流程和最佳实践

### [CLI 工具链 / CLI Toolchain](wiki/concepts/CLI_Toolchain.md)
命令行工具（mlip-lint, mlip-fmt, mlip-test等）

## 综合 / Synthesis (API和工作流)

### [API 参考 / API Reference](wiki/synthesis/API_Reference.md)
完整的Python API文档

### [输入格式参考 / Input Format Reference](wiki/synthesis/Input_Format_Reference.md)
所有支持文件格式的详细参考

### [典型工作流 / Typical Workflows](wiki/synthesis/Typical_Workflows.md)
静态分析、格式化、验证和开发工作流

### [诊断代码参考 / Diagnostic Codes Reference](wiki/synthesis/Diagnostic_Codes_Reference.md)
所有诊断代码及其修复建议的完整列表

### [OpenQC Agent Context](wiki/synthesis/openqc-agent-context.md)
OpenQC agent CLI 与 wiki/raw 证据的映射

### [Diagnostic Engine v1](wiki/concepts/diagnostic-engine-v1.md)
DiagnosticEnvelope/v1 严重性与 blocking 策略

## 快速开始 / Quick Start

### 静态分析
```bash
mlip-lint ./case --json
```

### 格式化
```bash
mlip-fmt -w input.json
```

### LSP集成
```bash
mlip-lsp --stdio
```

## 关键诊断代码 / Key Diagnostic Codes

| 代码 | 名称 | 严重性 |
|------|------|--------|
| MLIP-E080 | mlip.json.invalid | error |
| MLIP-E081 | mlip.yaml.invalid | error |
| MLIP-E082 | mlip.manifest.missing_model | error |
| MLIP-E083 | mlip.manifest.missing_task | error |
| MLIP-E084 | mlip.manifest.missing_structure | error |
| MLIP-W080 | mlip.python.missing_ase_import | warning |
| MLIP-E085 | mlip.python.missing_structure_symbol | error |
| MLIP-E086 | mlip.files.missing_path_reference | warning |
| MLIP-E087 | mlip.log.traceback | error |

## 外部链接 / External Links

- [项目README](raw/assets/README.md)
- [MLIP生态README合集](raw/assets/mlip-readme.md) — NequIP, Allegro, MACE, DeePMD-kit, ACE, MALA
- [MTP文档](raw/assets/mtp-documentation.md) — Moment Tensor Potential完整文档
- [输入格式参考](raw/assets/mlip-input-format.md) — NEP, MTP, MACE, DeePMD-kit, NequIP, ACE格式
- [训练示例](raw/assets/mlip-examples.md) — 各框架训练脚本
- [CLI参考](raw/assets/mlip-cli-reference.md) — mlp, mace_run_train, dp, nequip-train, nep命令
- [上游来源清单](raw/assets/upstream-sources.md) — 官方文档与示例索引
- [诊断引擎文档](docs/DIAGNOSTIC_ENGINE_V1.md)
- [原始源代码](https://github.com/newtontech/mlip-lsp)

### MLIP框架链接 / MLIP Framework Links
- [NequIP](https://github.com/mir-group/nequip) — E(3)-equivariant interatomic potentials
- [Allegro](https://github.com/mir-group/allegro) — Local equivariant representations
- [MACE](https://github.com/acesuit/mace) — Higher order equivariant message passing
- [DeePMD-kit](https://github.com/deepmodeling/deepmd-kit) — Deep Potential models
- [ACEpotentials.jl](https://github.com/ACEsuit/ACEpotentials.jl) — Atomic Cluster Expansion (Julia)
- [MLIP-2 (MTP)](https://gitlab.com/ashapeev/mlip-2) — Moment Tensor Potentials
- [GPUMD/NEP](https://gpumd.org/) — Neuroevolution Potentials
- [MALA](https://github.com/mala-project/mala) — Materials Learning Algorithms

## 变更历史 / Change History

参见 [log.md](log.md) 获取详细变更记录。

运行 `bash scripts/check-llm-wiki.sh` 可验证 wiki 导航链接。
