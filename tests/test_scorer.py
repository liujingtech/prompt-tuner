"""评分引擎单元测试"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import OutputParser
from src.scorer import OutputScorer


class TestOutputScorer:
    """评分引擎测试"""

    @pytest.fixture
    def scorer(self):
        return OutputScorer()

    @pytest.fixture
    def sample_output(self):
        return """【思考】分析通知，进行分级筛选【思考】
【TTS】您有待审批工作。账户有支出变动。另有社交生活类通知多条【TTS】
<show>一级重要通知
企业微信 待审批申请需处理
企业微信 会议即将开始提醒
短信 尾号5090账户支出413元

二级重要通知
微信 家庭群个人私信多条
QQ 个人私信群聊消息多条
美团 外卖接单与送达通知
淘宝 包裹派送中

三级通知
营销类 优惠促销优惠券多条
娱乐类 游戏群同学群消息多条
系统类 存储空间不足提醒</show>"""

    def test_parse_output(self, sample_output):
        """测试输出解析"""
        parsed = OutputParser.parse(sample_output)

        assert parsed.has_think_tag
        assert parsed.has_tts_tag
        assert parsed.has_show_tag
        assert "分级" in parsed.think
        assert "待审批" in parsed.tts
        assert "一级" in parsed.show

    def test_score_output(self, scorer, sample_output):
        """测试输出评分"""
        parsed = OutputParser.parse(sample_output)
        result = scorer.score(parsed, [])

        assert result.total_score > 0
        assert "format" in result.dimensions
        assert "content" in result.dimensions
        assert "classification" in result.dimensions
        assert "tts" in result.dimensions
        assert "show" in result.dimensions

    def test_perfect_output(self, scorer):
        """测试完美输出应该得高分"""
        perfect_output = """【思考】按规则分级筛选去重【思考】
【TTS】您有待审批工作。账户有支出变动。另有社交生活类通知多条【TTS】
<show>一级重要通知
企业微信 待审批申请需处理
短信 账户支出413元

二级重要通知
微信 个人私信多条
美团 外卖通知

三级通知
营销类 促销优惠多条</show>"""

        parsed = OutputParser.parse(perfect_output)
        result = scorer.score(parsed, [])

        assert result.total_score >= 80

    def test_missing_tags(self, scorer):
        """测试缺少标签应该扣分"""
        bad_output = "这是一段没有标签的输出"

        parsed = OutputParser.parse(bad_output)
        result = scorer.score(parsed, [])

        assert result.dimensions["format"].score < 20
        assert not result.passed

    def test_tts_too_long(self, scorer):
        """测试TTS过长应该扣分"""
        long_tts_output = """【思考】分析通知【思考】
【TTS】""" + "这是一句话。" * 20 + """【TTS】
<show>测试内容</show>"""

        parsed = OutputParser.parse(long_tts_output)
        result = scorer.score(parsed, [])

        assert result.dimensions["tts"].score < 20


class TestOutputParser:
    """解析器测试"""

    def test_extract_tts_sentences(self):
        """测试TTS句子提取"""
        tts = "这是第一句。这是第二句！这是第三句？"
        sentences = OutputParser.extract_tts_sentences(tts)

        assert len(sentences) == 3
        assert "第一句" in sentences[0]

    def test_extract_show_items(self):
        """测试SHOW条目提取"""
        show = "第一行\n第二行\n第三行"
        items = OutputParser.extract_show_items(show)

        assert len(items) == 3
        assert items[0] == "第一行"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
