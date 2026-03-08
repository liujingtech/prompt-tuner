"""报告生成器"""
from datetime import datetime
from typing import List, Dict, Any
import json
import os
from src.scorer import ScoringResult
from src.parser import ParsedOutput


class Reporter:
    """报告生成器 - 生成测试报告"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_iteration_result(
        self,
        model_name: str,
        iteration: int,
        system_prompt: str,
        user_prompt: str,
        raw_output: str,
        parsed: ParsedOutput,
        score: ScoringResult,
        notifications_count: int,
        response_time: float = 0.0
    ):
        """保存单次迭代结果"""
        timestamp = datetime.now().isoformat()

        result = {
            "timestamp": timestamp,
            "model": model_name,
            "iteration": iteration,
            "score": score.total_score,
            "passed": score.passed,
            "response_time": response_time,
            "summary": score.summary,
            "dimensions": {
                name: {
                    "score": dim.score,
                    "issues": dim.issues
                }
                for name, dim in score.dimensions.items()
            },
            "notifications_count": notifications_count,
            "prompts": {
                "system_length": len(system_prompt),
                "user_length": len(user_prompt)
            },
            "output": {
                "raw_length": len(raw_output),
                "think": parsed.think[:200] if parsed.think else "",
                "tts": parsed.tts[:200] if parsed.tts else "",
                "show": parsed.show[:500] if parsed.show else ""
            }
        }

        # 追加到JSONL文件
        filepath = os.path.join(self.output_dir, "results.jsonl")
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    def generate_final_report(
        self,
        best_result: Dict[str, Any],
        total_iterations: int,
        total_time_seconds: float,
        model_results: Dict[str, List]
    ) -> str:
        """生成最终报告

        Returns:
            Markdown格式的报告内容
        """
        report = f"""# 提示词调优报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 总体概况

- 总迭代次数: {total_iterations}
- 总运行时间: {total_time_seconds / 60:.1f} 分钟
- 最佳分数: {best_result.get('score', 0):.1f}/100
- 最佳模型: {best_result.get('model', 'N/A')}

## 各模型表现

"""
        for model_name, results in model_results.items():
            if results:
                best_score = max(r['score'] for r in results)
                avg_score = sum(r['score'] for r in results) / len(results)
                pass_count = sum(1 for r in results if r['passed'])
                report += f"""### {model_name}

- 最高分: {best_score:.1f}
- 平均分: {avg_score:.1f}
- 通过次数: {pass_count}/{len(results)}
"""
            else:
                report += f"### {model_name}\n\n- 无测试结果\n"

        report += f"""
## 最佳提示词

```
{best_result.get('system_prompt', 'N/A')[:1000]}...
```

## 优化历史

"""
        for i, step in enumerate(best_result.get('optimization_history', [])[:5], 1):
            report += f"{i}. 分数: {step.get('score', 0):.1f} - {', '.join(step.get('issues', [])[:3])}\n"

        report += "\n---\n\n*报告由 Prompt Tuner 自动生成*\n"

        # 保存报告
        report_path = os.path.join(self.output_dir, "final_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        # 同时保存最佳结果JSON
        best_path = os.path.join(self.output_dir, "best_result.json")
        with open(best_path, "w", encoding="utf-8") as f:
            json.dump(best_result, f, ensure_ascii=False, indent=2)

        return report
