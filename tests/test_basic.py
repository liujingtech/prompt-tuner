"""基础测试 - 不依赖pytest"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import OutputParser
from src.scorer import OutputScorer


def test_parse_output():
    """测试输出解析"""
    sample_output = """【思考】分析通知，进行分级筛选【思考】
【TTS】您有待审批工作【TTS】
<show>一级重要通知
企业微信 待审批申请</show>"""

    parsed = OutputParser.parse(sample_output)

    assert parsed.has_think_tag, "缺少思考标签"
    assert parsed.has_tts_tag, "缺少TTS标签"
    assert parsed.has_show_tag, "缺少SHOW标签"
    assert "分级" in parsed.think, "思考内容不正确"
    print("✓ test_parse_output passed")


def test_score_output():
    """测试输出评分"""
    sample_output = """【思考】分析通知【思考】
【TTS】您有待审批工作【TTS】
<show>企业微信 待审批申请</show>"""

    scorer = OutputScorer()
    parsed = OutputParser.parse(sample_output)
    result = scorer.score(parsed, [])

    assert result.total_score > 0, "分数应大于0"
    assert "format" in result.dimensions, "缺少format维度"
    print(f"✓ test_score_output passed (score: {result.total_score})")


def test_missing_tags():
    """测试缺少标签"""
    bad_output = "这是一段没有标签的输出"

    scorer = OutputScorer()
    parsed = OutputParser.parse(bad_output)
    result = scorer.score(parsed, [])

    assert result.dimensions["format"].score < 20, "缺少标签应扣分"
    print(f"✓ test_missing_tags passed (format score: {result.dimensions['format'].score})")


def test_extract_sentences():
    """测试句子提取"""
    tts = "这是第一句。这是第二句！这是第三句？"
    sentences = OutputParser.extract_tts_sentences(tts)

    assert len(sentences) == 3, f"应提取3个句子，实际: {len(sentences)}"
    print(f"✓ test_extract_sentences passed ({len(sentences)} sentences)")


def run_all():
    """运行所有测试"""
    print("Running tests...\n")

    test_parse_output()
    test_score_output()
    test_missing_tags()
    test_extract_sentences()

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    run_all()
