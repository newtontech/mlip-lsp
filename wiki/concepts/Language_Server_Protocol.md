# 语言服务器协议 / Language Server Protocol

## 概述 / Overview

mlip-lsp基于LSP（Language Server Protocol）实现，使用pygls库提供IDE集成功能。

## 实现特性 / Implemented Features

### TEXT_DOCUMENT_DID_OPEN
- 文档打开时触发诊断
- 计算并发布诊断结果

### TEXT_DOCUMENT_DID_CHANGE
- 文档更改时触发诊断
- 实时反馈错误和警告

### TEXT_DOCUMENT_COMPLETION
- 提供代码自动完成
- 支持manifest键、模型名称、任务类型
- Python导入完成

### TEXT_DOCUMENT_HOVER
- 悬停文档
- 显示键、模型、任务的说明
- Python符号文档

### TEXT_DOCUMENT_FORMATTING
- 文档格式化
- JSON/YAML安全格式化
- 保持幂等性

### TEXT_DOCUMENT_CODE_ACTION
- 快速修复建议
- 添加缺失的JSON/YAML键
- 添加缺失的Python导入
- 添加缺失的符号

## 启动方式 / Startup Methods

### stdio模式（推荐）
```bash
mlip-lsp --stdio
```

### 库模式
```python
from mlip_lsp.server import create_server
server = create_server()
```

## 服务器类 / Server Class

### MLIPServer
- **name**: "mlip-lsp"
- **version**: "0.1.0"
- **后端**: pygls LanguageServer

## 公共API / Public API

```python
# 创建服务器
server = create_server()

# 计算诊断
diagnostics = server.compute_diagnostics(uri, content)

# 获取完成项
items = server.complete(uri, content, line, character)

# 获取悬停信息
info = server.hover(uri, content, line, character)

# 格式化内容
formatted = server.format(content)
```

## 相关文件 / Related Files

- `raw/assets/analyzer.py` - 核心分析逻辑
- `src/mlip_lsp/server.py` - 完整LSP实现
