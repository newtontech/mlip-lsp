# LLM Wiki 知识库计划 / LLM Wiki Knowledge Base Plan

## 概述 / Overview

为mlip-lsp项目创建Karpathy风格的LLM Wiki知识库，提供MLIP领域的原始证据和综合知识的双向链接。

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
│   └── README.md             # 项目概述
├── wiki/
│   ├── entities/         # MLIP领域实体 (6个页面)
│   ├── concepts/         # 跨领域概念 (6个页面)
│   └── synthesis/        # API参考和工作流 (4个页面)
├── index.md              # 导航中心
└── log.md                # 变更日志
```

## 内容计划 / Content Plan

### 原始证据文件 (7个)
- 分析器核心逻辑提取
- 诊断规则表提取
- MatMaster执行规则提取
- 有效示例文件
- 项目概述

### 实体页面 (6个)
1. MLIP_Models.md - 模型族（DPA, MACE, NEP等）
2. MLIP_Manifest.md - 清单文件结构
3. MLIP_Task_Types.md - 任务类型和参数
4. ASE_Atomistic_Simulation.md - ASE集成
5. Structure_File_Formats.md - 结构文件格式
6. NEP_Configuration.md - NEP配置格式

### 概念页面 (6个)
1. Diagnostic_System.md - 诊断系统
2. Language_Server_Protocol.md - LSP实现
3. MatMaster_Execution_Contract.md - 执行约定
4. Log_Parsing.md - 日志解析
5. Safe_Formatting.md - 安全格式化
6. CLI_Toolchain.md - CLI工具链

### 综合页面 (4个)
1. API_Reference.md - Python API文档
2. Input_Format_Reference.md - 输入格式参考
3. Typical_Workflows.md - 典型工作流
4. Diagnostic_Codes_Reference.md - 诊断代码参考

## 格式约定 / Format Conventions

- 双语格式（中文标题，英文术语）
- 每个页面包含相关文件链接
- 诊断代码包含置信度和修复建议
- API文档包含类型签名
- 工作流包含实际命令示例

## 完成标准 / Completion Criteria

- [x] 创建目录结构
- [x] 复制原始证据文件
- [x] 创建6个实体页面
- [x] 创建6个概念页面
- [x] 创建4个综合页面
- [x] 创建index.md导航中心
- [x] 创建log.md变更日志
- [ ] Git提交和PR
- [ ] 自动合并

## 统计 / Statistics

- **总页面数**: 17 (目标15-25个)
- **实体页面**: 6
- **概念页面**: 6
- **综合页面**: 4
- **原始证据**: 7
- **导航文件**: 2
