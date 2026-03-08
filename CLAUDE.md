# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

车载通知汇总提示词自动调优工具。根据模型输出质量自动优化提示词，支持多模型对比测试。

**输出格式:**
```
【思考】{分级逻辑，≤30字}【思考】
【TTS】{语音播报内容，≤15句，每句≤30字}【TTS】
<show>{屏幕显示内容，按优先级排序，单条≤20字}</show>
```

---

## 架构

数据流向: `run.py` → `PromptTuner` → `ZhipuClient` → `OutputParser` → `OutputScorer`

| 模块 | 职责 |
|------|------|
| `tuner.py` | 主控制器，按模型迭代运行测试 |
| `client.py` | 智谱API客户端（OpenAI兼容格式） |
| `parser.py` | 解析【思考】【TTS】<show>标签 |
| `scorer.py` | 5维度评分引擎（各20分，总分100） |
| `optimizer.py` | 基于评分结果优化提示词 |
| `data_generator.py` | 生成模拟通知测试数据 |
| `reporter.py` | 生成JSONL和Markdown报告 |

---

## 命令

```bash
# 运行调优
python3 run.py config.json

# 运行所有测试
python3 -m pytest tests/ -v

# 运行单个测试
python3 tests/test_basic.py
```

**输出文件:**
- `output/results.jsonl` - 每次测试详情
- `output/best_result.json` - 最佳配置和提示词
- `output/final_report.md` - 完整报告

---

## 评分标准

| 维度 | 满分 | 通过阈值 |
|------|:----:|:--------:|
| 格式正确性 | 20 | ≥15 |
| 内容合规性 | 20 | ≥15 |
| 分级准确性 | 20 | ≥15 |
| TTS约束 | 20 | ≥15 |
| SHOW约束 | 20 | ≥15 |
| **总分** | **100** | **≥85** |

通过条件: 总分≥85 且 各维度≥15 且 连续3次通过

---

## 通知分级规则

**一级（TTS全量播报，SHOW置顶）:** 工作、财务、安全类
**二级（TTS仅汇总条数，SHOW二级展示）:** 社交、生活、出行类
**三级（仅SHOW展示，禁止TTS）:** 营销、娱乐、系统类

---

## 注意事项

- **宽松标签匹配**: 若输出缺少`</show>`闭合标签，解析器会从`<show>`提取到内容末尾
- **分类关键词**: 评分器使用`scorer.py`中的`LEVEL1/2/3_KEYWORDS`字典判断通知级别
- **推荐模型**: GLM-4-Flash稳定得分99/100，GLM-Z1-Flash格式问题较多，不推荐使用

---

## 配置

编辑`config.json`:
- `models`: 模型列表（name, api_key, base_url）
- `scoring`: 收敛参数（total_score, dimension_score, consecutive_passes, max_iterations）
- `output_dir`: 输出目录

可用模型: GLM-4-Flash, GLM-4.5-Air, GLM-Z1-Flash 等
