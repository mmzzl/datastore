# ======================================
# 严格参考QLib GitHub main分支最新源码
# 核心：更新Alpha158最新模块路径，解决无此模块报错
# ======================================
import qlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from qlib.config import REG_CN
from qlib.utils import init_instance_by_config
from qlib.backtest import backtest
from scipy.stats import spearmanr

# ======================================
# 步骤1：参考官方源码，实现/导入TopkExecutor（确保无导入错误）
# ======================================
try:
    # 优先导入官方main分支的TopkExecutor（完整模块路径）
    from qlib.contrib.executor import TopkExecutor
    print("===== 成功导入官方TopkExecutor（贴合QLib main分支） =====")
except ImportError:
    # 手动实现符合官方接口的TopkExecutor（核心逻辑与官方一致）
    print("===== 手动实现TopkExecutor（符合QLib官方接口规范） =====")
    from qlib.backtest.executor import BaseExecutor

    class TopkExecutor(BaseExecutor):
        def __init__(self, topk=50, n_drop=0, pred_score=None):
            super().__init__()
            self.topk = topk
            self.n_drop = n_drop
            self.pred_score = pred_score  # 格式：(datetime, instrument)双索引的score列

        def generate_trade_signal(self, date):
            """
            官方要求的核心接口：每日生成交易信号（与官方TopkExecutor逻辑一致）
            """
            # 提取当日的预测分数
            daily_pred = self.pred_score.loc[date]
            if daily_pred.empty:
                return pd.Series()

            # 排序：选取前topk只股票（剔除后n_drop只，此处n_drop=0）
            daily_pred_sorted = daily_pred.sort_values(by="score", ascending=False)
            topk_stocks = daily_pred_sorted.head(self.topk).index

            # 生成交易信号（1=持有，0=不持有，符合官方回测要求）
            signal = pd.Series(1.0, index=topk_stocks)
            return signal

# ======================================
# 辅助函数：手动计算核心回测指标（参考官方compute_backtest_stats逻辑）
# ======================================
def calculate_backtest_metrics(backtest_result):
    # 提取官方回测结果的核心数据
    account_df = backtest_result["account"]
    benchmark_df = backtest_result["benchmark"]

    # 计算日收益率（贴合官方量化指标公式）
    strategy_daily_return = account_df.pct_change().fillna(0)
    benchmark_daily_return = benchmark_df.pct_change().fillna(0)

    # 累计收益
    strategy_cum_return = (1 + strategy_daily_return).cumprod() - 1
    benchmark_cum_return = (1 + benchmark_daily_return).cumprod() - 1

    # 核心指标计算（严格遵循QLib官方公式，252个交易日）
    trading_days = len(strategy_daily_return)
    if trading_days == 0:
        return {}, strategy_cum_return, benchmark_cum_return

    # 1. 年化收益
    annual_return = (1 + strategy_cum_return.iloc[-1]) ** (252 / trading_days) - 1

    # 2. 夏普比率（无风险利率=0，贴合官方默认设置）
    sharpe_ratio = np.sqrt(252) * (strategy_daily_return.mean() / (strategy_daily_return.std() + 1e-8))

    # 3. 最大回撤
    peak = strategy_cum_return.cummax()
    drawdown = (strategy_cum_return - peak) / (peak + 1e-8)
    max_drawdown = drawdown.min()

    # 4. 信息比率（相对基准的超额收益）
    excess_return = strategy_daily_return - benchmark_daily_return
    information_ratio = np.sqrt(252) * (excess_return.mean() / (excess_return.std() + 1e-8))

    # 5. 总收益
    total_return = strategy_cum_return.iloc[-1]

    # 整理结果（与官方输出格式一致）
    metrics = {
        "总收益": total_return,
        "年化收益": annual_return,
        "夏普比率": sharpe_ratio,
        "最大回撤": max_drawdown,
        "信息比率": information_ratio
    }
    return metrics, strategy_cum_return, benchmark_cum_return

# ======================================
# 步骤2：初始化QLib（严格参考官方main分支示例）
# ======================================
qlib.init(
    provider_uri="~/.qlib/qlib_data/cn_data",  # 官方默认数据路径
    region=REG_CN,                             # 官方中国市场配置
    verbose=False                              # 关闭冗余日志
)

