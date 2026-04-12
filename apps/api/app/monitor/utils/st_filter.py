import logging
from typing import List

logger = logging.getLogger(__name__)


def is_st_stock(stock_name: str) -> bool:
    """
    Check if a stock is an ST stock.
    ST stocks usually have 'ST' or '*ST' in their name.
    """
    if not stock_name:
        return False

    name_upper = stock_name.upper()
    return "ST" in name_upper


def filter_st_stocks(stocks: List[dict], name_field: str = "name") -> List[dict]:
    """
    Filter out ST stocks from a list of stock dictionaries.

    :param stocks: List of stock dictionaries containing a name field.
    :param name_field: The key in the dictionary that holds the stock name.
    :return: A filtered list containing only non-ST stocks.
    """
    filtered = [s for s in stocks if not is_st_stock(s.get(name_field, ""))]

    removed_count = len(stocks) - len(filtered)
    if removed_count > 0:
        logger.debug(f"Filtered out {removed_count} ST stocks from list.")

    return filtered


def filter_st_tickers(tickers: List[str], name_map: dict) -> List[str]:
    """
    Filter ST stocks given a list of tickers and a mapping of ticker -> name.

    :param tickers: List of stock codes.
    :param name_map: Dictionary mapping stock codes to their names.
    :return: List of non-ST tickers.
    """
    return [t for t in tickers if not is_st_stock(name_map.get(t, ""))]
