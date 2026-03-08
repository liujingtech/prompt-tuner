"""提示词优化器"""
from typing import List, Dict, Tuple
import re
from src.scorer import ScoringResult


class PromptOptimizer:
    """提示词优化器 - 根据评分结果自动优化提示词"""

    # 优化策略映射
    STRATEGIES = {
        "format_error": [
            "强化格式约束：在提示词开头明确说明输出格式",
            "增加格式示例：在提示词中添加完整的正确输出示例",
            "添加格式检查提醒：在提示词末尾强调必须严格遵循格式"
        ],
        "english_output": [
            "添加禁止英文规则：明确说明输出必须全部使用中文",
            "强调中文输出：在多个位置重复强调使用中文"
        ],
        "extra_content": [
            "添加禁止多余内容规则：明确禁止输出标签外的任何内容",
            "强化结束标记：说明遇到</show>后必须立即停止输出"
        ],
        "classification_error": [
            "补充分级示例：为每个级别添加更多具体示例",
            "明确边界规则：说明边界模糊时应该如何处理"
        ],
        "tts_too_long": [
            "强化句数限制：将最大句数限制写得更明确",
            "添加简洁示例：提供简洁TTS输出的示例"
        ],
        "tts_level3": [
            "明确三级禁止播报规则",
            "添加三级过滤示例"
        ],
        "show_unstructured": [
            "强化结构化格式要求",
            "添加完整的SHOW格式示例"
        ]
    }

    def __init__(self, initial_system_prompt: str, initial_user_prompt: str):
        self.system_prompt = initial_system_prompt
        self.user_prompt = initial_user_prompt
        self.optimization_history: List[Dict] = []

    def optimize(self, result: ScoringResult) -> Tuple[str, str]:
        """根据评分结果优化提示词

        Args:
            result: 评分结果

        Returns:
            (optimized_system_prompt, optimized_user_prompt)
        """
        optimizations = []

        # 分析问题并收集优化策略
        for dim_name, dim_score in result.dimensions.items():
            if dim_score.score < 15:
                issues = dim_score.issues
                for issue in issues:
                    strategy = self._get_strategy_for_issue(issue)
                    if strategy:
                        optimizations.append(strategy)

        # 去重
        optimizations = list(dict.fromkeys(optimizations))

        if not optimizations:
            # 没有明确的优化方向，使用通用优化
            optimizations.append("强化所有约束：在提示词中更明确地强调所有规则")

        # 记录优化历史
        self.optimization_history.append({
            "score": result.total_score,
            "issues": [issue for dim in result.dimensions.values() for issue in dim.issues],
            "optimizations": optimizations
        })

        # 应用优化
        optimized_system = self._apply_optimizations(self.system_prompt, optimizations)
        self.system_prompt = optimized_system

        return optimized_system, self.user_prompt

    def _get_strategy_for_issue(self, issue: str) -> str:
        """根据问题获取优化策略"""
        issue_lower = issue.lower()

        if "标签" in issue_lower or "格式" in issue_lower:
            return self.STRATEGIES["format_error"][0]
        elif "英文" in issue_lower:
            return self.STRATEGIES["english_output"][0]
        elif "额外" in issue_lower or "标签外" in issue_lower:
            return self.STRATEGIES["extra_content"][0]
        elif "分级" in issue_lower or "级别" in issue_lower:
            return self.STRATEGIES["classification_error"][0]
        elif "句子" in issue_lower or "超标" in issue_lower:
            return self.STRATEGIES["tts_too_long"][0]
        elif "三级" in issue_lower and "tts" in issue_lower:
            return self.STRATEGIES["tts_level3"][0]
        elif "结构" in issue_lower:
            return self.STRATEGIES["show_unstructured"][0]

        return ""

    def _apply_optimizations(self, prompt: str, optimizations: List[str]) -> str:
        """应用优化到提示词"""
        # 在提示词开头添加强调
        emphasis = "\n\n【重要提醒 - 本次优化重点】\n"
        for i, opt in enumerate(optimizations[:3], 1):  # 最多显示3个
            emphasis += f"{i}. {opt}\n"

        # 将强调插入到提示词开头
        if "【重要提醒" in prompt:
            # 替换现有的提醒
            prompt = re.sub(r'【重要提醒.*?(?=\n\n)', emphasis, prompt, flags=re.DOTALL)
        else:
            # 添加新的提醒
            prompt = emphasis + "\n" + prompt

        return prompt

    def get_history(self) -> List[Dict]:
        """获取优化历史"""
        return self.optimization_history
