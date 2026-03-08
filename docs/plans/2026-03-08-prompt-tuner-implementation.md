# Prompt Tuner 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建一个Python CLI工具，自动调优车载通知汇总的提示词，支持多模型测试、质量评分和自动优化循环。

**Architecture:** 模块化设计，主控制器协调数据流；评分引擎从5个维度评估输出质量；优化器根据问题诊断规则自动调整提示词; 报告器生成详细的测试报告。

**Tech Stack:** Python 3.10+, requests, 2.x, 标准库 (json, re, dataclasses)

---

## Task 1: 项目初始化与配置

**Files:**
- Create: `/mnt/d/Code/agent/src/config.py`
- Create: `/mnt/d/Code/agent/requirements.txt`
- Create: `/mnt/d/Code/agent/run.py`

**Step 1: 创建项目结构**

```bash
mkdir -p /mnt/d/Code/agent/src /mnt/d/Code/agent/output /mnt/d/Code/agent/tests
```

**Step 2: 创建依赖文件**

Create `requirements.txt`:
```
requests>=2.28.0
```

**Step 3: 创建配置模块**

Create `src/config.py`:
```python
"""配置管理模块"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json
import os

@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    api_key: str
    base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    max_tokens: int = 3000
    temperature: float = 0.0

@dataclass
class ScoringThreshold:
    """评分阈值配置"""
    total_score: float = 85.0  # 总分阈值
    dimension_score: float = 15.0  # 各维度阈值
    consecutive_passes: int = 3  # 连续通过次数
    max_iterations: int = 50  # 每个模型最大迭代次数
    max_runtime_hours: float = 2.0  # 最大运行时间（小时）

@dataclass
class Config:
    """全局配置"""
    models: List[ModelConfig]
    scoring: ScoringThreshold
    output_dir: str = "output"

    @classmethod
    def load(cls, filepath: str) -> 'Config':
        """从JSON文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        models = [
            ModelConfig(**m) for m in data.get("models", [])
        ]
        scoring = ScoringThreshold(**data.get("scoring", {}))

        return cls(
            models=models,
            scoring=scoring,
            output_dir=data.get("output_dir", "output")
        )

    def save(self, filepath: str):
        """保存配置到JSON文件"""
        data = {
            "models": [
                {
                    "name": m.name,
                    "api_key": m.api_key,
                    "base_url": m.base_url,
                    "max_tokens": m.max_tokens,
                    "temperature": m.temperature
                }
                for m in self.models
            ],
            "scoring": {
                "total_score": self.scoring.total_score,
                "dimension_score": self.scoring.dimension_score,
                "consecutive_passes": self.scoring.consecutive_passes,
                "max_iterations": self.scoring.max_iterations,
                "max_runtime_hours": self.scoring.max_runtime_hours,
            },
            "output_dir": self.output_dir
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

**Step 4: 验证配置模块**

```bash
cd /mnt/d/Code/agent && python -c "from src.config import Config; c = Config('test', {})"
```

Expected: No error

**Step 5: 创建入口文件**

Create `run.py`:
```python
#!/usr/bin/env python3
"""提示词调优工具入口"""
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import Config
from src.tuner import PromptTuner

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = Config.load(config_path)

    tuner = PromptTuner(config)
    tuner.run()

if __name__ == "__main__":
    main()
```

**Step 6: Commit**

```bash
cd /mnt/d/Code/agent && git add requirements.txt src/config.py run.py && git commit -m "feat: init project structure and config module"
```

---

## Task 2: 模拟通知数据生成器

**Files:**
- Create: `/mnt/d/Code/agent/src/data_generator.py`

**Step 1: 创建通知数据模型**

Create `src/data_generator.py`:
```python
"""模拟通知数据生成器 - 移植自AutoGLM项目"""
from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta
import random
import uuid
import json

