"""
行业标准化模块
解决 DeepSeek 返回板块信息不规范的问题
"""
import os
import pandas as pd
import re
from typing import List, Dict, Optional, Set
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class IndustryNormalizer:
    """行业标准化器"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化行业标准化器
        
        Args:
            data_dir: 数据目录路径，默认为项目data目录
        """
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        self.csv_path = os.path.join(base_dir, "data", "all_stock_industry.csv")
        logger.info("csv_path: %s", self.csv_path)
        self._load_industry_data()
    
    def _load_industry_data(self):
        """加载行业数据"""
        try:
            # 加载板块-股票映射数据
            sector_stock_path = self.csv_path
            self.sector_industry_df = pd.read_csv(sector_stock_path, encoding='utf-8')
            self.sector_industry_df = self.sector_industry_df.rename(
                columns={
                    "板块名称": "sector",
                    "名称": "stock",
                    "板块代码": "sector_code",
                    "代码": "stock_code",
                }
            )
            logger.info(f"加载板块-股票映射数据: {len(self.sector_industry_df)} 条记录")
        except Exception as e:
            logger.error(f"加载行业数据失败: {e}")
            self.stock_industry_df = pd.DataFrame()
    
    def get_industry_name(self, sector_code: str) -> Optional[str]:
        """根据板块代码获取行业名称"""
        if self.sector_industry_df.empty:
            return None
            
        stock_row = self.sector_industry_df[self.sector_industry_df['sector_code'] == sector_code]
        if not stock_row.empty:
            return stock_row.iloc[0]['sector']
        return None
    
    def get_stock_name(self, sector: str) -> Optional[List[str]]:
        """根据板块获取股票名称"""
        if self.sector_industry_df.empty:
            return None
        stock_row = self.sector_industry_df[self.sector_industry_df['sector'] == sector]
        if not stock_row.empty:
            return stock_row['stock'].tolist()
        return None
    
    def get_stock_codes(self, sector: str) -> Optional[List[str]]:
        """根据板块获取股票代码列表"""
        if self.sector_industry_df.empty:
            return None
        stock_row = self.sector_industry_df[self.sector_industry_df['sector'] == sector]
        if not stock_row.empty:
            codes = stock_row['stock_code'].tolist()
            # 格式化股票代码为baostock格式（sh.600000 或 sz.000001）
            formatted_codes = []
            for code in codes:
                if pd.isna(code):
                    continue
                code_str = str(int(code)) if pd.notna(code) else ""
                if len(code_str) == 6:
                    if int(code_str) >= 600000:
                        formatted_codes.append(f"sh.{code_str}")
                    else:
                        formatted_codes.append(f"sz.{code_str}")
            return formatted_codes
        return None
    
    def get_stock_sector(self, symbol: str) -> Optional[str]:
        """根据股票代码获取所属板块"""
        if self.sector_industry_df.empty:
            return None
        
        # 提取6位数字代码
        code_match = re.search(r'\d{6}', symbol)
        if not code_match:
            return None
        
        code = code_match.group()
        
        # 查找股票代码对应的板块
        stock_row = self.sector_industry_df[self.sector_industry_df['stock_code'].astype(str) == code]
        if not stock_row.empty:
            return stock_row.iloc[0]['sector']
        return None
    
    def get_stock_name_by_code(self, symbol: str) -> Optional[str]:
        """根据股票代码获取股票名称"""
        if self.sector_industry_df.empty:
            return None
        
        # 提取6位数字代码
        code_match = re.search(r'\d{6}', symbol)
        if not code_match:
            return None
        
        code = code_match.group()
        
        # 查找股票代码对应的名称
        stock_row = self.sector_industry_df[self.sector_industry_df['stock_code'].astype(str) == code]
        if not stock_row.empty:
            return stock_row.iloc[0]['stock']
        return None
