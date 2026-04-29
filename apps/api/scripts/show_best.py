#!/usr/bin/env python3
"""Show best experiment."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.experiment.tracker import ExperimentTracker

tracker = ExperimentTracker()
best = tracker.get_best('backtest_result.sharpe_ratio')

if best:
    print('=' * 100)
    print('当前最好的实验：')
    print('=' * 100)
    
    bt = best.get('backtest_result', {}) or {}
    tm = best.get('training_metrics', {}) or {}
    cfg = best.get('config', {})
    
    print(f'Experiment ID: {best.get("experiment_id")}')
    print(f'Status: {best.get("status")}')
    print(f'Created at: {best.get("created_at")}')
    print()
    print('Backtest Results:')
    print(f'  Sharpe Ratio:  {bt.get("sharpe_ratio", 0):.3f}')
    print(f'  Annual Return: {bt.get("annual_return", 0):.2%}')
    print(f'  Max Drawdown:  {bt.get("max_drawdown", 0):.2%}')
    print(f'  Total Return:  {bt.get("total_return", 0):.2%}')
    print()
    print('Training Metrics:')
    print(f'  Rank IC:    {tm.get("rank_ic", 0):.4f}')
    print(f'  IC:         {tm.get("ic", 0):.4f}')
    print(f'  ICIR:       {tm.get("icir", 0):.4f}')
    print()
    print('Configuration:')
    print(f'  Model Type:    {cfg.get("model_type")}')
    print(f'  Factor Type:   {cfg.get("factor_type")}')
    print(f'  Instruments:   {cfg.get("instruments")}')
    print(f'  Start Time:    {cfg.get("start_time")}')
    print(f'  End Time:      {cfg.get("end_time")}')
    hp = cfg.get('hyperparams', {})
    if hp:
        print(f'  Hyperparams:   {hp}')
    print(f'  Model ID:      {best.get("model_id")}')
    
    tracker.close()
else:
    print('没有找到完成的实验。')