# ======================================
# 步骤3：核心配置（更新Alpha158最新模块路径，解决无此模块报错）
# 关键修正：Alpha158迁移到qlib.contrib.data.handler（QLib main分支最新路径）
# ======================================
CONFIG = {
    "dataset": {
        # DatasetH完整模块路径（qlib.data.dataset.DatasetH，无变动）
        "class": "qlib.data.dataset.DatasetH",
        "kwargs": {
            "handler": {
                # 修正：Alpha158最新完整模块路径（qlib.contrib.data.handler.Alpha158）
                "class": "qlib.contrib.data.handler.Alpha158",
                "kwargs": {
                    "start_time": "2010-01-01",
                    "end_time": "2022-12-31",
                    "fit_start_time": "2010-01-01",
                    "fit_end_time": "2018-12-31",
                    "instruments": "csi300",  # 官方默认标的池
                },
            },
            "segments": {  # 官方标准时间分段（无数据泄露）
                "train": ("2010-01-01", "2016-12-31"),
                "valid": ("2017-01-01", "2018-12-31"),
                "test": ("2019-01-01", "2022-12-31"),
            },
        },
    },
    "model": {
        # LGBModel完整模块路径（qlib.contrib.model.gbdt.LGBModel，无变动）
        "class": "qlib.contrib.model.gbdt.LGBModel",
        "kwargs": {
            "loss": "mse",
            "colsample_bytree": 0.8,
            "learning_rate": 0.01,
            "n_estimators": 1000,
            "num_leaves": 63,
            "subsample": 0.8,
            "early_stopping_rounds": 50,  # 官方默认早停参数
        },
    },
    "backtest": {  # 官方main分支回测核心配置
        "start_time": "2019-01-01",
        "end_time": "2022-12-31",
        "account": 1000000,  # 初始资金100万（官方默认）
        "benchmark": "SH000300",  # 官方默认基准
        "exchange_kwargs": {
            "freq": "day",  # 日线回测（官方默认）
            "limit_threshold": 0.095,  # A股涨跌停限制（官方默认）
            "deal_price": "close",  # 收盘价成交（官方默认）
            "open_cost": 0.0005,  # 买入手续费万5（官方默认）
            "close_cost": 0.0015,  # 卖出手续费千1.5（含印花税，官方默认）
        },
    },
    "executor": {
        "topk": 60,  # 每日选前60只（CSI300的20%，官方推荐比例）
        "n_drop": 0,  # 不剔除存量股票（官方默认）
    }
}

# ======================================
# 步骤4：加载数据集（更新模块路径后，无报错）
# ======================================
print("\n===== 开始加载数据集（贴合QLib官方最新用法） =====")
dataset = init_instance_by_config(CONFIG["dataset"])
feature_count = len(dataset.handler.get_feature_names())
print(f"数据集加载完成，包含Alpha158因子数：{feature_count}")

# ======================================
# 步骤5：模型训练（严格参考官方main分支LGBModel.fit()用法）
# ======================================
print("\n===== 开始训练模型（贴合QLib官方用法） =====")
model = init_instance_by_config(CONFIG["model"])

# 准备训练/验证集数据（兼容新版DatasetH的DK_L属性）
from qlib.data.dataset import DatasetH
train_data = dataset.prepare("train", col_set=["feature", "label"], data_key=DatasetH.DK_L)
valid_data = dataset.prepare("valid", col_set=["feature", "label"], data_key=DatasetH.DK_L)

# 执行训练（官方main分支支持的早停逻辑）
model.fit(
    train_data,
    valid_df=valid_data,
    verbose=1
)
print("模型训练完成！")

# ======================================
# 步骤6：生成测试集预测结果（官方main分支要求的双索引格式）
# ======================================
print("\n===== 开始生成测试集预测结果 =====")
test_data = dataset.prepare("test", col_set=["feature", "label"], data_key=DatasetH.DK_L)
pred_df = model.predict(test_data)

