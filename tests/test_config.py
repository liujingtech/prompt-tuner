"""Tests for config module"""
import json
import os
import tempfile
import pytest
from src.config import ModelConfig, ScoringThreshold, Config


class TestModelConfig:
    """Test ModelConfig dataclass"""

    def test_model_config_creation_with_required_fields(self):
        """Test creating ModelConfig with only required fields"""
        config = ModelConfig(name="test-model", api_key="test-key")
        assert config.name == "test-model"
        assert config.api_key == "test-key"
        assert config.base_url == "https://open.bigmodel.cn/api/paas/v4"
        assert config.max_tokens == 3000
        assert config.temperature == 0.0

    def test_model_config_creation_with_all_fields(self):
        """Test creating ModelConfig with all fields"""
        config = ModelConfig(
            name="custom-model",
            api_key="custom-key",
            base_url="https://custom.api.url",
            max_tokens=4000,
            temperature=0.5
        )
        assert config.name == "custom-model"
        assert config.api_key == "custom-key"
        assert config.base_url == "https://custom.api.url"
        assert config.max_tokens == 4000
        assert config.temperature == 0.5


class TestScoringThreshold:
    """Test ScoringThreshold dataclass"""

    def test_scoring_threshold_defaults(self):
        """Test default values for ScoringThreshold"""
        threshold = ScoringThreshold()
        assert threshold.total_score == 85.0
        assert threshold.dimension_score == 15.0
        assert threshold.consecutive_passes == 3
        assert threshold.max_iterations == 50
        assert threshold.max_runtime_hours == 2.0

    def test_scoring_threshold_custom_values(self):
        """Test custom values for ScoringThreshold"""
        threshold = ScoringThreshold(
            total_score=90.0,
            dimension_score=18.0,
            consecutive_passes=5,
            max_iterations=100,
            max_runtime_hours=3.0
        )
        assert threshold.total_score == 90.0
        assert threshold.dimension_score == 18.0
        assert threshold.consecutive_passes == 5
        assert threshold.max_iterations == 100
        assert threshold.max_runtime_hours == 3.0


class TestConfig:
    """Test Config class"""

    def test_config_creation(self):
        """Test creating Config instance"""
        models = [ModelConfig(name="model1", api_key="key1")]
        scoring = ScoringThreshold()
        config = Config(models=models, scoring=scoring)
        assert len(config.models) == 1
        assert config.models[0].name == "model1"
        assert config.output_dir == "output"

    def test_config_load_from_json(self):
        """Test loading Config from JSON file"""
        config_data = {
            "models": [
                {
                    "name": "glm-4",
                    "api_key": "test-api-key",
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
            "output_dir": "custom_output"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            config = Config.load(temp_path)
            assert len(config.models) == 1
            assert config.models[0].name == "glm-4"
            assert config.models[0].api_key == "test-api-key"
            assert config.scoring.total_score == 85.0
            assert config.output_dir == "custom_output"
        finally:
            os.unlink(temp_path)

    def test_config_save_to_json(self):
        """Test saving Config to JSON file"""
        models = [
            ModelConfig(
                name="test-model",
                api_key="test-key",
                base_url="https://test.url",
                max_tokens=2000,
                temperature=0.3
            )
        ]
        scoring = ScoringThreshold(
            total_score=90.0,
            dimension_score=18.0,
            consecutive_passes=4,
            max_iterations=60,
            max_runtime_hours=1.5
        )
        config = Config(models=models, scoring=scoring, output_dir="test_output")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            config.save(temp_path)

            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert len(data["models"]) == 1
            assert data["models"][0]["name"] == "test-model"
            assert data["models"][0]["api_key"] == "test-key"
            assert data["scoring"]["total_score"] == 90.0
            assert data["scoring"]["dimension_score"] == 18.0
            assert data["output_dir"] == "test_output"
        finally:
            os.unlink(temp_path)

    def test_config_load_with_defaults(self):
        """Test loading Config with missing optional fields using defaults"""
        config_data = {
            "models": [
                {
                    "name": "minimal-model",
                    "api_key": "minimal-key"
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            config = Config.load(temp_path)
            assert len(config.models) == 1
            assert config.models[0].base_url == "https://open.bigmodel.cn/api/paas/v4"
            assert config.models[0].max_tokens == 3000
            assert config.models[0].temperature == 0.0
            assert config.scoring.total_score == 85.0  # default
            assert config.output_dir == "output"  # default
        finally:
            os.unlink(temp_path)

    def test_config_round_trip(self):
        """Test that save/load round trip preserves data"""
        original_models = [
            ModelConfig(name="model-a", api_key="key-a"),
            ModelConfig(name="model-b", api_key="key-b", temperature=0.7)
        ]
        original_scoring = ScoringThreshold(total_score=88.0, consecutive_passes=4)
        original_config = Config(
            models=original_models,
            scoring=original_scoring,
            output_dir="round_trip_output"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            original_config.save(temp_path)
            loaded_config = Config.load(temp_path)

            assert len(loaded_config.models) == 2
            assert loaded_config.models[0].name == "model-a"
            assert loaded_config.models[1].temperature == 0.7
            assert loaded_config.scoring.total_score == 88.0
            assert loaded_config.scoring.consecutive_passes == 4
            assert loaded_config.output_dir == "round_trip_output"
        finally:
            os.unlink(temp_path)
