"""
Stock Pool Service

Manages stock pool data (HS300, ZZ500, All Market).
Loads data from CSV files with caching.
"""

import logging
import os
import time
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Default data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
DATA_DIR = os.path.normpath(DATA_DIR)


class StockPoolService:
    """
    Service for managing stock pool data.

    Provides access to stock lists (HS300, ZZ500, All Market) and
    industry classification data with memory caching.
    """

    CACHE_TTL = 3600  # 1 hour cache TTL

    def __init__(self, data_dir: str = None):
        """
        Initialize StockPoolService.

        Args:
            data_dir: Directory containing CSV data files.
                     Defaults to apps/api/data/
        """
        self.data_dir = data_dir or DATA_DIR
        self._pool_cache: Dict[str, List[str]] = {}
        self._pool_cache_time: Dict[str, float] = {}
        self._industry_cache: Optional[Dict[str, str]] = None
        self._name_cache: Optional[Dict[str, str]] = None

    def _load_pool_csv(self, filename: str) -> List[str]:
        """
        Load stock codes from CSV file.

        Args:
            filename: CSV filename

        Returns:
            List of stock codes
        """
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Stock pool file not found: {filepath}")
            return []

        try:
            df = pd.read_csv(filepath)
            if "code" in df.columns:
                codes = df["code"].astype(str).str.strip().tolist()
                logger.info(f"Loaded {len(codes)} stocks from {filename}")
                return codes
            else:
                logger.warning(f"No 'code' column in {filename}")
                return []
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return []

    def get_codes(self, pool_type: str) -> List[str]:
        """
        Get stock codes for a pool type.

        Args:
            pool_type: Pool type (hs300, zz500, all)

        Returns:
            List of stock codes
        """
        now = time.time()
        pool_type = pool_type.lower()

        # Check cache
        if pool_type in self._pool_cache:
            if now - self._pool_cache_time.get(pool_type, 0) < self.CACHE_TTL:
                return self._pool_cache[pool_type]

        # Load based on pool type
        if pool_type == "hs300":
            codes = self._load_pool_csv("hs300_stocks.csv")
        elif pool_type == "zz500":
            codes = self._load_pool_csv("zz500_stocks.csv")
        elif pool_type == "all":
            # Combine HS300 and ZZ500 for "all" market (excluding ST)
            hs300 = self._load_pool_csv("hs300_stocks.csv")
            zz500 = self._load_pool_csv("zz500_stocks.csv")
            # Remove duplicates
            codes = list(set(hs300 + zz500))
            # Filter out ST stocks (codes starting with *ST or ST)
            codes = [c for c in codes if not self._is_st_stock(c)]
        else:
            logger.warning(f"Unknown pool type: {pool_type}")
            return []

        # Update cache
        self._pool_cache[pool_type] = codes
        self._pool_cache_time[pool_type] = now

        return codes

    def _is_st_stock(self, code: str) -> bool:
        """Check if a stock is ST (Special Treatment)."""
        # ST stocks are identified by name, not code
        # For now, we'll check via name cache if available
        if self._name_cache and code in self._name_cache:
            name = self._name_cache[code]
            return "ST" in name or "*ST" in name
        return False

    def load_industry_map(self) -> Dict[str, str]:
        """
        Load industry classification map (code -> industry).

        Returns:
            Dictionary mapping stock code to industry name
        """
        if self._industry_cache is not None:
            return self._industry_cache

        filepath = os.path.join(self.data_dir, "stock_industry.csv")
        if not os.path.exists(filepath):
            logger.warning(f"Industry file not found: {filepath}")
            return {}

        try:
            df = pd.read_csv(filepath)
            industry_map = {}

            for _, row in df.iterrows():
                code = str(row.get("code", "")).strip()
                # Handle both sh.600000 and 600000 formats
                if "." in code:
                    code = code.split(".")[-1]

                industry = str(row.get("industry", "")).strip()
                # Simplify industry name (extract main category)
                if industry:
                    # Industry format: "J66货币金融服务" -> "银行"
                    # We'll use a simplified mapping
                    simplified = self._simplify_industry(industry)
                    industry_map[code] = simplified

            self._industry_cache = industry_map
            logger.info(f"Loaded industry map with {len(industry_map)} entries")
            return industry_map

        except Exception as e:
            logger.error(f"Failed to load industry map: {e}")
            return {}

    def _simplify_industry(self, industry: str) -> str:
        """
        Simplify industry name.

        Args:
            industry: Full industry classification string

        Returns:
            Simplified industry name
        """
        # Industry mapping based on CSRC classification
        industry_mapping = {
            "银行": "银行",
            "证券": "证券",
            "保险": "保险",
            "货币金融": "银行",
            "资本市场": "证券",
            "白酒": "白酒",
            "酒": "白酒",
            "饮料": "饮料",
            "食品": "食品",
            "医药": "医药",
            "医疗": "医药",
            "生物": "生物制药",
            "电子": "电子",
            "计算机": "计算机",
            "通信": "通信",
            "软件": "软件",
            "互联网": "互联网",
            "传媒": "传媒",
            "电力": "电力",
            "电气": "电气设备",
            "机械": "机械",
            "汽车": "汽车",
            "房地产": "房地产",
            "建筑": "建筑",
            "建材": "建材",
            "钢铁": "钢铁",
            "有色": "有色金属",
            "煤炭": "煤炭",
            "石油": "石油",
            "化工": "化工",
            "军工": "军工",
            "航空": "航空",
            "港口": "港口",
            "铁路": "铁路",
            "公路": "公路",
            "物流": "物流",
            "商业": "商业",
            "零售": "零售",
            "家电": "家电",
            "纺织": "纺织",
            "服装": "服装",
            "造纸": "造纸",
            "环保": "环保",
            "水务": "水务",
        }

        # Find matching industry
        for key, value in industry_mapping.items():
            if key in industry:
                return value

        # Return first part before any separator if no match
        return industry.split("、")[0].split("和")[0][:4] if industry else "其他"

    def get_industry(self, code: str) -> str:
        """
        Get industry for a stock code.

        Args:
            code: Stock code

        Returns:
            Industry name or empty string
        """
        if self._industry_cache is None:
            self.load_industry_map()

        # Normalize code
        pure_code = code.split(".")[-1] if "." in code else code
        pure_code = pure_code.replace("SH", "").replace("SZ", "").replace("sh", "").replace("sz", "")

        return self._industry_cache.get(pure_code, "")

    def load_name_map(self) -> Dict[str, str]:
        """
        Load stock name map (code -> name).

        Returns:
            Dictionary mapping stock code to name
        """
        if self._name_cache is not None:
            return self._name_cache

        filepath = os.path.join(self.data_dir, "stock_industry.csv")
        if not os.path.exists(filepath):
            return {}

        try:
            df = pd.read_csv(filepath)
            name_map = {}

            for _, row in df.iterrows():
                code = str(row.get("code", "")).strip()
                if "." in code:
                    code = code.split(".")[-1]
                name = str(row.get("code_name", "")).strip()
                if code and name:
                    name_map[code] = name

            self._name_cache = name_map
            return name_map

        except Exception as e:
            logger.error(f"Failed to load name map: {e}")
            return {}

    def get_stock_name(self, code: str) -> str:
        """
        Get stock name by code.

        Args:
            code: Stock code

        Returns:
            Stock name or code if not found
        """
        if self._name_cache is None:
            self.load_name_map()

        pure_code = code.split(".")[-1] if "." in code else code
        pure_code = pure_code.replace("SH", "").replace("SZ", "").replace("sh", "").replace("sz", "")

        return self._name_cache.get(pure_code, code)

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._pool_cache.clear()
        self._pool_cache_time.clear()
        self._industry_cache = None
        self._name_cache = None
        logger.info("Stock pool cache cleared")
