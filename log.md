# 变更日志 / Change Log

## 2026-06-13

### Issue #29 closeout / 问题#29收尾

**Created by**: dmux Worker D (Cursor Agent)
**Purpose**: Complete upstream doc gaps, cross-references, wiki lint, and LSP capability grounding

#### 原始证据 / Raw evidence
- `upstream-sources.md` — Official MLIP ecosystem source manifest
- `examples/manifest_md.json` — MD task manifest with temperature/steps parameters

#### LSP / Agent updates
- `lsp-capabilities.json` — Added `llmWiki` block with operation hints and example inputs
- `raw/assets/manifest.json` — Checksum-backed provenance manifest (#34)
- `wiki/synthesis/openqc-agent-context.md` — Wiki/raw grounding table for agent operations
- `scripts/check-llm-wiki.sh` — Lightweight index and capability path validation

#### CI repair
- `src/mlip_lsp/tool.py` — Fix ruff E501 line length in fallback capabilities JSON

#### 导航 / Navigation
- `index.md` — upstream manifest, openqc-agent-context, diagnostic-engine-v1 links
- `wiki/entities/MLIP_Manifest.md` — Cross-link to MD manifest example

---

## 2025-06-12

### 新增 / Added

#### 知识库初始化 / Knowledge Base Initialization
- 创建LLM Wiki目录结构
  - `raw/assets/` - 原始源证据文件
  - `wiki/entities/` - 领域实体页面
  - `wiki/concepts/` - 跨领域概念页面
  - `wiki/synthesis/` - API参考和工作流页面
  - `index.md` - 导航中心
  - `log.md` - 本变更日志

#### 实体页面 / Entity Pages (6)
- `MLIP_Models.md` - MLIP模型族（DPA, MACE, NEP等）
- `MLIP_Manifest.md` - 清单文件结构和必需字段
- `MLIP_Task_Types.md` - 任务类型（optimize, md, static等）
- `ASE_Atomistic_Simulation.md` - ASE原子模拟环境
- `Structure_File_Formats.md` - 结构文件格式（CIF, XYZ, POSCAR等）
- `NEP_Configuration.md` - NEP配置文件格式

#### 概念页面 / Concept Pages (6)
- `Diagnostic_System.md` - 诊断系统和严重性策略
- `Language_Server_Protocol.md` - LSP实现和特性
- `MatMaster_Execution_Contract.md` - MatMaster执行约定
- `Log_Parsing.md` - 日志解析和traceback检测
- `Safe_Formatting.md` - 安全格式化保证
- `CLI_Toolchain.md` - CLI工具和命令

#### 综合页面 / Synthesis Pages (4)
- `API_Reference.md` - 完整Python API文档
- `Input_Format_Reference.md` - 所有支持文件格式参考
- `Typical_Workflows.md` - 静态分析、格式化、验证工作流
- `Diagnostic_Codes_Reference.md` - 诊断代码完整列表

#### 原始证据文件 / Raw Evidence Files (7)
- `analyzer.py` - 分析器核心逻辑提取
- `diagnostic_codes.py` - 诊断规则表提取
- `matmaster_rules.py` - MatMaster执行规则提取
- `valid_manifest.json` - 有效JSON manifest示例
- `valid_ase_script.py` - 有效Python ASE脚本示例
- `nep_config.txt` - NEP配置示例
- `README.md` - 项目概述

### 统计 / Statistics

- **总页面数**: 17
- **实体页面**: 6
- **概念页面**: 6
- **综合页面**: 4
- **原始证据**: 7
- **导航文件**: 2

### 格式约定 / Format Conventions

- 使用双语格式（中文标题，英文术语）
- 每个页面包含相关文件链接
- 诊断代码包含置信度和修复建议
- API文档包含类型签名
- 工作流包含实际命令示例

## 未来改进 / Future Improvements

- [ ] 添加更多MLIP模型详细文档
- [ ] 扩展Python脚本验证规则
- [ ] 添加Bohrium集成文档
- [ ] 创建OpenQC集成示例
- [ ] 添加性能分析工作流
- [ ] 添加NEP配置文件的关键字补全支持
- [ ] 添加MTP .cfg文件的语法高亮
- [ ] 添加MACE YAML配置的LSP支持
- [ ] 添加DeePMD-kit JSON配置的验证

## 2026-06-12

### 新增 / Added

#### MLIP生态文档收集 / MLIP Ecosystem Documentation Collection

##### 原始证据文件 / Raw Evidence Files (5 new)
- `mlip-readme.md` — NequIP, Allegro, MACE, DeePMD-kit, ACE, MALA README合集
- `mtp-documentation.md` — MLIP-2/MTP完整文档（CLI命令、文件格式、主动学习）
- `mlip-input-format.md` — NEP nep.in, MTP .mtp/.cfg, MACE YAML, DeePMD-kit JSON, NequIP YAML, ACE Julia格式
- `mlip-examples.md` — 各框架训练脚本和ASE集成示例
- `mlip-cli-reference.md` — mlp, mace_run_train, dp, nequip-train, nep CLI命令参考

##### 实体页面 / Entity Pages (1 new)
- `MTP_Documentation.md` — 矩张量势MLIP-2包文档、CLI命令和主动学习工作流

##### 概念页面 / Concept Pages (1 new)
- `MLIP_Training_Workflows.md` — 各MLIP框架的典型训练流程和最佳实践

##### 更新页面 / Updated Pages (3)
- `MLIP_Models.md` — 扩展为完整模型对比（DPA, MACE, NEP, MTP, NequIP, Allegro, ACE, MALA）
- `NEP_Configuration.md` — 添加完整nep.in参数参考（30+参数）
- `Input_Format_Reference.md` — 添加各框架特定格式（MTP, DeePMD-kit, MACE, NequIP, ACE）

##### 导航更新 / Navigation Updates
- `index.md` — 添加新页面链接、MLIP框架外部链接、扩展目录结构
- `log.md` — 本更新

### 统计 / Statistics

- **总页面数**: 19 (+2)
- **实体页面**: 7 (+1)
- **概念页面**: 7 (+1)
- **综合页面**: 4
- **原始证据**: 12 (+5)
- **导航文件**: 2
