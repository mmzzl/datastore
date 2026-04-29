#!/usr/bin/env python3
"""Check previous experiment results."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.experiment.tracker import ExperimentTracker

tracker = ExperimentTracker()
# list_experiments 返回 (results, total_count)
experiments, _ = tracker.list_experiments(page_size=50)

print('最近 30 个实验（按 Sharpe 排序）：')
print('='*130)

# 按 Sharpe 排序
sorted_exps = sorted(
    experiments, 
    key=lambda e: (e.get('backtest_result', {}) or {}).get('sharpe_ratio', -float('inf')),
    reverse=True
)

for i, exp in enumerate(sorted_exps[:15], 1):
    bt = exp.get('backtest_result', {}) or {}
    tm = exp.get('training_metrics', {}) or {}
    cfg = exp.get('config', {})
    sharpe = bt.get('sharpe_ratio', 0)
    ann_ret = bt.get('annual_return', 0)
    max_dd = bt.get('max_drawdown', 0)
    rank_ic = tm.get('rank_ic', 0)
    model_id = exp.get('model_id', '')
    
    print(f'{i:2d}. Sharpe={sharpe:.3f}, AnnRet={ann_ret:.2%}, MaxDD={max_dd:.2%}, RankIC={rank_ic:.4f}')
    print(f'    Model={cfg.get("model_type")}, Factor={cfg.get("factor_type")}, Inst={cfg.get("instruments", "")[:15]}...')
    hp = cfg.get('hyperparams', {})
    if hp:
        print(f'    Params: {hp}')
    if model_id:
        print(f'    ModelID: {model_id}')
    print()

tracker.close()
