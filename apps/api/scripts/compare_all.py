#!/usr/bin/env python3
"""Compare all experiments."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.experiment.tracker import ExperimentTracker

def main():
    tracker = ExperimentTracker()
    
    print("=" * 140)
    print(f"{'排名':<4} {'Sharpe':>8} {'年化':>8} {'回撤':>8} {'RankIC':>10} {'模型':<10} {'因子':<12} {'股票池':<10} {'TopK':<6} {'标签':<20} {'实验ID':<20}")
    print("-" * 140)
    
    # 获取所有完成的实验
    if tracker.collection is not None:
        cursor = tracker.collection.find({"status": "completed"})
        cursor = cursor.sort([("backtest_result.sharpe_ratio", -1)])
        
        all_exps = []
        for doc in cursor:
            doc.pop("_id", None)
            all_exps.append(doc)
        
        for rank, exp in enumerate(all_exps, 1):
            bt = exp.get("backtest_result", {}) or {}
            tm = exp.get("training_metrics", {}) or {}
            cfg = exp.get("config", {})
            
            sharpe = bt.get("sharpe_ratio", 0) or 0.0
            ann_ret = bt.get("annual_return", 0) or 0.0
            max_dd = bt.get("max_drawdown", 0) or 0.0
            rank_ic = tm.get("rank_ic", 0) or 0.0
            
            model = cfg.get("model_type", "-") or "-"
            factor = cfg.get("factor_type", "-") or "-"
            tag = exp.get("tag", "-") or "-"
            
            # 简化股票池显示
            instruments = cfg.get("instruments", [])
            if isinstance(instruments, list):
                if len(instruments) > 300:
                    inst_display = "CSI500"
                elif len(instruments) > 100:
                    inst_display = "CSI300"
                else:
                    inst_display = f"{len(instruments)}只"
            else:
                inst_display = str(instruments)
            
            # 从配置读取 TopK
            topk = cfg.get("topk", "-")
            
            exp_id = exp.get("experiment_id", "-")
            
            print(f"{rank:<4} {sharpe:>8.3f} {ann_ret:>8.1%} {max_dd:>8.1%} {rank_ic:>10.4f} {model:<10} {factor:<12} {inst_display:<10} {topk:<6} {tag:<20} {exp_id:<20}")
    
    print("=" * 140)
    
    tracker.close()


if __name__ == "__main__":
    main()
