"""输出评分引擎"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
import re
from src.parser import ParsedOutput, OutputParser


@dataclass
class DimensionScore:
    """单个维度评分"""
    name: str
    score: float  # 0-20
    max_score: float = 20.0
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringResult:
    """评分结果"""
    total_score: float  # 0-100
    dimensions: Dict[str, DimensionScore]
    passed: bool
    summary: str


class OutputScorer:
    """输出评分引擎"""

    # 分级关键词
    LEVEL1_KEYWORDS = {
        "work": ["待审批", "会议", "任务", "截止", "工作"],
        "finance": ["账户", "支出", "收入", "还款", "支付", "银行"],
        "security": ["异常登录", "安全", "违章", "警告"]
    }

    LEVEL2_KEYWORDS = {
        "social": ["微信", "QQ", "群", "私信", "家人"],
        "life": ["快递", "外卖", "取件", "缴费"],
        "travel": ["行程", "停车", "限行", "导航"]
    }

    LEVEL3_KEYWORDS = {
        "marketing": ["促销", "优惠", "广告", "活动", "优惠券"],
        "entertainment": ["游戏", "视频", "音乐", "热点"],
        "system": ["存储", "更新", "验证码"]
    }

    def __init__(self):
        pass

    def score(self, parsed: ParsedOutput, notifications: list) -> ScoringResult:
        """对解析后的输出进行评分

        Args:
            parsed: 解析后的输出
            notifications: 原始通知列表（用于验证分级准确性）

        Returns:
            评分结果
        """
        dimensions = {}

        # 1. 格式正确性 (20分)
        dimensions["format"] = self._score_format(parsed)

        # 2. 内容合规性 (20分)
        dimensions["content"] = self._score_content(parsed)

        # 3. 分级准确性 (20分)
        dimensions["classification"] = self._score_classification(parsed, notifications)

        # 4. TTS约束 (20分)
        dimensions["tts"] = self._score_tts(parsed)

        # 5. SHOW约束 (20分)
        dimensions["show"] = self._score_show(parsed)

        # 计算总分
        total = sum(d.score for d in dimensions.values())

        # 判断是否通过
        passed = total >= 85 and all(d.score >= 15 for d in dimensions.values())

        # 生成摘要
        issues = []
        for name, dim in dimensions.items():
            if dim.issues:
                issues.extend(dim.issues)

        summary = f"总分: {total:.1f}/100, "
        if passed:
            summary += "✓ 通过"
        else:
            summary += f"✗ 未通过 - 问题: {'; '.join(issues[:3])}"

        return ScoringResult(
            total_score=total,
            dimensions=dimensions,
            passed=passed,
            summary=summary
        )

    def _score_format(self, parsed: ParsedOutput) -> DimensionScore:
        """评分：格式正确性"""
        issues = []
        score = 20.0

        # 检查标签完整性
        if not parsed.has_think_tag:
            issues.append("缺少【思考】标签")
            score -= 10
        if not parsed.has_tts_tag:
            issues.append("缺少【TTS】标签")
            score -= 10
        if not parsed.has_show_tag:
            issues.append("缺少<show>标签")
            score -= 10

        # 检查额外内容
        if parsed.extra_content and len(parsed.extra_content) > 50:
            issues.append(f"存在标签外内容: {parsed.extra_content[:50]}...")
            score -= min(10, len(parsed.extra_content) / 50)

        return DimensionScore(
            name="格式正确性",
            score=max(0, score),
            issues=issues,
            details={
                "has_think": parsed.has_think_tag,
                "has_tts": parsed.has_tts_tag,
                "has_show": parsed.has_show_tag,
                "extra_content_length": len(parsed.extra_content)
            }
        )

    def _score_content(self, parsed: ParsedOutput) -> DimensionScore:
        """评分：内容合规性"""
        issues = []
        score = 20.0
        content = parsed.raw

        # 检查markdown格式
        if re.search(r'#{1,6}\s', content) or re.search(r'\*{1,2}', content):
            issues.append("使用Markdown格式")
            score -= 5

        # 检查特殊符号/表情
        if re.search(r'[🔥⭐❌✅💡🎯]', content):
            issues.append("使用表情符号")
            score -= 3

        # 检查英文（如果有）
        english_matches = re.findall(r'[a-zA-Z]{3,}', content)
        # 允许常见英文词汇（如app名、品牌等）
        allowed_english = ['app', 'web', 'api', 'gps', 'wifi', 'show', 'tts']
        problematic_english = [w for w in english_matches if w.lower() not in allowed_english]
        if problematic_english:
            issues.append(f"包含英文内容: {', '.join(problematic_english[:5])}")
            score -= min(5, len(problematic_english))

        return DimensionScore(
            name="内容合规性",
            score=max(0, score),
            issues=issues,
            details={
                "has_markdown": bool(re.search(r'#{1,6}\s', content)),
                "has_emoji": bool(re.search(r'[🔥⭐❌✅💡🎯]', content)),
                "english_words": len(english_matches)
            }
        )

    def _score_classification(self, parsed: ParsedOutput, notifications: list) -> DimensionScore:
        """评分：分级准确性"""
        issues = []
        score = 20.0

        # 简化实现：检查输出中是否正确识别了通知类型
        # 实际实现需要更复杂的逻辑
        tts_lower = parsed.tts.lower()
        show_lower = parsed.show.lower()

        # 检查是否有明显的分级标记
        has_level1 = "一级" in parsed.show
        has_level2 = "二级" in parsed.show
        has_level3 = "三级" in parsed.show

        if not (has_level1 or has_level2 or has_level3):
            issues.append("缺少明确的分级标记")
            score -= 5

        return DimensionScore(
            name="分级准确性",
            score=max(0, score),
            issues=issues,
            details={
                "has_level1_mark": has_level1,
                "has_level2_mark": has_level2,
                "has_level3_mark": has_level3
            }
        )

    def _score_tts(self, parsed: ParsedOutput) -> DimensionScore:
        """评分：TTS约束"""
        issues = []
        score = 20.0

        tts = parsed.tts

        # 检查句子数量
        sentences = OutputParser.extract_tts_sentences(tts)
        sentence_count = len(sentences)

        if sentence_count > 15:
            issues.append(f"句子数量超标: {sentence_count}/15")
            score -= min(10, sentence_count - 15)

        # 检查单句长度
        long_sentences = [s for s in sentences if len(s) > 30]
        if long_sentences:
            issues.append(f"存在过长句子: {len(long_sentences)}句超过30字")
            score -= min(5, len(long_sentences))

        # 检查是否包含三级内容（营销词等）
        level3_in_tts = any(kw in tts.lower() for kws in self.LEVEL3_KEYWORDS.values() for kw in kws)
        if level3_in_tts:
            issues.append("TTS中包含三级内容")
            score -= 5

        # 检查口语化程度（简化实现）
        formal_words = ["请注意", "请查收", "敬请期待"]
        for word in formal_words:
            if word in tts:
                issues.append(f"使用书面用语: {word}")
                score -= 2

        return DimensionScore(
            name="TTS约束",
            score=max(0, score),
            issues=issues,
            details={
                "sentence_count": sentence_count,
                "max_sentence_length": max(len(s) for s in sentences) if sentences else 0,
                "avg_sentence_length": sum(len(s) for s in sentences) / len(sentences) if sentences else 0
            }
        )

    def _score_show(self, parsed: ParsedOutput) -> DimensionScore:
        """评分：SHOW约束"""
        issues = []
        score = 20.0

        show = parsed.show
        items = OutputParser.extract_show_items(show)

        # 检查单条长度
        long_items = [item for item in items if len(item) > 20]
        if long_items:
            issues.append(f"存在过长条目: {len(long_items)}条超过20字")
            score -= min(5, len(long_items))

        # 检查是否有明显重复
        for i in range(len(items) - 1):
            if items[i] == items[i + 1]:
                issues.append("存在重复条目")
                score -= 3
                break

        return DimensionScore(
            name="SHOW约束",
            score=max(0, score),
            issues=issues,
            details={
                "item_count": len(items),
                "max_item_length": max(len(item) for item in items) if items else 0
            }
        )
