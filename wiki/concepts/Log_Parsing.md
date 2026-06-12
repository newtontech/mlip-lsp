# 日志解析 / Log Parsing

## 概述 / Overview

mlip-lsp包含一个运行时日志解析器，用于检测MLIP工作流日志中的Python traceback和其他运行时错误。

## 解析能力 / Parsing Capabilities

### Traceback检测
- **诊断代码**: MLIP-E087
- **严重性**: error
- **模式**: `^Traceback \(most recent call last\)`
- **类别**: preflight/runtime-risk

### 错误行提取
- **模式**: `^(\w+Error|Exception): (.+)$`
- **提取内容**: 错误类型和错误消息

## TracebackBlock结构

```python
@dataclass(frozen=True)
class TracebackBlock:
    start_line: int       # Traceback起始行号
    error_type: str       # 错误类型（如RuntimeError）
    error_message: str    # 错误消息
```

## 示例日志 / Example Log

```
Starting MLIP calculation...
Traceback (most recent call last):
  File "run.py", line 5, in <module>
    calc = MLIPCalculator(model='bad')
RuntimeError: Model not found
Done.
```

## 诊断输出 / Diagnostic Output

对于上面的示例日志，解析器产生：

```json
{
  "code": "MLIP-E087",
  "severity": "error",
  "message": "runtime log contains a Python traceback (RuntimeError: Model not found) starting at line 2",
  "file": "path/to/log.log",
  "line": 2,
  "evidence": ["Traceback detected: RuntimeError: Model not found"],
  "suggested_fix": {
    "kind": "investigate_traceback",
    "error_type": "RuntimeError",
    "error_message": "Model not found"
  },
  "confidence": 0.95
}
```

## 支持的文件格式 / Supported Formats

- `.log` - 运行时日志文件

## 相关文件 / Related Files

- `raw/assets/traceback.log` - 示例日志文件
- `src/mlip_lsp/features/log_parser.py` - 解析器实现
