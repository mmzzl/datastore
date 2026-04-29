#!/usr/bin/env python3
"""Auto optimization script to find best configuration."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import time
from typing import Any, Dict, List, Tuple
from datetime import datetime

from scripts.train_eval import run_pipeline, parse_args

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 100")
    logger.info("开始自动优化...")
    logger.info("=" * 100")

    # 定义要探索的配置空间
    factor_types = ["alpha158", "alpha360"]
    instruments_list = ["csi300", "csi500"]
    topk_list = [20, 30, 50]
    
    # LightGBM 超参数搜索空间
    lgbm_n_estimators = [1000, 2000]
    lgbm_lr = [0.01, 0.02]
    lgbm_num_leaves = [63, 127]
    lgbm_subsample = [0.8]
    lgbm_colsample = [0.8]

    total_configs = (len(factor_types) * len(instruments_list) * len(topk_list) * len(lgbm_n_estimators) * len(lgbm_lr) * len(lgbm_num_leaves)
    
    logger.info(f"总共需要探索的配置组合数：{total_configs}")
    logger.info(f"  因子类型：{factor_types}")
    logger.info(f"  股票池：{instruments_list}")
    logger.info(f"  TopK：{topk_list}")
    logger.info(f"  树数量：{lgbm_n_estimators}")
    logger.info(f"  学习率：{lgbm_lr}")
    logger.info("=" * 100")

    best_sharpe = -1.0
    best_config = None
    all_results = []
    
    start_time = time.time()
    config_count = 0

    # 按预期效果先探索高优先级组合
    priority_configs = [
        ("alpha360", "csi500", 30),
        ("alpha360", "csi500", 20),
        ("alpha360", "csi300", 30),
        ("alpha158", "csi500", 30),
        ("alpha360", "csi500", 50),
        ("alpha158", "csi300", 30),
    ]

    logger.info("先运行高优先级组合...")
    
    for factor_type, instruments, topk in priority_configs:
        config_count += 1
        logger.info("\n" + "=" * 100)
        logger.info(f"组合 {config_count}: 因子={factor_type}, 股票池={instruments}, TopK={topk}")
        logger.info("=" * 100")
        
        # 构建命令行参数
        import argparse
        import sys
        from unittest.mock import patch
        
        class Args:
            def __init__(self):
                self.model = "lgbm"
                self.factor = factor_type
                self.instruments = instruments
                self.start = "2022-01-01"
                self.end = "2026-01-01"
                self.sync_data = False
                self.min_ic = 0.015
                self.target_sharpe = 1.5
                self.tag = "auto_optimize"
                self.lgbm_n_estimators = "1000,2000"
                self.lgbm_lr = "0.01,0.02"
                self.lgbm_num_leaves = "63,127"
                self.lgbm_subsample = "0.8"
                self.lgbm_colsample_bytree = "0.8"
                self.mlp_hidden_sizes = None
                self.mlp_lr = None
                self.mlp_batch_size = None
                self.mlp_epochs = None
                self.topk = topk
        
        args = Args()
        
        # 运行训练管道
        try:
            from scripts.train_eval import build_param_grid, build_training_config, sync_data, train_model, evaluate_model, run_backtest, record_experiment, print_comparison_table
            import scripts.train_eval.main(sys.argv[1:])
            # 实际上我们直接调用 train_eval 的逻辑
            from scripts.train_eval import run_pipeline
            from scripts.train_eval import parse_args
            
            # 构造模拟命令行
            cmd_args = [
                "--model", "lgbm",
                "--factor", factor_type,
                "--instruments", instruments,
                "--lgbm-n-estimators", "1000,2000",
                "--lgbm-lr", "0.01,0.02",
                "--lgbm-num-leaves", "63,127",
                "--topk", str(topk),
                "--tag", "auto_optimize",
                "--min-ic", "0.015"
            ]
            
            # 使用真实调用
            sys.argv = [sys.argv[0]] + cmd_args
            results = scripts.train_eval.main()
            
            if results:
                for r = [r for r in results if r.status == "completed"]
                if r:
                    best_for_config = max(r, key=lambda x: (x.backtest_result or {}).get("sharpe_ratio", -float("inf"))
                    sharpe = (best_for_config.backtest_result or {}).get("sharpe_ratio", 0)
                    all_results.append((factor_type, instruments, topk, sharpe, best_for_config))
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_config = (factor_type, instruments, topk, best_for_config)
                        logger.info(f"🎉 找到更好的模型！Sharpe={sharpe:.3f}")
        
        except Exception as e:
            logger.error(f"组合 {factor_type}-{instruments}-TopK={topk} 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    # 打印总结
    logger.info("\n" + "=" * 100)
    logger.info("优化完成！")
    logger.info("=" * 100)
    
    if best_config:
        factor_type, instruments, topk, best_result = best_config
        bt = best_result.backtest_result or {}
        logger.info(f"最优配置：")
        logger.info(f"  因子类型：{factor_type}")
        logger.info(f"  股票池：{instruments}")
        logger.info(f"  TopK：{topk}")
        logger.info(f"  Sharpe Ratio：{bt.get('sharpe_ratio', 0):.3f}")
        logger.info(f"  年化收益：{bt.get('annual_return', 0):.2%}")
        logger.info(f"  最大回撤：{bt.get('max_drawdown', 0):.2%}")
        logger.info(f"  模型ID：{best_result.model_id}")
    else:
        logger.info("没有找到成功完成的实验。")
    
    elapsed = time.time() - start_time
    logger.info(f"总耗时：{elapsed:.1f} 秒")
