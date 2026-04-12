import csv
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class IndustryMapper:
    """
    Maps BK codes to industry names and their corresponding stock lists.
    Loads data from a CSV file into a memory map for fast lookups.
    """

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.mapping: Dict[str, Dict] = {}
        self.load_mapping()

    def load_mapping(self):
        """
        Loads the CSV file and builds a dictionary:
        { "BK123": { "name": "Sector Name", "stocks": ["600...", "000..."] } }
        """
        try:
            with open(self.csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    bk_code = row["板块代码"]
                    industry_name = row["板块名称"]
                    stock_code = row["代码"]

                    if bk_code not in self.mapping:
                        self.mapping[bk_code] = {"name": industry_name, "stocks": []}

                    if stock_code not in self.mapping[bk_code]["stocks"]:
                        self.mapping[bk_code]["stocks"].append(stock_code)

            logger.info(
                f"Successfully loaded industry mapping from {self.csv_path}. Total sectors: {len(self.mapping)}"
            )
        except Exception as e:
            logger.error(f"Failed to load industry mapping from {self.csv_path}: {e}")
            raise

    def get_stocks_by_bk_code(self, bk_code: str) -> List[str]:
        """Returns the list of stock codes for a given BK code."""
        sector = self.mapping.get(bk_code)
        return sector["stocks"] if sector else []

    def get_industry_name(self, bk_code: str) -> Optional[str]:
        """Returns the industry name for a given BK code."""
        sector = self.mapping.get(bk_code)
        return sector["name"] if sector else None
