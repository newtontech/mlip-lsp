# 诊断代码参考 / Diagnostic Codes Reference

## 完整代码列表 / Complete Code List

### MLIP-E080: mlip.json.invalid
- **类别**: syntax
- **严重性**: error
- **消息**: JSON manifest cannot be parsed: {detail}
- **触发条件**: JSON解析失败
- **置信度**: 0.95
- **修复建议**: fix_json_syntax

### MLIP-E081: mlip.yaml.invalid
- **类别**: syntax
- **严重性**: error
- **消息**: YAML manifest cannot be parsed: {detail}
- **触发条件**: YAML解析失败
- **置信度**: 0.95
- **修复建议**: fix_yaml_syntax

### MLIP-E082: mlip.manifest.missing_model
- **类别**: schema
- **严重性**: error
- **消息**: manifest is missing required key 'model'
- **触发条件**: manifest缺少model键
- **置信度**: 0.9
- **修复建议**: add_json_key

### MLIP-E082 (warning): mlip.manifest.unknown_model
- **类别**: schema
- **严重性**: warning
- **消息**: unknown MLIP model '{model}'; known models: {list}
- **触发条件**: 模型名称不在已知列表中
- **置信度**: 0.7
- **修复建议**: check_model_name

### MLIP-E083: mlip.manifest.missing_task
- **类别**: schema
- **严重性**: error
- **消息**: manifest is missing required key 'task'
- **触发条件**: manifest缺少task键
- **置信度**: 0.9
- **修复建议**: add_json_key

### MLIP-E083 (warning): mlip.manifest.unknown_task
- **类别**: schema
- **严重性**: warning
- **消息**: unknown task type '{task}'; valid types: {list}
- **触发条件**: 任务类型不在有效列表中
- **置信度**: 0.7
- **修复建议**: check_task_type

### MLIP-E083 (warning): mlip.manifest.missing_task_parameter
- **类别**: schema
- **严重性**: warning
- **消息**: task '{task}' recommends parameter '{param}' which is not set
- **触发条件**: 任务缺少推荐参数
- **置信度**: 0.65
- **修复建议**: add_parameter

### MLIP-E084: mlip.manifest.missing_structure
- **类别**: schema
- **严重性**: error
- **消息**: manifest is missing required key 'structure'
- **触发条件**: manifest缺少structure键
- **置信度**: 0.9
- **修复建议**: add_json_key

### MLIP-E084 (warning): mlip.manifest.invalid_structure_extension
- **类别**: schema
- **严重性**: warning
- **消息**: structure file '{path}' has unsupported extension '{ext}'; expected one of: {list}
- **触发条件**: 结构文件扩展名不支持
- **置信度**: 0.6
- **修复建议**: check_structure_extension

### MLIP-W080: mlip.python.missing_ase_import
- **类别**: schema
- **严重性**: warning
- **消息**: expected import or symbol 'ase' was not found
- **触发条件**: Python脚本缺少ASE导入
- **置信度**: 0.75
- **修复建议**: add_import

### MLIP-E085: mlip.python.missing_structure_symbol
- **类别**: schema
- **严重性**: error
- **消息**: expected workflow symbol 'structure' was not found
- **触发条件**: Python脚本缺少structure符号
- **置信度**: 0.68
- **修复建议**: add_symbol

### MLIP-E086: mlip.files.missing_path_reference
- **类别**: cross-file reference
- **严重性**: warning
- **消息**: manifest references file '{path}' which does not exist
- **触发条件**: 引用的文件不存在
- **置信度**: 0.7-0.8
- **修复建议**: create_missing_file

### MLIP-E087: mlip.log.traceback
- **类别**: preflight/runtime-risk
- **严重性**: error
- **消息**: runtime log contains a Python traceback starting at line {line}
- **触发条件**: 日志包含Python traceback
- **置信度**: 0.95
- **修复建议**: investigate_traceback

## 置信度分级 / Confidence Levels

| 分级 | 范围 | 含义 |
|------|------|------|
| 高 | 0.9-1.0 | 确定性的错误 |
| 中 | 0.6-0.9 | 可能的问题 |
| 低 | 0.0-0.6 | 不确定的建议 |

## 修复建议类型 / Fix Suggestion Types

| 类型 | 描述 | 适用代码 |
|------|------|----------|
| fix_json_syntax | 修复JSON语法 | MLIP-E080 |
| fix_yaml_syntax | 修复YAML语法 | MLIP-E081 |
| add_json_key | 添加JSON键 | MLIP-E082/E083/E084 |
| add_import | 添加Python导入 | MLIP-W080 |
| add_symbol | 添加Python符号 | MLIP-E085 |
| add_parameter | 添加任务参数 | MLIP-E083 |
| add_required_token | 添加必需token | MLIP-101 |
| check_model_name | 检查模型名称 | MLIP-E082 |
| check_task_type | 检查任务类型 | MLIP-E083 |
| check_structure_extension | 检查结构扩展名 | MLIP-E084 |
| check_keyword_spelling | 检查关键字拼写 | MLIP-001 |
| create_missing_file | 创建缺失文件 | MLIP-E086 |
| investigate_traceback | 调查traceback | MLIP-E087 |

## 相关文件 / Related Files

- `raw/assets/diagnostic_codes.py` - 完整规则定义
- `wiki/concepts/Diagnostic_System.md` - 诊断系统概述
