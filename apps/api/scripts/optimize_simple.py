#!/usr/bin/env python3
"""Simple optimization script - runs multiple train_eval searches."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_train_eval(config: dict):
    """Run train_eval with given config."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.dirname(script_dir)
    
    cmd = [
        "py", "-3.12", "scripts/train_eval.py",
        "--model", "lgbm",
        "--factor", config["factor"],
        "--instruments", config["instruments"],
        "--lgbm-n-estimators", "1000,2000",
        "--lgbm-lr", "0.01,0.02",
        "--lgbm-num-leaves", "63,127",
        "--lgbm-subsample", "0.8",
        "--lgbm-colsample-bytree", "0.8",
        "--topk", str(config["topk"]),
        "--tag", config["tag"],
        "--min-ic", "0.015",
    ]
    
    logger.info(f"运行命令：{' '.join(cmd)}")
    logger.info(f"配置：{config}")
    logger.info(f"工作目录：{api_dir}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=api_dir,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"运行失败：{e}")
        return False


def main():
    logger.info("=" * 100)
    logger.info("开始简单自动优化")
    logger.info("=" * 100)
    
    # 按优先级排列的配置组合
    configs = [
        {"factor": "alpha360", "instruments": "csi500", "topk": 30, "tag": "opt_a360_csi500_k30"},
        {"factor": "alpha360", "instruments": "csi500", "topk": 20, "tag": "opt_a360_csi500_k20"},
        {"factor": "alpha360", "instruments": "csi300", "topk": 30, "tag": "opt_a360_csi300_k30"},
        {"factor": "alpha158", "instruments": "csi500", "topk": 30, "tag": "opt_a158_csi500_k30"},
        {"factor": "alpha360", "instruments": "csi500", "topk": 50, "tag": "opt_a360_csi500_k50"},
        {"factor": "alpha158", "instruments": "csi300", "topk": 30, "tag": "opt_a158_csi300_k30"},
    ]
    
    success_count = 0
    for i, config in enumerate(configs, 1):
        logger.info("\n" + "=" * 100)
        logger.info(f"配置 {i}/{len(configs)}")
        logger.info("=" * 100)
        
        success = run_train_eval(config)
        if success:
            success_count += 1
            logger.info(f"✅ 配置 {i} 完成")
        else:
            logger.warning(f"❌ 配置 {i} 失败")
    
    logger.info("\n" + "=" * 100)
    logger.info(f"优化循环完成！成功：{success_count}/{len(configs)}")
    logger.info("=" * 100)
    logger.info("请运行 'py -3.12 scripts/show_best.py' 查看最优结果")


if __name__ == "__main__":
    main()