@dataclass
class MockNotification:
    """模拟通知数据"""
    id: str
    package_name: str
    app_name: str
    title: str
    text: str
    timestamp: int
    category: str  # WECHAT_QQ, WORK_WECHAT, SMS, OTHER

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "packageName": self.package_name,
            "appName": self.app_name,
            "title": self.title,
            "text": self.text,
            "timestamp": self.timestamp,
            "category": self.category
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class NotificationGenerator:
    """通知数据生成器"""

    # 应用配置
    APP_CONFIGS = {
        "WECHAT_QQ": [
            {"package_name": "com.tencent.mm", "app_name": "微信", "senders": ["张三", "李四", "王五", "工作群", "家庭群", "技术交流群"]},
            {"package_name": "com.tencent.mobileqq", "app_name": "QQ", "senders": ["小明", "小红", "同学群", "游戏群"]}
        ],
        "WORK_WECHAT": [
            {"package_name": "com.tencent.wework", "app_name": "企业微信", "senders": ["公司公告", "项目组", "部门群", "周报提醒"]}
        ],
        "SMS": [
            {"package_name": "com.android.messaging", "app_name": "短信", "senders": ["验证码", "物流", "营销", "银行"]}
        ],
        "OTHER": [
            {"package_name": "com.taobao.taobao", "app_name": "淘宝", "senders": ["物流更新", "促销活动"]},
            {"package_name": "com.jingdong.app.mall", "app_name": "京东", "senders": ["订单状态", "优惠券"]},
            {"package_name": "com.sankuai.meituan", "app_name": "美团", "senders": ["外卖状态", "优惠领取"]},
            {"package_name": "com.android.system", "app_name": "系统", "senders": ["存储空间", "系统更新", "安全警告"]}
        ]
    }

    # 消息模板
    MESSAGE_TEMPLATES = {
        "微信": [
            "{sender}: 你好，明天的会议几点开始？",
            "{sender}: 收到，我马上处理",
            "{sender}: [图片]",
            "{sender}: 晚上一起吃饭吗？",
            "{sender}: 文件已发送，请查收",
            "{sender}: 这个问题怎么解决？",
            "{sender}: 周末有空吗？"
        ],
        "QQ": [
            "{sender}: 在吗？",
            "{sender}: 游戏开黑吗？",
            "{sender}: 作业写完了吗？",
            "{sender}: [表情]"
        ],
        "企业微信": [
            "【{sender}】您有一个待审批的申请",
            "【{sender}】会议将于15分钟后开始",
            "【{sender}】本周周报已截止提交",
            "【{sender}】项目进度更新通知",
            "【{sender}】新任务已分配给您"
        ],
        "短信": [
            "【验证码】您的验证码是 {code}，5分钟内有效。",
            "【物流】您的快递已到达{city}转运中心。",
            "【营销】限时优惠！全场5折起，点击查看详情。",
            "【银行】您尾号{account}的账户于{time}支出{amount}元。"
        ],
        "淘宝": [
            "您的包裹正在派送中，预计今日送达",
            "您关注的商品正在降价促销",
            "订单已发货，快递单号: SF{tracking}",
            "您有未使用的优惠券即将过期"
        ],
        "京东": [
            "订单已签收，感谢您的购买",
            "您关注的商品有货了",
            "京东PLUS会员即将到期"
        ],
        "美团": [
            "外卖已送达，祝您用餐愉快",
            "您有新的优惠券可用",
            "商家已接单，正在准备中"
        ],
        "系统": [
            "存储空间不足，请清理不必要的文件",
            "系统更新可用，建议连接WiFi后下载",
            "检测到异常登录，请确认是否为本人操作",
            "电池电量低，请及时充电"
        ]
    }

    def __init__(self, distribution: dict = None):
        """初始化

        Args:
            distribution: 通知分布配置，如 {"WECHAT_QQ": 30, "WORK_WECHAT": 20, "SMS": 30, "OTHER": 20}
        """
        self.distribution = distribution or {
            "WECHAT_QQ": 30,
            "WORK_WECHAT": 20,
            "SMS": 30,
            "OTHER": 20
        }

    def generate(self, count: int = 100) -> List[MockNotification]:
        """生成模拟通知数据

        Args:
            count: 通知总数

        Returns:
            通知列表
        """
        notifications = []
        now = datetime.now()

        for category, percentage in self.distribution.items():
            category_count = int(count * percentage / 100)
            notifications.extend(
                self._generate_for_category(category, category_count, now)
            )

        # 按时间戳排序
        return sorted(notifications, key=lambda x: x.timestamp, reverse=True)

    def _generate_for_category(
        self, category: str, count: int, base_time: datetime
    ) -> List[MockNotification]:
        """为特定类别生成通知"""
        configs = self.APP_CONFIGS.get(category, [])
        if not configs:
            return []

        notifications = []
        for _ in range(count):
            app_config = random.choice(configs)
            sender = random.choice(app_config["senders"])
            templates = self.MESSAGE_TEMPLATES.get(app_config["app_name"], ["来自{app_name}的通知"])
            template = random.choice(templates)

            # 替换模板中的占位符
            message = template.replace("{sender}", sender)
            if "{code}" in message:
                message = message.replace("{code}", str(random.randint(100000, 999999)))
            if "{city}" in message:
                message = message.replace("{city}", random.choice(["北京", "上海", "广州", "深圳"]))
            if "{account}" in message:
                message = message.replace("{account}", str(random.randint(1000, 9999)))
            if "{time}" in message:
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                message = message.replace("{time}", f"{hour}:{minute:02d}")
            if "{amount}" in message:
                message = message.replace("{amount}", str(random.randint(100, 999)))
            if "{tracking}" in message:
                message = message.replace("{tracking}", str(random.randint(100000000, 999999999)))

            notifications.append(MockNotification(
                id=str(uuid.uuid4()),
                package_name=app_config["package_name"],
                app_name=app_config["app_name"],
                title=sender if category != "SMS" and category != "OTHER" else app_config["app_name"],
                text=message,
                timestamp=int((base_time - timedelta(seconds=random.randint(0, 86400)).timestamp() * 1000),
                category=category
            ))

        return notifications

    def to_json_string(self, notifications: List[MockNotification]) -> str:
        """将通知列表转换为JSON字符串"""
        return json.dumps(
            [n.to_dict() for n in notifications],
            ensure_ascii=False,
            indent=2
        )
```

**Step 2: 验证生成器**

```bash
cd /mnt/d/Code/agent && python -c "
from src.data_generator import NotificationGenerator
gen = NotificationGenerator()
notifications = gen.generate(10)
print(f'Generated {len(notifications)} notifications')
for n in notifications[:3]:
    print(f'  [{n.category}] {n.app_name}: {n.title} - {n.text[:30]}...')
"
```

Expected: 输出10条通知，显示前3条摘要

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add src/data_generator.py && git commit -m "feat: add notification data generator"
```

---

## Task 3: API客户端

**Files:**
- Create: `/mnt/d/Code/agent/src/client.py`

**Step 1: 创建API客户端**

Create `src/client.py`:
```python
"""智谱API客户端"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import requests
import json
import time
from src.config import ModelConfig


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    time_to_first_token: Optional[float]
    total_time: Optional[float]
    success: bool
    error: Optional[str] = None


class ZhipuClient:
    """智谱API客户端"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        })

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        stream: bool = False
    ) -> ModelResponse:
        """发送聊天请求

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            stream: 是否使用流式响应

        Returns:
            模型响应
        """
        url = f"{self.config.base_url}/chat/completions"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        payload = {
            "model": self.config.name,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": stream
        }

        start_time = time.time()

        try:
            if stream:
                return self._stream_request(url, payload, start_time)
            else:
                return self._sync_request(url, payload, start_time)
        except Exception as e:
            return ModelResponse(
                content="",
                time_to_first_token=None,
                total_time=time.time() - start_time,
                success=False,
                error=str(e)
            )

    def _sync_request(
        self, url: str, payload: dict, start_time: float
    ) -> ModelResponse:
        """同步请求"""
        response = self.session.post(url, json=payload, timeout=120)
        total_time = time.time() - start_time

        if response.status_code != 200:
            error_body = response.text
            return ModelResponse(
                content="",
                time_to_first_token=None,
                total_time=total_time,
                success=False,
                error=f"API error {response.status_code}: {error_body}"
            )

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        return ModelResponse(
            content=content,
            time_to_first_token=None,
            total_time=total_time,
            success=True
        )

    def _stream_request(
        self, url: str, payload: dict, start_time: float
    ) -> ModelResponse:
        """流式请求"""
        content_chunks = []
        time_to_first_token = None

        response = self.session.post(
            url,
            json=payload,
            stream=True,
            timeout=120
        )

        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    chunk = delta.get("content", "")
                    if chunk:
                        if time_to_first_token is None:
                            time_to_first_token = time.time() - start_time
                        content_chunks.append(chunk)
                except json.JSONDecodeError:
                    continue

        total_time = time.time() - start_time
        content = "".join(content_chunks)

        return ModelResponse(
            content=content,
            time_to_first_token=time_to_first_token,
            total_time=total_time,
            success=response.status_code == 200
        )

    def test_connection(self) -> tuple[bool, str]:
        """测试连接

        Returns:
            (success, message)
        """
        response = self.chat(
            system_prompt="你是一个助手。",
            user_prompt="你好",
            stream=False
        )
        return response.success, response.error or "连接成功"
```

**Step 2: 验证客户端**

```bash
cd /mnt/d/Code/agent && python -c "
from src.client import ZhipuClient
from src.config import ModelConfig
config = ModelConfig(name='GLM-4-Flash', api_key='test')
client = ZhipuClient(config)
print('Client created successfully')
"
```

Expected: "Client created successfully"

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add src/client.py && git commit -m "feat: add Zhipu API client"
```

---

## Task 4: 输出解析器

**Files:**
- Create: `/mnt/d/Code/agent/src/parser.py`

**Step 1: 创建输出解析器**

Create `src/parser.py`:
```python
"""模型输出解析器"""
from dataclasses import dataclass
from typing import Optional, Tuple
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
    """输出解析器 - 解析【思考】【思考】...<show>...</show>格式"""

    # 正则表达式模式
    THINK_PATTERN = re.compile(r'【思考】(.*?)【思考】', re.DOTALL)
    TTS_PATTERN = re.compile(r'【TTS】(.*?)【TTS】', re.DOTALL)
    SHOW_PATTERN = re.compile(r'<show>(.*?)</show>', re.DOTALL)

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

        # 检测额外内容（标签外的内容）
        cleaned = content
        if think_match:
            cleaned = cleaned.replace(think_match.group(0), "")
        if tts_match:
            cleaned = cleaned.replace(tts_match.group(0), "")
        if show_match:
            cleaned = cleaned.replace(show_match.group(0), "")
        extra_content = cleaned.strip()

        return ParsedOutput(
            think=think,
            tts=tts,
            show=show,
            raw=content,
            has_think_tag=think_match is not None,
            has_tts_tag=tts_match is not None,
            has_show_tag=show_match is not None,
            extra_content=extra_content
        )

    @classmethod
    def extract_tts_sentences(cls, tts: str) -> list[str]:
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
    def extract_show_items(cls, show: str) -> list[str]:
        """从SHOW内容提取条目列表

        Args:
            show: SHOW内容

        Returns:
            条目列表
        """
        # 按换行分割
        items = show.split('\n')
        return [item.strip() for item in items if item.strip()]
```

**Step 2: 验证解析器**

```bash
cd /mnt/d/Code/agent && python -c "
from src.parser import OutputParser

test_output = '''【思考】分析通知，进行分级和筛选【思考】
【TTS】您有待审批工作。账户有支出变动【TTS】
<show>一级重要通知
企业微信 待审批申请需处理
短信 银行账户支出通知</show>'''

parsed = OutputParser.parse(test_output)
print(f'Think: {parsed.think}')
print(f'TTS: {parsed.tts}')
print(f'Show: {parsed.show}')
print(f'Has all tags: {parsed.has_think_tag and parsed.has_tts_tag and parsed.has_show_tag}')
"
```

Expected: 所有标签都被正确解析

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add src/parser.py && git commit -m "feat: add output parser"
```

---

## Task 5: 评分引擎

**Files:**
- Create: `/mnt/d/Code/agent/src/scorer.py`

**Step 1: 创建评分引擎**

Create `src/scorer.py`:
```python
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
        if parsed.extra_content:
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
        if re.search(r'[^\x00-\x7F\u4e00-\u9fff]', content):
            # 允许中文标点
            pass
        if re.search(r'[🔥⭐❌✅💡🎯]', content):
            issues.append("使用表情符号")
            score -= 3

        # 检查英文（如果有）
        english_matches = re.findall(r'[a-zA-Z]{3,}', content)
        # 允许常见英文词汇（如app名、品牌等）
        allowed_english = ['app', 'web', 'api', 'gps', 'wifi']
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

        # 检查一级通知是否被正确处理
        for category, keywords in self.LEVEL1_KEYWORDS.items():
                for kw in keywords:
                    # 检查输入中是否有一级通知
                    has_level1_input = any(
                        kw in n.text.lower() or kw in n.title.lower()
                        for n in notifications
                    )
                    if has_level1_input:
                        # 检查输出中是否提及
                        if kw not in tts_lower and kw not in show_lower:
                            # 可能是问题，也可能被汇总了
                            pass

        return DimensionScore(
            name="分级准确性",
            score=score,
            issues=issues,
            details={}
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
        # 如果有过多的书面用语，扣分
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
        # (简化实现：检查连续重复)
        for i in range(len(items) - 1):
            if items[i] == items[i + 1]:
                issues.append("存在重复条目")
                score -= 3
                break

        # 检查结构化程度
        if items and not any('\n\n' in show or '一级' in show or '二级' in show):
            # 没有明显的结构化标记
            pass

        return DimensionScore(
            name="SHOW约束",
            score=max(0, score),
            issues=issues,
            details={
                "item_count": len(items),
                "max_item_length": max(len(item) for item in items) if items else 0
            }
        )
```

**Step 2: 验证评分引擎**

```bash
cd /mnt/d/Code/agent && python -c "
from src.scorer import OutputScorer
from src.parser import OutputParser

test_output = '''【思考】分析通知【思考】
【TTS】您有待审批工作【TTS】
<show>企业微信 待审批申请</show>'''

parsed = OutputParser.parse(test_output)
scorer = OutputScorer()
result = scorer.score(parsed, [])
print(f'Score: {result.total_score}/100')
print(f'Passed: {result.passed}')
"
```

Expected: 显示评分结果

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add src/scorer.py && git commit -m "feat: add output scorer"
```

---

## Task 6: 提示词优化器

**Files:**
- Create: `/mnt/d/Code/agent/src/optimizer.py`

**Step 1: 创建提示词优化器**

Create `src/optimizer.py`:
```python
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
```

**Step 2: 验证优化器**

```bash
cd /mnt/d/Code/agent && python -c "
from src.optimizer import PromptOptimizer

optimizer = PromptOptimizer('Initial system prompt', 'Initial user prompt')
print('Optimizer created successfully')
print(f'Strategies: {len(optimizer.STRATEGIES)} categories')
"
```

Expected: "Optimizer created successfully"

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add src/optimizer.py && git commit -m "feat: add prompt optimizer"
```

---

## Task 7: 报告生成器

**Files:**
- Create: `/mnt/d/Code/agent/src/reporter.py`

**Step 1: 创建报告生成器**

Create `src/reporter.py`:
```python
"""报告生成器"""
from datetime import datetime
from typing import List, Dict, Any, Optional
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
        notifications_count: int
    ):
        """保存单次迭代结果"""
        timestamp = datetime.now().isoformat()

        result = {
            "timestamp": timestamp,
            "model": model_name,
            "iteration": iteration,
            "score": score.total_score,
            "passed": score.passed,
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
```

**Step 2: 验证报告生成器**

```bash
cd /mnt/d/Code/agent && python -c "
from src.reporter import Reporter
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    reporter = Reporter(tmpdir)
    print('Reporter created successfully')
    print(f'Output directory: {tmpdir}')
    print('Files:', os.listdir(tmpdir))
"
```

Expected: "Reporter created successfully"

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add src/reporter.py && git commit -m "feat: add reporter"
```

---

## Task 8: 主控制器

**Files:**
- Create: `/mnt/d/Code/agent/src/tuner.py`

**Step 1: 创建主控制器"""

Create `src/tuner.py`:
```python
"""提示词调优主控制器"""
from typing import Dict, List, Any, Optional
import time
from datetime import datetime

from src.config import Config, ModelConfig
from src.client import ZhipuClient, ModelResponse
from src.parser import OutputParser, ParsedOutput
from src.scorer import OutputScorer, ScoringResult
from src.optimizer import PromptOptimizer
from src.reporter import Reporter
from src.data_generator import NotificationGenerator, MockNotification


class PromptTuner:
    """提示词调优主控制器"""

    # 初始提示词（用户提供）
    INITIAL_SYSTEM_PROMPT = """你是专为车载停车场景打造的手机通知汇总智能助手，输出必须100%适配车机端TTS语音播报与屏幕显示。严格遵守以下所有规则。任何偏离规则的输出均为无效输出。

【强制输出格式 - 绝对不可修改】
【思考】{think}【思考】
【TTS】{tts}【TTS】
<show>{show}</show>

【格式字段定义】
- {think}：仅写本次通知分级、筛选、去重的核心推理逻辑，纯文本，不超过30字。无任何特殊符号。
- {tts}：仅播报给用户的语音内容。严格遵守TTS约束。无任何特殊符号。
- {show}：仅车机屏幕显示的结构化汇总内容。严格遵守SHOW约束。

【通知重要度分级规则 - 100%严格执行】

一级（必须TTS全量播报。SHOW置顶展示）：
- 工作类：企业微信待审批、会议提醒、工作任务分配、截止类工作通知
- 财务类：银行账户变动、收付款、还款提醒
- 安全类：账号异常登录、安全警告、车辆违章提醒

二级（TTS仅汇总核心条数。不播报详情。SHOW二级位置展示）：
- 社交类：微信/QQ个人私信、家人群等重要群聊消息
- 生活类：外卖、快递、取件码、水电煤缴费通知
- 出行类：行程、停车、限行、导航相关通知

三级（仅SHOW末尾展示。绝对禁止TTS播报）：
- 营销类：促销、优惠、广告、活动、优惠券推送
- 娱乐类：音乐、视频、游戏、热点、非重要群聊消息
- 系统类：非紧急系统提醒、存储提醒、应用更新、验证码短信
- 其他无明确优先级的低重要度通知

【TTS语音播报强制约束】
1. 仅可播报一级通知核心内容+二级通知条数汇总。禁止播报三级任何内容
2. 口语化、简洁自然。无任何特殊符号、标点、英文
3. 总句数不超过15句。单句不超过30个字
4. 无一级/二级重要通知时，仅输出：暂无重要通知

【SHOW屏幕展示强制约束】
1. 严格按「一级>二级>三级」优先级排序。同级别按应用分类展示
2. 同类重复通知必须合并去重。仅保留1条。禁止重复展示
3. 单条内容精简。不超过20个字。禁止长文本
4. 禁止编造、新增任何通知中不存在的信息
5. 纯文本分条展示。禁止使用markdown、表情、特殊符号

【绝对禁止行为】
违反任意一条均为无效输出：
1. 禁止输出标签格式外的任何文字、解释、统计、说明内容
2. 禁止修改、增减、拆分标签结构
3. 禁止使用任何markdown格式、表情、特殊符号、英文
4. 禁止编造通知数据、统计数字、不存在的内容
5. 禁止突破分级规则播报、展示内容"""

    INITIAL_USER_PROMPT_TEMPLATE = """以下是需要处理的通知数据：
{notifications}"""

    def __init__(self, config: Config):
        self.config = config
        self.reporter = Reporter(config.output_dir)
        self.generator = NotificationGenerator()

        # 初始化提示词
        self.system_prompt = self.INITIAL_SYSTEM_PROMPT
        self.user_prompt_template = self.INITIAL_USER_PROMPT_TEMPLATE

        # 结果存储
        self.results_by_model: Dict[str, List[Dict]] = {}
        self.best_result: Optional[Dict[str, Any]] = None

        # 计数器
        self.total_iterations = 0
        self.start_time: Optional[float] = None

    def run(self):
        """运行调优过程"""
        self.start_time = time.time()
        max_time = self.config.scoring.max_runtime_hours * 3600

        print(f"\n{'='*60}")
        print(f"提示词调优工具启动")
        print(f"{'='*60}")
        print(f"配置: {len(self.config.models)} 个模型")
        print(f"收敛阈值: 总分 >= {self.config.scoring.total_score}, 各维度 >= {self.config.scoring.dimension_score}")
        print(f"最大迭代: {self.config.scoring.max_iterations} 次/模型")
        print(f"最大运行时间: {self.config.scoring.max_runtime_hours} 小时")
        print(f"{'='*60}\n")

        # 生成测试数据
        notifications = self.generator.generate(100)
        notifications_json = self.generator.to_json_string(notifications)
        print(f"生成了 {len(notifications)} 条测试通知\n")

        for model_config in self.config.models:
            print(f"\n{'-'*60}")
            print(f"测试模型: {model_config.name}")
            print(f"{'-'*60}")

            model_result = self._test_model(
                model_config,
                notifications,
                notifications_json,
                max_time
            )

            if model_result:
                self.results_by_model[model_config.name] = model_result

                # 更新最佳结果
                best_score = max(r['score'] for r in model_result)
                if self.best_result is None or best_score > self.best_result.get('score', 0):
                    self.best_result = {
                        'model': model_config.name,
                        'score': best_score,
                        'system_prompt': self.system_prompt,
                        'user_prompt_template': self.user_prompt_template,
                        'optimization_history': []
                    }

            # 检查是否达到全局目标
            if self._check_convergence():
                print("\n✓ 达到收敛目标！")
                break

            # 检查时间限制
            if time.time() - self.start_time > max_time:
                print("\n⏰ 达到最大运行时间")
                break

        # 生成最终报告
        self._generate_final_report()

    def _test_model(
        self,
        model_config: ModelConfig,
        notifications: List[MockNotification],
        notifications_json: str,
        max_time: float
    ) -> Optional[List[Dict]]:
        """测试单个模型"""
        client = ZhipuClient(model_config)
        optimizer = PromptOptimizer(self.system_prompt, self.user_prompt_template)
        scorer = OutputScorer()

        results = []
        consecutive_passes = 0

        for iteration in range(self.config.scoring.max_iterations):
            self.total_iterations += 1

            # 检查时间限制
            if time.time() - self.start_time > max_time:
                break

            # 构建用户提示词
            user_prompt = self.user_prompt_template.replace("{notifications}", notifications_json)

            # 调用模型
            print(f"  [{iteration+1}] 调用 {model_config.name}...", end=" ")
            response = client.chat(
                system_prompt=optimizer.system_prompt,
                user_prompt=user_prompt,
                stream=False
            )

            if not response.success:
                print(f"    ✗ API错误: {response.error}")
                time.sleep(2)
                continue

            # 解析输出
            parsed = OutputParser.parse(response.content)

            # 评分
            score_result = scorer.score(parsed, notifications)

            print(f"    分数: {score_result.total_score:.1f}/100 - {'✓' if score_result.passed else '✗'}")

            # 保存结果
            result = {
                'iteration': iteration + 1,
                'score': score_result.total_score,
                'passed': score_result.passed,
                'response_time': response.total_time,
                'raw_output': response.content[:500]
            }
            results.append(result)

            # 保存详细结果
            self.reporter.save_iteration_result(
                model_name=model_config.name,
                iteration=iteration + 1,
                system_prompt=optimizer.system_prompt,
                user_prompt=user_prompt,
                raw_output=response.content,
                parsed=parsed,
                score=score_result,
                notifications_count=len(notifications)
            )

            # 检查收敛
            if score_result.passed:
                consecutive_passes += 1
                if consecutive_passes >= self.config.scoring.consecutive_passes:
                    print(f"    ✓ 连续 {consecutive_passes} 次通过！")
                    return results
            else:
                consecutive_passes = 0

                # 优化提示词
                if score_result.total_score < self.config.scoring.total_score:
                    optimizer.optimize(score_result)
                    print(f"    → 优化提示词")

            time.sleep(1)  # 避免请求过快

        return results

    def _check_convergence(self) -> bool:
        """检查是否达到收敛条件"""
        if not self.best_result:
            return False

        # 检查是否有模型连续通过足够次数
        for model_name, results in self.results_by_model.items():
                if len(results) >= self.config.scoring.consecutive_passes:
                    recent = results[-self.config.scoring.consecutive_passes:]
                    if all(r['passed'] for r in recent):
                        return True

        return False

    def _generate_final_report(self):
        """生成最终报告"""
        total_time = time.time() - self.start_time if self.start_time else 0

        report = self.reporter.generate_final_report(
            best_result=self.best_result or {},
            total_iterations=self.total_iterations,
            total_time_seconds=total_time,
            model_results=self.results_by_model
        )

        print(f"\n{'='*60}")
        print("调优完成！")
        print(f"{'='*60}")
        print(f"总迭代: {self.total_iterations}")
        print(f"总时间: {total_time/60:.1f} 分钟")
        if self.best_result:
            print(f"最佳分数: {self.best_result['score']:.1f}/100")
            print(f"最佳模型: {self.best_result['model']}")
        print(f"\n报告已保存到: {self.config.output_dir}/")
        print(report)
```

**Step 2: 验证主控制器**

```bash
cd /mnt/d/Code/agent && python -c "
from src.tuner import PromptTuner
print('PromptTuner class loaded successfully')
print(f'Initial system prompt length: {len(PromptTuner.INITIAL_SYSTEM_PROMPT)}')
"
```

Expected: 显示类加载成功

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add src/tuner.py && git commit -m "feat: add main tuner controller"
```

---

## Task 9: 创建配置文件

**Files:**
- Create: `/mnt/d/Code/agent/config.json`

**Step 1: 创建配置文件**

Create `config.json`:
```json
{
  "models": [
    {
      "name": "GLM-4-Flash",
      "api_key": "YOUR_API_KEY_HERE",
      "base_url": "https://open.bigmodel.cn/api/paas/v4",
      "max_tokens": 3000,
      "temperature": 0.0
    }
  ],
  "scoring": {
    "total_score": 85.0,
    "dimension_score": 15.0,
    "consecutive_passes": 3,
    "max_iterations": 50,
    "max_runtime_hours": 2.0
  },
  "output_dir": "output"
}
```

**Step 2: 提示用户填入API Key**

```bash
echo "请在 config.json 中填入您的 API Key"
```

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add config.json && git commit -m "feat: add config file template"
```

---

## Task 10: 髀脚测试

**Files:**
- Create: `/mnt/d/Code/agent/tests/test_scorer.py`

**Step 1: 创建评分测试**

Create `tests/test_scorer.py`:
```python
"""评分引擎单元测试"""
import pytest
from src.parser import OutputParser
from src.scorer import OutputScorer


class TestOutputScorer:
    """评分引擎测试"""

    @pytest.fixture
    def scorer(self):
        return OutputScorer()

    @pytest.fixture
    def sample_output(self):
        return """【思考】分析通知。进行分级筛选【思考】
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
        perfect_output = """【思考】按规则分级筛选去重。优先播报高优通知【思考】
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
```

**Step 2: 运行测试**

```bash
cd /mnt/d/Code/agent && pip install pytest && python -m pytest tests/test_scorer.py -v
```

Expected: 所有测试通过

**Step 3: Commit**

```bash
cd /mnt/d/Code/agent && git add tests/test_scorer.py && git commit -m "test: add scorer unit tests"
```

---

## Task 11: 最终集成测试

**Step 1: 安装依赖**

```bash
cd /mnt/d/Code/agent && pip install -r requirements.txt
```

**Step 2: 验证整体结构**

```bash
cd /mnt/d/Code/agent && python -c "
from src.config import Config
from src.client import ZhipuClient
from src.parser import OutputParser
from src.scorer import OutputScorer
from src.optimizer import PromptOptimizer
from src.reporter import Reporter
from src.tuner import PromptTuner
from src.data_generator import NotificationGenerator
print('✓ All modules imported successfully')
"
```

Expected: "All modules imported successfully"

**Step 3: 创建README**

Create `README.md`:
```markdown
# Prompt Tuner

车载通知汇总提示词自动调优工具

## 功能

- 多模型测试：支持同时测试多个智谱模型
- 自动评分：从5个维度评估输出质量
- 自动优化：根据评分结果自动调整提示词
- 详细报告：生成完整的测试报告

## 快速开始

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置 API Key:
编辑 `config.json`， 巻加您的智谱 API Key

3. 运行:
```bash
python run.py config.json
```

## 输出

- `output/results.jsonl` - 每次测试的详细结果
- `output/best_result.json` - 最佳配置
- `output/final_report.md` - 完整报告

## 评分维度

| 维度 | 分值 | 检查项 |
|------|------|--------|
| 格式正确性 | 20 | 标签完整、无额外内容 |
| 内容合规性 | 20 | 无markdown、无特殊符号、无英文 |
| 分级准确性 | 20 | 一级/二级/三级分类正确 |
| TTS约束 | 20 | 不超过15句、单句不超过30字 |
| SHOW约束 | 20 | 按优先级排序、单条不超过20字 |
```

**Step 4: Commit最终版本**

```bash
cd /mnt/d/Code/agent && git add README.md && git commit -m "docs: add README"
```

---

## 完成标准

- [ ] 所有模块可正常导入
- [ ] 评分引擎测试通过
- [ ] 配置文件可正确加载
- [ ] 可通过 `python run.py config.json` 启动