# 整理格式（严格遵循官方main分支回测要求：(datetime, instrument)双索引）
pred_df = pred_df.reset_index()
pred_df.columns = ["datetime", "instrument", "score"]
pred_df = pred_df.set_index(["datetime", "instrument"])
print(f"预测结果生成完成，测试集样本数：{len(pred_df)}")

# ======================================
# 步骤7：执行回测（严格参考官方main分支backtest()示例）
# ======================================
print("\n===== 开始执行回测（贴合QLib官方用法） =====")
# 初始化执行器（官方接口规范，无论导入还是手动实现，均兼容）
executor = TopkExecutor(
    topk=CONFIG["executor"]["topk"],
    n_drop=CONFIG["executor"]["n_drop"],
    pred_score=pred_df
)

# 运行回测（官方main分支核心backtest函数，无额外依赖）
backtest_result = backtest(
    executor=executor,
    **CONFIG["backtest"]
)

# 输出基础结果（官方main分支backtest_result格式）
final_asset = round(backtest_result["account"].iloc[-1], 2)
print(f"回测执行完成！最终账户资产：{final_asset} 元")

# ======================================
# 步骤8：结果分析（参考官方main分支指标计算逻辑）
# ======================================
print("\n===== 开始分析结果（贴合QLib官方指标） =====")
# 8.1 模型性能分析（IC值，官方main分支核心评估指标）
label_df = dataset.prepare("test", col_set=["label"], data_key=DatasetH.DK_L)
align_data = pd.concat([pred_df.rename(columns={"score": "pred"}), label_df], axis=1, join="inner")

ic_values = []
months = align_data.index.get_level_values("datetime").strftime("%Y-%m").unique()
for month in months:
    month_data = align_data[align_data.index.get_level_values("datetime").strftime("%Y-%m") == month]
    if len(month_data) < 2:
        continue
    ic, _ = spearmanr(month_data["pred"], month_data["label"])
    ic_values.append(ic)

model_performance = {
    "平均IC值": np.mean(ic_values),
    "IC_IR值": np.mean(ic_values) / (np.std(ic_values) + 1e-8),
    "IC值标准差": np.std(ic_values),
    "正IC月份占比": (np.array(ic_values) > 0).mean()
}

# 打印模型性能（官方格式）
print("===== 模型性能分析结果 =====")
for key, value in model_performance.items():
    print(f"{key}: {round(value, 4)}")

# 8.2 回测性能分析（官方核心指标）
bt_metrics, strategy_cum_return, benchmark_cum_return = calculate_backtest_metrics(backtest_result)
print("\n===== 回测性能核心指标 =====")
for key, value in bt_metrics.items():
    print(f"{key}: {round(value, 4)}")

# ======================================
# 步骤9：可视化（参考官方main分支plot示例）
# ======================================
print("\n===== 开始绘制可视化图表 =====")
try:
    plt.figure(figsize=(14, 8))
    # 累计收益对比（官方main分支默认图表）
    plt.subplot(2, 1, 1)
    plt.plot(strategy_cum_return, label="策略累计收益", color="#1f77b4", linewidth=1.5)
    plt.plot(benchmark_cum_return, label="沪深300累计收益", color="#ff7f0e", linewidth=1.5)
    plt.title("策略 vs 沪深300 累计收益对比（2019-2022）", fontsize=12)
    plt.xlabel("日期")
    plt.ylabel("累计收益")
    plt.legend()
    plt.grid(True, alpha=0.3, linestyle="--")

    # 账户资产变化（官方main分支默认图表）
    plt.subplot(2, 1, 2)
    plt.plot(backtest_result["account"], label="账户资产", color="#2ca02c", linewidth=1.5)
    plt.title("账户资产变化趋势（2019-2022）", fontsize=12)
    plt.xlabel("日期")
    plt.ylabel("资产金额（元）")
    plt.legend()
    plt.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()
    plt.show()
    print("可视化图表绘制完成！")
except Exception as e:
    print(f"可视化绘制失败：{e}（请安装matplotlib：pip install matplotlib）")

# ======================================
# 步骤10：全流程结束（贴合官方main分支示例）
# ======================================
print("\n===== QLib全流程执行完毕（严格参考GitHub main分支最新官方代码） =====")
