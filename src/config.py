"""配置管理模块"""
from dataclasses import dataclass
from typing import List


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
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        models = [
            ModelConfig(**m) for m in data.get("models", [])
        ]
        scoring_data = data.get("scoring", {})
        scoring = ScoringThreshold(**scoring_data)

        return cls(
            models=models,
            scoring=scoring,
            output_dir=data.get("output_dir", "output")
        )

    def save(self, filepath: str):
        """保存配置到JSON文件"""
        import json
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
