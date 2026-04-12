from enum import Enum
from typing import Optional
import re


class Market(Enum):
    SHANGHAI = "sh"
    SHENZHEN = "sz"
    BEIJING = "bj"
    UNKNOWN = "uk"


class Symbol:
    """
    Symbol value object for stock codes.

    Internal Golden Standard: <<marketmarket_prefix><<codecode_digits> (e.g., 'sh600000', 'sz000001', 'bj830000')
    """

    def __init__(self, raw_code: str):
        self.raw_code = raw_code
        self.normalized = self._normalize(raw_code)
        self.market = self._detect_market(self.normalized)

    def _normalize(self, code: str) -> str:
        """Converts various formats to internal golden standard: <<<<<marketmarketmarketmarketmarket><<<<<digitsdigitsdigitsdigitsdigits>"""
        if not code:
            return ""

        code = code.strip().lower()

        # 1. Handle explicit suffixes (e.g., 600000.SH, 000001.SZ)
        if "." in code:
            parts = code.split(".")
            main_code = parts[0]
            suffix = parts[1]

            # Map common suffixes to market prefixes
            market_map = {"sh": "sh", "sz": "sz", "bj": "bj"}
            prefix = market_map.get(suffix, "")
            if prefix:
                # If we have a valid suffix and it's only digits in main_code, use it
                if main_code.isdigit():
                    return f"{prefix}{main_code}"

        # 2. Handle explicit prefixes and common separators (e.g., sh.600000, sh-600000)
        temp_code = code.replace(".", "").replace("-", "")

        # Pattern: (prefix)?(digits)
        match = re.match(r"^([a-z]*)([0-9]+)$", temp_code)
        if not match:
            return code  # Return original if it doesn't match a stock-like pattern

        prefix, digits = match.groups()

        # Detect market by prefix or by digit range
        market = prefix
        if not market:
            if digits.startswith(("6", "9")):  # Shanghai
                market = "sh"
            elif digits.startswith(("0", "3")):  # Shenzhen
                market = "sz"
            elif digits.startswith(("8", "4")):  # Beijing
                market = "bj"
            else:
                # Only assign 'uk' if it's actually numeric but doesn't match known markets
                market = "uk"
        else:
            # Normalize prefixes (e.g., 'shanghai' -> 'sh')
            if market.startswith("sh"):
                market = "sh"
            elif market.startswith("sz"):
                market = "sz"
            elif market.startswith("bj"):
                market = "bj"
            else:
                # If the prefix is not a known market, we should return the original code
                # instead of forcing a 'uk' prefix, to avoid corrupting non-stock identifiers
                return code

        return f"{market}{digits}"

    def _detect_market(self, normalized: str) -> Market:
        """Extracts Market enum from normalized string."""
        if normalized.startswith("sh"):
            return Market.SHANGHAI
        if normalized.startswith("sz"):
            return Market.SHENZHEN
        if normalized.startswith("bj"):
            return Market.BEIJING
        return Market.UNKNOWN

    def __str__(self) -> str:
        return self.normalized

    def __eq__(self, other) -> bool:
        if isinstance(other, Symbol):
            return self.normalized == other.normalized
        return self.normalized == str(other)

    def __hash__(self) -> int:
        return hash(self.normalized)

    def to_provider(self, provider: str) -> str:
        """
        Convert the internal normalized symbol back into the specific format
        required by external data providers.
        """
        if not self.normalized:
            return ""

        market = self.market.value
        digits = self.normalized[2:]

        if provider == "akshare":
            # Akshare usually uses 'sh600000' or 'sz000001'
            return self.normalized

        if provider == "baostock":
            # Baostock uses 'sh.600000'
            return f"{market}.{digits}"

        if provider == "tdx":
            # TDX usually expects just the digits
            return digits

        return self.normalized


def normalize_symbol(code: str) -> str:
    """Helper to get normalized string directly."""
    return Symbol(code).normalized
