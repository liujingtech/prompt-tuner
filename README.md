# Prompt Tuner

车载通知汇总提示词自动调优工具

## 功能

- **多模型测试**: 支持同时测试多个智谱模型 (GLM-4-Flash, GLM-5, etc.)
- **自动评分**: 从5个维度评估输出质量（格式、内容、分级、TTS、SHOW）
- **自动优化**: 根据评分结果自动调整提示词
- **详细报告**: 生成完整的Markdown测试报告

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

编辑 `config.json`，添加您的智谱 API Key:

```json
{
  "models": [
    {
      "name": "GLM-4-Flash",
      "api_key": "YOUR_API_KEY_HERE",
      "base_url": "https://open.bigmodel.cn/api/paas/v4"
    }
  ]
}
```

### 3. 运行

```bash
python run.py config.json
```

## 配置说明

```json
{
  "models": [...],           // 模型列表
  "scoring": {
    "total_score": 85.0,      // 总分阈值
    "dimension_score": 15.0,   // 各维度阈值
    "consecutive_passes": 3,   // 连续通过次数
    "max_iterations": 50,      // 每个模型最大迭代次数
    "max_runtime_hours": 2.0   // 最大运行时间
  },
  "output_dir": "output"      // 输出目录
}
```

## 评分维度

| 维度 | 分值 | 检查项 |
|------|------|--------|
| 格式正确性 | 20 | 标签完整、无额外内容 |
| 内容合规性 | 20 | 无markdown、无特殊符号、无英文 |
| 分级准确性 | 20 | 一级/二级/三级分类正确 |
| TTS约束 | 20 | 不超过15句、单句不超过30字、三级不播报 |
| SHOW约束 | 20 | 按优先级排序、单条不超过20字、无重复 |

**通过条件**:
- 总分 >= 85
- 各维度 >= 15
- 连续3次测试通过

## 输出文件

- `output/results.jsonl` - 每次测试的详细结果（JSONL格式）
- `output/best_result.json` - 最佳配置
- `output/final_report.md` - 完整的Markdown报告

## 测试

```bash
python tests/test_basic.py
```

## 项目结构

```
/agent
├── src/
│   ├── config.py           # 配置管理
│   ├── client.py           # API客户端
│   ├── parser.py           # 输出解析
│   ├── scorer.py           # 评分引擎
│   ├── optimizer.py        # 提示词优化
│   ├── reporter.py         # 报告生成
│   ├── tuner.py            # 主控制器
│   └── data_generator.py   # 测试数据生成
├── tests/
│   └── test_basic.py       # 基础测试
├── config.json             # 配置文件
├── run.py                  # 入口
└── requirements.txt        # 依赖
```

## 注意事项

1. 配置文件中的 `api_key` 需要替换为实际值
2. 运行时间可能较长，建议在后台运行
3. 如需手动停止，按 `Ctrl+C` 中断
4. 首次运行会创建 `output/` 目录

## License

MIT
