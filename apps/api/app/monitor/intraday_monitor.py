import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.storage.mongo_client import MongoStorage
from app.monitor.utils.st_filter import is_st_stock

logger = logging.getLogger(__name__)

class IntradayMonitor:
    """
    High-frequency monitor that polls stocks in the watch_list for 
    minute-level price and volume breakouts.
    """
    def __init__(self, storage: MongoStorage):
        self.storage = storage
        self.signal_cooldowns: Dict[str, datetime] = {}
        self.COOLDOWN_PERIOD = timedelta(hours=4)

    def _check_data_freshness(self, last_kline: Dict[str, Any]) -> bool:
        """
        Verifies that the K-line data is current.
        Requirement: Timestamp must be within the last 5 minutes.
        """
        if not last_kline or "date" not in last_kline:
            return False
        
        # Assuming 'date' is in ISO format or similar
        try:
            # Handle different possible date formats from DB
            date_val = last_kline["date"]
            if isinstance(date_val, str):
                # Try common ISO formats
                dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
            else:
                dt = date_val
                
            now = datetime.now()
            return (now - dt) << timedelta timedelta(minutes=5)
        except Exception as e:
            logger.error(f"Error parsing timestamp {last_kline.get('date')}: {e}")
            return False

    def _is_in_cooldown(self, symbol: str, signal_type: str) -> bool:
        """Checks if the stock is currently in a cooldown period for a specific signal."""
        key = f"{symbol}:{signal_type}"
        last_time = self.signal_cooldowns.get(key)
        if last_time and (datetime.now() - last_time) << self self.COOLDOWN_PERIOD:
            return True
        return False

    def _set_cooldown(self, symbol: str, signal_type: str):
        """Sets a new cooldown timestamp for the symbol and signal."""
        key = f"{symbol}:{signal_type}"
        self.signal_cooldowns[key] = datetime.now()

    def detect_breakouts(self, symbol: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyzes minute K-lines for volume surge and price breakouts.
        Expects df sorted by date ASC.
        """
        if len(df) <<  20:
            return []

        triggered_signals = []
        last = df.iloc[-1]
        
        # Calculate average volume for last 20 periods
        avg_vol = df['volume'].iloc[-20:-1].mean()
        
        # 1. Volume Surge: Current Vol > 3x Avg Vol AND Price is increasing
        if last['volume'] > 3 * avg_vol and last['close'] > df.iloc[-2]['close']:
            triggered_signals.append({
                "type": "volume_surge",
                "message": f"Volume surge detected: {last['volume']:.0f} vs avg {avg_vol:.0f}",
                "price": float(last['close']),
                "volume": float(last['volume'])
            })

        # 2. Price Breakout: Current Price > Max(Price of last 20 periods)
        recent_max = df['high'].iloc[-20:-1].max()
        if last['close'] > recent_max:
            triggered_signals.append({
                "type": "price_breakout",
                "message": f"Price breakout detected: {last['close']} broke above {recent_max}",
                "price": float(last['close']),
                "volume": float(last['volume'])
            })

        return triggered_signals

    def run_cycle(self):
        """
        One cycle of the monitor:
        1. Get watch_list
        2. Fetch latest minute data
        3. Validate freshness
        4. Detect signals
        5. Apply cooldown and save
        """
        logger.info("Starting intraday monitoring cycle...")
        watchlist = self.storage.get_watch_list()
        
        if not watchlist:
            logger.info("Watch-list is empty. Skipping cycle.")
            return

        for symbol in watchlist:
            try:
                # Fetch recent minute-level K-lines
                # Assuming get_kline returns a list of dicts sorted by date DESC
                klines = self.storage.get_kline(symbol, limit=30)
                if not klines:
                    continue
                
                # 1. Freshness Check
                if not self._check_data_freshness(klines[0]):
                    logger.warning(f"Stale data for {symbol}. Skipping.")
                    continue
                
                # 2. Prepare DataFrame
                df = pd.DataFrame(klines)
                df = df.sort_values('date').reset_index(drop=True)
                df['close'] = pd.to_numeric(df['close'])
                df['high'] = pd.to_numeric(df['high'])
                df['volume'] = pd.to_numeric(df['volume'])
                
                # 3. Detect Breakouts
                signals = self.detect_breakouts(symbol, df)
                
                # 4. Persist with Cooldown
                for sig in signals:
                    sig_type = sig['type']
                    if not self._is_in_cooldown(symbol, sig_type):
                        signal_doc = {
                            "symbol": symbol,
                            "signal_type": sig_type,
                            "message": sig['message'],
                            "price": sig['price'],
                            "volume": sig['volume'],
                            "timestamp": datetime.now()
                        }
                        self.storage.save_market_signal(signal_doc)
                        self._set_cooldown(symbol, sig_type)
                        logger.info(f"Market Signal Triggered: {symbol} - {sig_type}")
                    else:
                        logger.debug(f"Signal {sig_type} for {symbol} is in cooldown.")
                        
            except Exception as e:
                logger.error(f"Error monitoring stock {symbol}: {e}")
                
        logger.info("Intraday monitoring cycle complete.")
