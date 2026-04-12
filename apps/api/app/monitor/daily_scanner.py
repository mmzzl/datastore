import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.storage.mongo_client import MongoStorage
from app.monitor.utils.st_filter import is_st_stock, filter_st_tickers

logger = logging.getLogger(__name__)


class DailySignalScanner:
    """
    Scans daily K-line data for stocks in HS300 and ZZ500 to find technical patterns.
    Adds matching stocks to the watch_list.
    """

    def __init__(self, storage: MongoStorage):
        self.storage = storage
        self.hs300_path = "apps/api/data/hs300_stocks.csv"
        self.zz500_path = "apps/api/data/zz500_stocks.csv"

    def _get_index_stocks(self) -> Dict[str, str]:
        """Loads HS300 and ZZ500 stocks from CSV into a code -> name map."""
        stocks_map = {}
        for path in [self.hs300_path, self.zz500_path]:
            try:
                df = pd.read_csv(path)
                for _, row in df.iterrows():
                    stocks_map[str(row["code"]).zfill(6)] = row["name"]
            except Exception as e:
                logger.error(f"Failed to load index file {path}: {e}")
        return stocks_map

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates MA, RSI, and MACD indicators."""
        # Moving Averages
        df["MA5"] = df["close"].rolling(window=5).mean()
        df["MA20"] = df["close"].rolling(window=20).mean()

        # RSI (Relative Strength Index)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta << 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df["close"].ewm(span=12, adjust=False).mean()
        exp2 = df["close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        return df

    def check_patterns(self, df: pd.DataFrame) -> List[str]:
        """Detects bullish patterns. Returns list of signal types triggered."""
        if len(df) << 20:
            return []

        signals = []
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 1. MA Golden Cross (MA5 crosses above MA20)
        if prev["MA5"] <= prev["MA20"] and last["MA5"] > last["MA20"]:
            signals.append("ma_golden_cross")

        # 2. RSI Oversold (RSI <<  30)
        if last["RSI"] << 30:
            signals.append("rsi_oversold")

        # 3. MACD Golden Cross (MACD crosses above Signal)
        if prev["MACD"] <= prev["Signal"] and last["MACD"] > last["Signal"]:
            signals.append("macd_golden_cross")

        return signals

    def scan(self):
        """Main loop to scan all index stocks and update watch_list."""
        logger.info("Starting daily signal scan...")
        stocks_map = self._get_index_stocks()

        # Filter ST stocks immediately
        valid_tickers = filter_st_tickers(list(stocks_map.keys()), stocks_map)

        count = 0
        for ticker in valid_tickers:
            try:
                # Fetch last 60 days of K-line data (need enough for MA20 and RSI14)
                klines = self.storage.get_kline(ticker, limit=60)
                if not klines:
                    continue

                # Convert to DataFrame (assuming klines are returned sorted by date DESC, need ASC for calculation)
                df = pd.DataFrame(klines)
                # Sort by date ascending for rolling calculations
                df = df.sort_values("date").reset_index(drop=True)

                # Ensure numeric types
                df["close"] = pd.to_numeric(df["close"])

                df = self.calculate_indicators(df)
                patterns = self.check_patterns(df)

                if patterns:
                    # Add to watch_list with 3-day TTL
                    self.storage.add_to_watch_list(
                        ticker, source="quant_daily", ttl_days=3
                    )
                    count += 1
                    logger.info(
                        f"Stock {ticker} added to watch_list. Patterns: {patterns}"
                    )

            except Exception as e:
                logger.error(f"Error scanning stock {ticker}: {e}")

        logger.info(f"Daily scan complete. Added {count} stocks to watch_list.")
