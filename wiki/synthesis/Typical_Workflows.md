# 典型工作流 / Typical Workflows

## 静态分析工作流 / Static Analysis Workflow

### 1. 基本诊断检查
```bash
# 分析整个案例目录
mlip-lint ./case --json
```

**输出**: JSON格式的诊断列表

### 2. 单文件分析
```python
from pathlib import Path
from mlip_lsp.analyzer import analyze_file

diagnostics = analyze_file(Path("input.json"))
for diag in diagnostics:
    print(f"{diag.code}: {diag.message}")
```

### 3. LSP集成
```bash
# 在编辑器中启动LSP
mlip-lsp --stdio
```

**功能**:
- 实时语法检查
- 自动完成
- 悬停文档
- 快速修复

## 格式化工作流 / Formatting Workflow

### 1. 安全格式化
```bash
# 格式化JSON/YAML文件
mlip-fmt -w input.json
mlip-fmt -w config.yaml
```

**保证**:
- 永不破坏文件
- 保持幂等性
- 保留尾随换行符

### 2. Python格式化
```python
from mlip_lsp.features.formatter import safe_format

with open("input.json") as f:
    content = f.read()
formatted = safe_format(content, ".json")

with open("input.json", "w") as f:
    f.write(formatted)
```

## 验证工作流 / Validation Workflow

### 1. Manifest验证
```python
from mlip_lsp.features.matmaster import validate_manifest_structure
import json

with open("manifest.json") as f:
    manifest = json.load(f)

diagnostics = validate_manifest_structure(manifest, "manifest.json")
if diagnostics:
    print("Validation failed:")
    for diag in diagnostics:
        print(f"  {diag.severity}: {diag.message}")
```

### 2. 完整案例检查
```bash
# 运行静态测试
mlip-test static ./case --json
```

## 开发工作流 / Development Workflow

### 1. 安装开发依赖
```bash
python -m pip install -e ".[dev]"
```

### 2. 运行测试
```bash
pytest
```

### 3. 代码质量检查
```bash
# 格式化
make format
# 或
ruff format src tests

# Lint
make lint
# 或
ruff check src tests

# 类型检查
make typecheck
# 或
mypy src
```

### 4. 完整本地检查
```bash
make check
```

## 错误修复工作流 / Error Fix Workflow

### 1. 使用LSP快速修复
在支持LSP的编辑器中：
1. 打开manifest文件
2. 点击诊断
3. 选择"快速修复"
4. 应用建议的修复

### 2. 使用CLI诊断
```bash
mlip-lint ./case --json | jq '.[] | select(.code == "MLIP-E082")'
```

### 3. Python脚本修复
```python
from pathlib import Path
from mlip_lsp.analyzer import analyze_path

diagnostics = analyze_path(Path("./case"))
error_diags = [d for d in diagnostics if d.severity == "error"]

for diag in error_diags:
    if diag.suggested_fix:
        kind = diag.suggested_fix.get("kind")
        if kind == "add_json_key":
            key = diag.suggested_fix.get("key")
            print(f"Add key '{key}' to {diag.file}")
```

## 日志分析工作流 / Log Analysis Workflow

### 1. 解析运行时日志
```python
from mlip_lsp.features.log_parser import log_diagnostics

with open("simulation.log") as f:
    content = f.read()

diagnostics = log_diagnostics(content, "simulation.log")
for diag in diagnostics:
    print(f"Line {diag.line}: {diag.message}")
```

### 2. 检测traceback
```bash
# 使用CLI
mlip-lint simulation.log --json
```

## 代理工作流 / Agent Workflow

### 1. 检查操作
```bash
mlip-lsp-tool check path/to/input --format json
```

### 2. 完成操作
```bash
mlip-lsp-tool complete path/to/input --format json
```

### 3. 悬停操作
```bash
mlip-lsp-tool hover path/to/input --format json
```

### 4. 修复操作
```bash
mlip-lsp-tool fix path/to/input --format json
```

## 相关文件 / Related Files

- `raw/assets/README.md` - 项目概述
- `wiki/synthesis/API_Reference.md` - API文档
