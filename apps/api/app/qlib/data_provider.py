"""
MongoDB Data Provider for Qlib

This module provides a custom data provider that loads K-line data
from MongoDB and converts it to Qlib-compatible format.
"""

import pandas as pd
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..data_source import DataSourceManager
from ..data_source.models import StockKLine

logger = logging.getLogger(__name__)


class MongoDataProvider:
    """
    Provides K-line data from MongoDB to Qlib.
    
    This class bridges the existing MongoDB K-line data storage
    with Qlib's data interface, enabling ML model training
    without duplicating data.
    
    Example:
        >>> provider = MongoDataProvider(data_manager)
        >>> df = provider.load_data(
        ...     instruments=["SH600000", "SH600519"],
        ...     start_time="2020-01-01",
        ...     end_time="2026-01-01"
        ... )
    """
    
    def __init__(
        self,
        data_manager: Optional[DataSourceManager] = None,
        mongo_adapter = None,
    ):
        """
        Initialize the data provider.
        
        Args:
            data_manager: DataSourceManager instance for unified data access
            mongo_adapter: Direct MongoDB adapter (alternative to data_manager)
        """
        self.data_manager = data_manager
        self.mongo_adapter = mongo_adapter
        self._cache: Dict[str, pd.DataFrame] = {}
        
        if data_manager is None and mongo_adapter is None:
            from ..data_source import DataSourceManager
            self.data_manager = DataSourceManager()
    
    def load_data(
        self,
        instruments: List[str],
        start_time: str,
        end_time: str,
        frequency: str = "day",
        adjust_flag: str = "3",
    ) -> pd.DataFrame:
        """
        Load K-line data from MongoDB for the specified instruments.
        
        Args:
            instruments: List of stock codes (e.g., ["SH600000", "SH600519"])
            start_time: Start date string (e.g., "2020-01-01")
            end_time: End date string (e.g., "2026-01-01")
            frequency: Data frequency ("day", "week", "month")
            adjust_flag: Adjustment type ("3" for forward adjusted)
        
        Returns:
            DataFrame with MultiIndex (datetime, instrument) and columns:
            - open, high, low, close, volume, amount
        
        Raises:
            ValueError: If no instruments provided or invalid date range
        """
        if not instruments:
            raise ValueError("No instruments provided")
        
        all_data = []
        
        for instrument in instruments:
            try:
                klines = self._get_klines_for_instrument(
                    code=instrument,
                    start_date=start_time,
                    end_date=end_time,
                    frequency=frequency,
                    adjust_flag=adjust_flag,
                )
                
                if not klines:
                    logger.warning(f"No data found for {instrument} in range {start_time} to {end_time}")
                    continue
                
                for kline in klines:
                    all_data.append({
                        "datetime": pd.to_datetime(kline.date),
                        "instrument": kline.code,
                        "open": float(kline.open),
                        "high": float(kline.high),
                        "low": float(kline.low),
                        "close": float(kline.close),
                        "volume": int(kline.volume),
                        "amount": float(kline.amount) if kline.amount else 0.0,
                    })
                    
            except Exception as e:
                logger.error(f"Error loading data for {instrument}: {e}")
                continue
        
        if not all_data:
            logger.warning(f"No data loaded for any instruments")
            return pd.DataFrame(columns=["datetime", "instrument", "open", "high", "low", "close", "volume", "amount"])
        
        df = pd.DataFrame(all_data)
        df = df.set_index(["datetime", "instrument"])
        df = df.sort_index()
        
        logger.info(f"Loaded {len(df)} records for {len(instruments)} instruments")
        return df
    
    def _get_klines_for_instrument(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str,
        adjust_flag: str,
    ) -> List[StockKLine]:
        """
        Get K-line data for a single instrument.
        
        Priority:
        1. Use mongo_adapter directly if available
        2. Use data_manager.get_kline() with provider="mongodb"
        """
        if self.mongo_adapter:
            return self.mongo_adapter.get_kline(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjust_flag=adjust_flag,
            )
        
        if self.data_manager:
            return self.data_manager.get_kline(
                code=code,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjust_flag=adjust_flag,
                provider="mongodb",
            )
        
        return []
    
    def get_instruments_df(self, instruments: List[str]) -> pd.DataFrame:
        """
        Get instrument metadata as DataFrame.
        
        Args:
            instruments: List of instrument codes
        
        Returns:
            DataFrame with instrument information
        """
        instrument_data = []
        
        for code in instruments:
            stock_info = None
            if self.data_manager:
                stock_info = self.data_manager.get_stock_info(code)
            
            if stock_info:
                instrument_data.append({
                    "instrument": code,
                    "name": stock_info.name or code,
                    "exchange": stock_info.exchange or code[:2],
                })
            else:
                instrument_data.append({
                    "instrument": code,
                    "name": code,
                    "exchange": code[:2],
                })
        
        return pd.DataFrame(instrument_data)
    
    def prepare_for_qlib(
        self,
        instruments: List[str],
        start_time: str,
        end_time: str,
        factor_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare Qlib Dataset configuration.
        
        This method creates the configuration dictionary needed
        to initialize a Qlib DatasetH with custom handler.
        
        Args:
            instruments: List of stock codes
            start_time: Start date for data
            end_time: End date for data
            factor_config: Optional custom factor configuration
        
        Returns:
            Qlib Dataset configuration dictionary
        """
        config = {
            "class": "qlib.data.dataset.DatasetH",
            "module_path": "qlib.data.dataset",
            "kwargs": {
                "handler": {
                    "class": "qlib.contrib.data.handler.Alpha158",
                    "module_path": "qlib.contrib.data.handler",
                    "kwargs": {
                        "start_time": start_time,
                        "end_time": end_time,
                        "fit_start_time": start_time,
                        "fit_end_time": end_time,
                        "instruments": instruments,
                    },
                },
                "segments": {
                    "train": (start_time, self._calc_split_date(end_time, 0.6)),
                    "valid": (self._calc_split_date(end_time, 0.6), self._calc_split_date(end_time, 0.8)),
                    "test": (self._calc_split_date(end_time, 0.8), end_time),
                },
            },
        }
        
        if factor_config:
            config["kwargs"]["handler"]["kwargs"].update(factor_config)
        
        return config
    
    def _calc_split_date(self, end_date: str, ratio: float) -> str:
        """
        Calculate split date based on ratio.
        
        Args:
            end_date: End date string
            ratio: Ratio of data to use (0.0 to 1.0)
        
        Returns:
            Split date string
        """
        end_dt = pd.to_datetime(end_date)
        start_dt = end_dt - pd.DateOffset(years=5)
        total_days = (end_dt - start_dt).days
        split_dt = start_dt + pd.Timedelta(days=int(total_days * ratio))
        return split_dt.strftime("%Y-%m-%d")
    
    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        logger.debug("Cache cleared")
