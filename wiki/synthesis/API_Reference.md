# API 参考 / API Reference

## 核心API / Core API

### analyze_path(path: Path) -> list[Diagnostic]
分析目录或文件路径，返回所有MLIP诊断。

**参数**:
- `path`: 目录或文件的Path对象

**返回**: 按文件、行号和代码排序的诊断列表

**示例**:
```python
from pathlib import Path
from mlip_lsp.analyzer import analyze_path

diagnostics = analyze_path(Path("./case"))
```

### analyze_file(path: Path) -> list[Diagnostic]
分析单个文件，返回该文件的MLIP诊断。

**支持的文件类型**:
- `.json` - JSON manifest
- `.yaml`, `.yml` - YAML manifest
- `.py` - Python ASE脚本
- `.log` - 运行时日志
- `.txt` - 文本配置（NEP等）

### validate_manifest_structure(manifest: dict, file_path: str) -> list[Diagnostic]
验证解析后的manifest是否符合MatMaster执行约定。

**验证项**:
- 必需字段存在性
- 模型名称有效性
- 任务类型有效性
- 任务参数完整性
- 结构文件扩展名

## LSP服务器API / LSP Server API

### create_server() -> MLIPServer
创建并返回MLIPServer实例。

```python
from mlip_lsp.server import create_server

server = create_server()
```

### MLIPServer.compute_diagnostics(uri: str, content: str) -> list[Diagnostic]
计算文档内容的诊断。

### MLIPServer.complete(uri: str, content: str, line: int, character: int) -> list[dict]
计算给定位置的完成项。

### MLIPServer.hover(uri: str, content: str, line: int, character: int) -> str | None
计算给定位置的悬停信息。

### MLIPServer.format(content: str) -> str
格式化文档内容。

## 诊断API / Diagnostic API

### Diagnostic数据类
```python
@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    file: str
    line: int
    column: int = 1
    evidence: list[str] = field(default_factory=list)
    suggested_fix: dict[str, Any] | None = None
    confidence: float = 1.0
```

### get_rule(code: str) -> Rule | None
按代码查找诊断规则。

### format_message(code: str, **kwargs) -> str
格式化规则的消息模板。

## 格式化API / Formatting API

### safe_format(text: str, file_suffix: str) -> str
根据文件类型分派格式化，永不抛出。

### format_json(text: str) -> str
格式化JSON文本。

### format_yaml(text: str) -> str
格式化YAML文本。

### format_text(text: str) -> str
格式化文本配置（NEP等）。

### is_idempotent(text: str, file_suffix: str) -> bool
检查格式化是否幂等。

## 日志解析API / Log Parsing API

### parse_log(content: str) -> list[TracebackBlock]
从日志内容中提取所有traceback块。

### log_diagnostics(content: str, file_path: str) -> list[Diagnostic]
为运行时日志文件产生诊断。

## 相关文件 / Related Files

- `raw/assets/analyzer.py` - 分析器API
- `raw/assets/diagnostic_codes.py` - 诊断规则API
- `raw/assets/matmaster_rules.py` - MatMaster验证API
