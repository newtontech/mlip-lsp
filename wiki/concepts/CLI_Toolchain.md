# CLI 工具链 / CLI Toolchain

## 概述 / Overview

mlip-lsp提供了一组命令行工具，用于诊断、格式化和测试MLIP工作流文件。

## 可用命令 / Available Commands

### mlip-lsp
**用途**: 启动LSP服务器

```bash
mlip-lsp --stdio
```

**用途**: 与IDE集成，提供实时诊断、完成、悬停和格式化

### mlip-lint
**用途**: 静态分析和诊断

```bash
mlip-lint ./case --json
```

**输出格式**:
- `file`: 文件路径
- `line`: 行号
- `column`: 列号
- `severity`: 严重性 (error/warning)
- `code`: 诊断代码
- `message`: 错误消息
- `evidence`: 证据列表
- `suggested_fix`: 修复建议
- `confidence`: 置信度

### mlip-fmt
**用途**: 安全格式化文件

```bash
mlip-fmt -w input.file
```

**选项**:
- `-w`: 就地写入文件
- 支持: `.json`, `.yaml`, `.yml`, `.txt`

### mlip-test
**用途**: 静态测试和验证

```bash
mlip-test static ./case --json
```

**功能**: 运行静态分析并返回结构化测试结果

### mlip-lsp-tool
**用途**: 代理友好的工具接口

```bash
mlip-lsp-tool check path/to/input --format json
mlip-lsp-tool context path/to/input --format json
mlip-lsp-tool complete path/to/input --format json
mlip-lsp-tool hover path/to/input --format json
mlip-lsp-tool symbols path/to/input --format json
mlip-lsp-tool fix path/to/input --format json
```

**操作**:
- `check`: 运行诊断检查
- `context`: 获取文档上下文
- `complete`: 获取完成项
- `hover`: 获取悬停信息
- `symbols`: 获取符号列表
- `fix`: 应用自动修复

## 诊断形状约定 / Diagnostic Shape Convention

所有工具使用共享的newtontech LSP诊断形状，确保工具链间的一致性。

## 相关文件 / Related Files

- `raw/assets/README.md` - CLI工具概述
- `src/mlip_lsp/cli.py` - CLI入口点实现
