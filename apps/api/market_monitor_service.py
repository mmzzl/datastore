#!/usr/bin/env python3
"""
市场监控服务启动脚本
用于启动 MarketWatcher 进行实时股票监控并生成交易信号
"""

import sys
import os
import time
import signal
import logging
import argparse
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.monitor import MarketWatcher
from app.monitor.config import MonitorConfig
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/market_monitor.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# 全局变量
watcher = None
running = True


def signal_handler(signum, frame):
    """信号处理器"""
    global running, watcher
    logger.info(f"接收到信号 {signum}，正在停止服务...")
    running = False
    if watcher:
        watcher.stop()
    sys.exit(0)


def main():
    global watcher, running

    parser = argparse.ArgumentParser(description="市场监控服务")
    parser.add_argument(
        "--interval", type=int, default=300, help="监控间隔（秒），默认300秒"
    )
    parser.add_argument("--days", type=int, default=5, help="分析天数，默认5天")
    parser.add_argument("--once", action="store_true", help="只运行一次")
    args = parser.parse_args()

    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 50)
    logger.info("市场监控服务启动")
    logger.info(f"监控间隔: {args.interval}秒")
    logger.info(f"分析天数: {args.days}天")
    logger.info("=" * 50)

    try:
        # 加载配置
        config = MonitorConfig()
        stocks = config.get_stocks()

        if not stocks:
            logger.warning("没有配置监控股票，使用默认股票列表")
            stocks = [
                {"code": "SH600000", "name": "浦发银行"},
                {"code": "SH600519", "name": "贵州茅台"},
            ]

        logger.info(f"监控股票列表: {[s.get('code') for s in stocks]}")

        # 转换为 watchlist 格式
        watchlist = []
        for stock in stocks:
            watchlist.append(
                {
                    "code": stock.get("code", ""),
                    "name": stock.get("name", ""),
                    "hold": stock.get("hold", False),
                    "cost_price": stock.get("cost_price", 0),
                }
            )

        # 创建监控器
        watcher = MarketWatcher(
            interval_sec=args.interval,
            watchlist=watchlist,
            days=args.days,
        )

        if args.once:
            # 只运行一次
            logger.info("执行单次监控...")
            watcher.run_once()
            logger.info("单次监控完成")
        else:
            # 持续运行
            watcher.start()
            logger.info("监控服务已启动，按 Ctrl+C 停止")

            # 保持运行
            while running:
                time.sleep(1)

    except Exception as e:
        logger.error(f"服务启动失败: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if watcher:
            watcher.stop()
        logger.info("市场监控服务已停止")


if __name__ == "__main__":
    main()
