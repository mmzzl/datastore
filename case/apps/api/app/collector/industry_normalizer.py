"""
行业标准化模块
解决 DeepSeek 返回板块信息不规范的问题
"""

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
        if data_dir is None:
            # 默认数据目录
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        self._load_industry_data()
        self._build_mapping_tables()
    
    def _load_industry_data(self):
        """加载行业数据"""
        try:
            # 加载板块-股票映射数据
            sector_stock_path = self.data_dir / "all_stock_industry.csv"
            if sector_stock_path.exists():
                self.sector_stock_df = pd.read_csv(sector_stock_path, encoding='utf-8')
                logger.info(f"加载板块-股票映射数据: {len(self.sector_stock_df)} 条记录")
            else:
                logger.warning(f"板块-股票映射文件不存在: {sector_stock_path}")
                self.sector_stock_df = pd.DataFrame()
            
            # 加载股票-行业分类数据
            stock_industry_path = self.data_dir / "stock_industry.csv"
            if stock_industry_path.exists():
                self.stock_industry_df = pd.read_csv(stock_industry_path, encoding='utf-8')
                logger.info(f"加载股票-行业分类数据: {len(self.stock_industry_df)} 条记录")
            else:
                logger.warning(f"股票-行业分类文件不存在: {stock_industry_path}")
                self.stock_industry_df = pd.DataFrame()
                
        except Exception as e:
            logger.error(f"加载行业数据失败: {e}")
            self.sector_stock1_df = pd.DataFrame()
            self.stock_industry_df = pd.DataFrame()
    
    def _build_mapping_tables(self):
        """构建映射表"""
        # 构建板块标准化映射
        self.sector_normalization_map = self._build_sector_normalization_map()
        
        # 构建行业标准化映射
        self.industry_normalization_map = self._build_industry_normalization_map()
        
        # 构建板块-行业映射
        self.sector_industry_map = self._build_sector_industry_map()
        
        # 构建股票-板块映射
        self.stock_sector_map = self._build_stock_sector_map()
        
        # 构建股票-行业映射
        self.stock_industry_map = self._build_stock_industry_map()
    
    def _build_sector_normalization_map(self) -> Dict[str, str]:
        """构建板块标准化映射表"""
        # DeepSeek 可能返回的板块名称 -> 标准板块名称
        mapping = {
            # 能源相关
            "能源": "能源",
            "油气": "油气",
            "石油": "石油",
            "煤炭": "煤炭",
            "采掘1": "采掘",
            "储能": "储能",
            "固态电池": "固态电池",
            "电池": "电池",
            "新能源": "新能源",
            "电力": "电力",
            
            # 科技相关
            "人工智能": "人工智能",
            "AI": "人工智能",
            "人工智能/金融科技": "人工智能",
            "金融科技": "金融科技",
            "计算机": "计算机",
            "软件": "软件",
            "信息技术": "信息技术",
            "半导体": "半导体",
            "芯片": "半导体",
            "电子": "电子",
            
            # 医药相关
            "医药": "医药生物",
            "医药生物": "医药生物",
            "医疗器械": "医疗器械",
            "生物医药": "医药生物",
            "医疗": "医药生物",
            
            # 消费相关
            "消费": "消费",
            "食品饮料": "食品饮料",
            "家用电器": "家用电器",
            "白酒": "食品饮料",
            "饮料": "食品饮料",
            
            # 金融相关
            "金融": "金融",
            "银行": "银行",
            "证券": "证券",
            "保险": "保险",
            
            # 其他
            "汽车": "汽车",
            "房地产": "房地产",
            "建筑": "建筑",
            "化工": "化工",
            "有色金属": "有色金属",
            "钢铁": "钢铁",
            "交通运输": "交通运输",
            "传媒": "传媒",
            "通信": "通信",
            "军工": "国防军工",
            "国防军工": "国防军工",
        }
        
        # 添加同义词映射
        synonyms = {
            "人工智能": ["AI", "智能", "机器学习", "深度学习"],
            "半导体": ["芯片", "集成电路", "IC"],
            "医药生物": ["医药", "生物医药", "医疗", "生物"],
            "食品饮料": ["白酒", "饮料", "食品", "酒类"],
            "新能源": ["新能源车", "新能源汽车", "光伏", "风电", "太阳能"],
            "储能": ["储能电池", "储能系统"],
            "固态电池": ["固态", "全固态电池"],
        }
        
        # 展开同义词
        for standard, syn_list in synonyms.items():
            for syn in syn_list:
                mapping[syn] = standard
        
        return mapping
    
    def _build_industry_normalization_map(self) -> Dict[str, str]:
        """构建行业标准化映射表"""
        if self.stock_industry_df.empty:
            return {}
        
        # 获取所有唯一的行业名称
        industries = self.stock_industry_df['industry'].dropna().unique()
        
        # 创建标准化映射
        mapping = {}
        for industry in industries:
            if pd.isna(industry):
                continue
            industry_str = str(industry).strip()
            # 行业名称本身作为标准
            mapping[industry_str] = industry_str
            
            # 添加常见变体
            if "医药" in industry_str:
                mapping[industry_str.replace("医药", "医疗")] = industry_str
                mapping[industry_str.replace("医药", "生物")] = industry_str
            
            if "电子" in industry_str:
                mapping[industry_str.replace("电子", "半导体")] = industry_str
            
            if "计算机" in industry_str:
                mapping[industry_str.replace("计算机", "软件")] = industry_str
        
        return mapping
    
    def _build_sector_industry_map(self) -> Dict[str, List[str]]:
        """构建板块-行业映射表"""
        mapping = {}
        
        # 基于规则映射
        sector_to_industry = {
            "人工智能": ["计算机", "软件", "信息技术"],
            "半导体": ["电子", "半导体"],
            "医药生物": ["医药生物", "医疗器械"],
            "新能源": ["电力设备", "新能源", "电池"],
            "储能": ["电力设备", "电池", "储能"],
            "固态电池": ["电池", "新能源材料", "化学制品"],
            "油气": ["石油", "采掘", "能源"],
            "煤炭": ["煤炭", "采掘", "能源"],
            "金融": ["银行", "证券", "保险", "金融"],
            "消费": ["食品饮料", "家用电器", "商业贸易"],
            "汽车": ["汽车", "汽车零部件"],
            "房地产": ["房地产", "建筑装饰"],
            "化工": ["化工", "化学制品"],
            "有色金属": ["有色金属", "钢铁"],
            "交通运输": ["交通运输", "物流"],
            "传媒": ["传媒", "文化传媒"],
            "通信": ["通信", "通信设备"],
            "国防军工": ["国防军工", "军工"],
        }
        
        # 从数据中学习映射
        if not self.sector_stock_df.empty and not self.stock_industry_df.empty:
            for sector in self.sector_stock_df['板块名称'].unique():
                if pd.isna(sector):
                    continue
                sector_str = str(sector).strip()
                
                # 获取该板块下的所有股票
                sector_stocks = self.sector_stock_df[
                    self.sector_stock_df['板块名称'] == sector
                ]['代码'].tolist()
                
                # 获取这些股票的行业
                industries = set()
                for stock in sector_stocks:
                    stock_industry = self.stock_industry_df[
                        self.stock_industry_df['code'] == stock
                    ]['industry'].unique()
                    industries.update(stock_industry)
                
                # 过滤空值
                industries = [ind for ind in industries if not pd.isna(ind)]
                if industries:
                    mapping[sector_str] = list(industries)
        
        # 合并规则映射
        for sector, industries in sector_to_industry.items():
            if sector not in mapping:
                mapping[sector] = industries
            else:
                mapping[sector].extend(industries)
                mapping[sector] = list(set(mapping[sector]))
        
        return mapping
    
    def _build_stock_sector_map(self) -> Dict[str, List[str]]:
        """构建股票-板块映射表"""
        if self.sector_stock_df.empty:
            return {}
        
        mapping = {}
        for _, row in self.sector_stock_df.iterrows():
            stock_code = str(row['代码']).strip()
            sector = str(row['板块名称']).strip()
            
            if stock_code not in mapping:
                mapping[stock_code] = []
            
            if sector not in mapping[stock_code]:
                mapping[stock_code].append(sector)
        
        return mapping
    
    def _build_stock_industry_map(self) -> Dict[str, str]:
        """构建股票-行业映射表"""
        if self.stock_industry_df.empty:
            return {}
        
        mapping = {}
        for _, row in self.stock_industry_df.iterrows():
            stock_code = str(row['code']).strip()
            industry = str(row['industry']).strip()
            
            if not pd.isna(industry):
                mapping[stock_code] = industry
        
        return mapping
    
    def normalize_sector(self, raw_sector: str) -> str:
        """
        标准化板块名称
        
        Args:
            raw_sector: 原始板块名称
            
        Returns:
            标准化后的板块名称
        """
        if not raw_sector or pd.isna(raw_sector):
            return "未知板块"
        
        raw_sector_str = str(raw_sector).strip()
        
        # 1. 清理特殊字符
        cleaned = re.sub(r'[【】\[\]()（）,，、/]', '', raw_sector_str)
        
        # 2. 分割多个板块
        sectors = re.split(r'[，,、/]', cleaned)
        
        # 3. 标准化每个板块
        normalized_sectors = []
        for sector in sectors:
            sector = sector.strip()
            if not sector:
                continue
            
            # 查找映射
            normalized = self.sector_normalization_map.get(sector, None)
            if normalized:
                normalized_sectors.append(normalized)
            else:
                # 模糊匹配
                for key, value in self.sector_normalization_map.items():
                    if key in sector or sector in key:
                        normalized_sectors.append(value)
                        break
                else:
                    # 未匹配到，保留原样
                    normalized_sectors.append(sector)
        
        # 4. 去重并返回
        unique_sectors = list(set(normalized_sectors))
        return "、".join(unique_sectors) if unique_sectors else "未知板块"
    
    def normalize_industry(self, raw_industry: str) -> str:
        """
        标准化行业名称
        
        Args:
            raw_industry: 原始行业名称
            
        Returns:
            标准化后的行业名称
        """
        if not raw_industry or pd.isna(raw_industry):
            return "未知行业"
        
        raw_industry_str = str(raw_industry).strip()
        
        # 直接查找映射
        normalized = self.industry_normalization_map.get(raw_industry_str, None)
        if normalized:
            return normalized
        
        # 模糊匹配
        for key, value in self.industry_normalization_map.items():
            if key in raw_industry_str or raw_industry_str in key:
                return value
        
        # 未匹配到，返回原样
        return raw_industry_str
    
    def get_stocks_by_sector(self, sector: str) -> List[str]:
        """
        根据板块获取股票列表
        
        Args:
            sector: 板块名称
            
        Returns:
            股票代码列表
        """
        normalized_sector = self.normalize_sector(sector)
        
        if self.sector_stock_df.empty:
            return []
        
        # 查找股票
        stocks = self.sector_stock_df[
            self.sector_stock_df['板块名称'] == normalized_sector
        ]['代码'].tolist()
        
        # 转换为标准格式
        standardized_stocks = []
        for stock in stocks:
            if pd.isna(stock):
                continue
            stock_str = str(stock).strip()
            # 确保是6位代码
            if len(stock_str) == 6 and stock_str.isdigit():
                if stock_str.startswith('6'):
                    standardized_stocks.append(f"sh{stock_str}")
                else:
                    standardized_stocks.append(f"sz{stock_str}")
        
        return list(set(standardized_stocks))
    
    def get_industries_by_sector(self, sector: str) -> List[str]:
        """
        根据板块获取相关行业
        
        Args:
            sector: 板块名称
            
        Returns:
            行业列表
        """
        normalized_sector = self.normalize_sector(sector)
        return self.sector_industry_map.get(normalized_sector, [])
    
    def get_sectors_by_stock(self, stock_code: str) -> List[str]:
        """
        根据股票获取所属板块
        
        Args:
            stock_code: 股票代码
            
        Returns:
            板块列表
        """
        # 标准化股票代码
        if stock_code.startswith('sh') or stock_code.startswith('sz'):
            code = stock_code[2:]
        else:
            code = stock_code
        
        return self.stock_sector_map.get(code, [])
    
    def get_industry_by_stock(self, stock_code: str) -> str:
        """
        根据股票获取所属行业
        
        Args:
            stock_code: 股票代码
            
        Returns:
            行业名称
        """
        # 标准化股票代码
        if stock_code.startswith('sh') or stock_code.startswith('sz'):
            code = stock_code[2:]
        else:
            code = stock_code
        
        return self.stock_industry_map.get(code, "未知行业")
    
    def analyze_deepseek_response(self, deepseek_text: str) -> Dict:
        """
        分析 DeepSeek 返回的文本，提取板块和股票信息
        
        Args:
            deepseek_text: DeepSeek 返回的文本
            
        Returns:
            标准化后的分析结果
        """
        result = {
            "hot_sectors": [],
            "hot_stocks": [],
            "raw_text": deepseek_text
        }
        
        # 提取板块信息
        sector_patterns = [
            r'板块[:：]\s*([^\n。]+)',
            r'热门板块[:：]\s*([^\n。]+)',
            r'关注板块[:：]\s*([^\n。]+)',
            r'涉及板块[:：]\s*([^\n。]+)',
        ]
        
        for pattern in sector_patterns:
            matches = re.findall(pattern, deepseek_text)
            for match in matches:
                sectors = re.split(r'[，,、]', match)
                for sector in sectors:
                    normalized = self.normalize_sector(sector.strip())
                    if normalized and normalized not in result["hot_sectors"]:
                        result["hot_sectors"].append(normalized)
        
        # 提取股票信息
        stock_patterns = [
            r'(\d{6})\.(?:SH|SZ|sh|sz)',
            r'(\d{6})',
            r'[（(](\d{6})[）)]',
        ]
        
        for pattern in stock_patterns:
            matches = re.findall(pattern, deepseek_text)
            for match in matches:
                if len(match) == 6 and match.isdigit():
                    if match.startswith('6'):
                        stock_code = f"sh{match}"
                    else:
                        stock_code = f"sz{match}"
                    
                    if stock_code not in result["hot_stocks"]:
                        result["hot_stocks"].append(stock_code)
        
        # 如果没有提取到板块，尝试从股票反推
        if not result["hot_sectors"] and result["hot_stocks"]:
            sectors_set = set()
            for stock in result["hot_stocks"]:
                stock_sectors = self.get_sectors_by_stock(stock)
                sectors_set.update(stock_sectors)
            
            if sectors_set:
                result["hot_sectors"] = list(sectors_set)
        
        return result


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建标准化器
    normalizer = IndustryNormalizer()
    
    # 测试标准化
    test_sectors = ["人工智能", "AI", "半导体芯片", "医药医疗", "新能源车"]
    for sector in test_sectors:
        normalized = normalizer.normalize_sector(sector)
        print(f"{sector} -> {normalized}")
    
    # 测试 DeepSeek 文本分析
    test_text = """
    今日热门板块：人工智能、半导体芯片、新能源车
    关注股票：600519(贵州茅台)、000858(五粮液)、002415(海康威视)
    """
    
    analysis = normalizer.analyze_deepseek_response(test_text)
    print("\nDeepSeek 分析结果:")
    print(f"热门板块: {analysis['hot_sectors']}")
    print(f"热门股票: {analysis['hot_stocks']}")
    
    # 测试股票-板块映射
    test_stock = "sh600519"
    sectors = normalizer.get_sectors_by_stock(test_stock)
    industry = normalizer.get_industry_by_stock(test_stock)
    print(f"\n股票 {test_stock}:")
    print(f"所属板块: {sectors}")