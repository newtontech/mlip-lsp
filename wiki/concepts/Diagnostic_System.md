# 诊断系统 / Diagnostic System

## 概述 / Overview

mlip-lsp实现了一个基于newtontech科学LSP诊断约定的诊断系统，受python-lsp-server的provider模型启发。

## 严重性策略 / Severity Policy

### error
- **定义**: 高置信度的语法、模式、类型/值或引用问题
- **行为**: 应阻止自动提交，因为上游运行时可能拒绝输入
- **示例**: JSON语法错误、缺少必需字段

### warning
- **定义**: 高风险或可疑输入
- **行为**: 应显示给代理，但不自动阻止修复循环
- **示例**: 引用的文件不存在、未知模型名称

### information / hint
- **定义**: 样式、文档或可选优化事实
- **当前状态**: MVP版本中主要使用error和warning

## 诊断分类 / Diagnostic Categories

1. **syntax** - 语法错误（JSON/YAML解析失败）
2. **schema** - 模式验证（缺少必需字段）
3. **type/value** - 类型和值检查
4. **cross-file reference** - 跨文件引用验证
5. **semantic consistency** - 语义一致性
6. **preflight/runtime-risk** - 运行时风险检查
7. **style/deprecation** - 样式和弃用警告

## 富诊断形状 / Rich Diagnostic Shape

每个代理面向的诊断必须包含：

```json
{
  "code": "STABLE_CODE",
  "severity": "error",
  "category": "schema",
  "confidence": 1.0,
  "source": "mlip-lsp",
  "range": {
    "start": {"line": 0, "character": 0},
    "end": {"line": 0, "character": 1}
  },
  "software": "mlip",
  "file_type": "input",
  "path": "input",
  "expected": null,
  "actual": null,
  "manual_ref": null,
  "fix_hints": [],
  "blocking": true
}
```

## 诊断代码分配 / Diagnostic Code Assignment

所有MLIP诊断使用`MLIP-`前缀：

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

## 置信度评分 / Confidence Scoring

诊断包含置信度分数（0.0-1.0），用于：
- 优先级排序
- 代理决策
- 修复建议的可靠性

## 相关文件 / Related Files

- `raw/assets/diagnostic_codes.py` - 完整诊断规则表
- `docs/DIAGNOSTIC_ENGINE_V1.md` - 诊断引擎文档
