#!/usr/bin/env python3
"""提示词调优工具入口"""
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.config import Config


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = Config.load(config_path)

    print(f"加载配置: {config_path}")
    print(f"模型数量: {len(config.models)}")
    print(f"输出目录: {config.output_dir}")
    print(f"收敛阈值: 总分 >= {config.scoring.total_score}")
    
    # 延迟导入，避免循环依赖
    from src.tuner import PromptTuner
    tuner = PromptTuner(config)
    tuner.run()


if __name__ == "__main__":
    main()
