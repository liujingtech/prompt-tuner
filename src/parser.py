"""模型输出解析器"""
from dataclasses import dataclass
from typing import List
import re


@dataclass
class ParsedOutput:
    """解析后的输出"""
    think: str
    tts: str
    show: str
    raw: str
    has_think_tag: bool
    has_tts_tag: bool
    has_show_tag: bool
    extra_content: str  # 标签外的额外内容


class OutputParser:
    """输出解析器 - 解析【思考】...【思考】...【TTS】...【TTS】...<show>...</show>格式"""

    # 正则表达式模式
    THINK_PATTERN = re.compile(r'【思考】(.*?)【思考】', re.DOTALL)
    TTS_PATTERN = re.compile(r'【TTS】(.*?)【TTS】', re.DOTALL)
    SHOW_PATTERN = re.compile(r'<show>(.*?)</show>', re.DOTALL)
    SHOW_OPEN_PATTERN = re.compile(r'<show>', re.DOTALL)

    @classmethod
    def parse(cls, content: str) -> ParsedOutput:
        """解析模型输出

        Args:
            content: 模型原始输出

        Returns:
            解析后的输出对象
        """
        think_match = cls.THINK_PATTERN.search(content)
        tts_match = cls.TTS_PATTERN.search(content)
        show_match = cls.SHOW_PATTERN.search(content)

        think = think_match.group(1).strip() if think_match else ""
        tts = tts_match.group(1).strip() if tts_match else ""
        show = show_match.group(1).strip() if show_match else ""

        # 如果没有找到闭合的<show>标签，尝试从开始标签提取到末尾
        has_show_tag = show_match is not None
        show_open_match = None
        if not show_match:
            show_open_match = cls.SHOW_OPEN_PATTERN.search(content)
            if show_open_match:
                show = content[show_open_match.end():].strip()
                has_show_tag = True

        # 检测额外内容（标签外的内容）
        cleaned = content
        if think_match:
            cleaned = cleaned.replace(think_match.group(0), "")
        if tts_match:
            cleaned = cleaned.replace(tts_match.group(0), "")
        if show_match:
            cleaned = cleaned.replace(show_match.group(0), "")
        elif show_open_match:
            cleaned = cleaned[:show_open_match.start()]
        extra_content = cleaned.strip()

        return ParsedOutput(
            think=think,
            tts=tts,
            show=show,
            raw=content,
            has_think_tag=think_match is not None,
            has_tts_tag=tts_match is not None,
            has_show_tag=has_show_tag,
            extra_content=extra_content
        )

    @classmethod
    def extract_tts_sentences(cls, tts: str) -> List[str]:
        """从TTS内容提取句子列表

        Args:
            tts: TTS内容

        Returns:
            句子列表
        """
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？.!?]', tts)
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def count_sentences(cls, tts: str) -> int:
        """统计TTS句子数量

        Args:
            tts: TTS内容

        Returns:
            句子数量
        """
        return len(cls.extract_tts_sentences(tts))

    @classmethod
    def extract_show_items(cls, show: str) -> List[str]:
        """从SHOW内容提取条目列表

        Args:
            show: SHOW内容

        Returns:
            条目列表
        """
        # 按换行分割
        items = show.split('\n')
        return [item.strip() for item in items if item.strip()]
