import requests
from typing import Dict, List, Optional
import json
import logging
from .industry_normalizer import IndustryNormalizer
logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, provider: str, api_key: str, model: str, base_url: str):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.industry = IndustryNormalizer()

    def chat(self, prompt: str) -> str:
        """通用聊天接口，返回原始文本响应"""
        if not self.api_key:
            raise Exception("未配置LLM API Key")
        return self._call_api(prompt)

    def analyze_stocks(self, stock_data: List[Dict], hot_sectors: List[str], top_n: int = 5) -> Dict:
        """分析股票数据，推荐买入标的"""
        if not stock_data:
            return {"error": "无股票数据"}
        
        prompt = f"""你是一位专业的A股短线交易分析师。根据以下股票的技术指标数据，从热门板块 {hot_sectors} 中选出最值得买入的{top_n}只股票。

股票技术数据：
{json.dumps(stock_data, ensure_ascii=False, indent=2)}

筛选逻辑：
1. RSI < 70（不超买）
2. MA5 > MA10（金叉状态）
3. 涨幅 > 0（上涨趋势）

请选出最值得买入的{top_n}只股票，返回JSON格式：
{{
    "recommendations": [{{"symbol": "股票代码", "reason": "推荐理由"}}],
    "analysis": "整体分析（50字以内）"
}}

只返回JSON。"""
        
        try:
            response = self.chat(prompt)
            result = json.loads(response)
            return {
                "top_stocks": result.get('recommendations', [])[:top_n],
                "analysis": result.get('analysis', '')
            }
        except Exception as e:
            logger.warning(f"股票分析失败: {e}")
            return {"error": str(e)}

    def analyze_news(self, news_list: List[Dict]) -> Dict:
        """分析新闻并返回结构化结果"""
        if not self.api_key:
            logger.info("未配置LLM API Key，使用简单关键词分析")
            return self._simple_analyze(news_list)
        
        # 构建prompt
        prompt = self._build_prompt(news_list)
        
        # 调用API
        try:
            response = self._call_api(prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return self._simple_analyze(news_list)

    def _build_prompt(self, news_list: List[Dict]) -> str:
        news_text = ""
        for i, news in enumerate(news_list, 1):
            title = news.get('title', '')
            summary = news.get('summary', '')
            sector_list = [i.split(".")[1] for i in news.get('stockList', [])]
            industry_list = [self.industry.get_industry_name(sector) for sector in sector_list]
            industry_list = [i for i in industry_list if i]
            stock_list = []
            for industry in industry_list:
                stock_list.extend(self.industry.get_stock_name(industry) or [])
            logger.info("industry_list: %s, stock_list: %s", industry_list, stock_list)
            news_text += f"{i}. 标题: {title}\n"
            if summary:
                news_text += f"   摘要: {summary}\n"
            if stock_list:
                news_text += f"   关联股票: {', '.join(stock_list)}\n"
            if industry_list:
                news_text += f"   关联行业: {', '.join(industry_list)}\n"
        # 关键：把 JSON 示例用 HEREDOC/原始字符串包裹，避免 f-string 解析冲突
        prompt = f"""你是一位专业、严谨、客观的A股市场分析师。请严格遵守以下要求分析新闻：

        ### 核心规则（必须100%遵守）
        1. 立场客观，不夸大、不造谣，基于新闻事实分析；
        2. 不推荐具体股票买卖，不预测个股涨跌，只做板块与情绪判断；
        3. 严格区分利好/利空/中性，不模棱两可；
        4. 只输出合法合规内容，不提供投资建议，仅做市场解读与风险提示；
        5. **格式强制要求**：仅返回标准 JSON 字符串，无任何多余文字、注释、换行、解释，JSON 必须可被 Python json.loads() 解析；
        6. JSON 字段约束：
        - summary：50字以内，新闻核心总结；
        - hot_sectors：数组，数据只能从关联行业中取值,不能自己创造新的名字；
        - hot_concepts：数组（仅列名称，不做推荐）；
        - hot_stocks：数组（仅列名称，不做推荐）；
        - sentiment：仅可选「利好」「利空」「中性」；
        - tomorrow_strategy.direction：仅可选「看多」「看空」「震荡」；
        - tomorrow_strategy.attention：重点关注方向（50字内）；
        - tomorrow_strategy.risk：风险提示（50字内）；
        - key_events：数组，最多3个关键事件。

        ### 待分析新闻
        {news_text}

        ### 输出示例（仅参考格式，需替换为真实分析结果）
        {{
            "summary": "央行降准0.25个百分点，释放流动性利好基建板块",
            "hot_sectors": ["基建", "银行"],
            "hot_concepts": ["大基建", "低估值"],
            "hot_stocks": ["中国建筑", "工商银行"],
            "sentiment": "利好",
            "tomorrow_strategy": {{
                "direction": "看多",
                "attention": "关注基建板块龙头股资金流向",
                "risk": "谨防板块短期冲高回落风险"
            }},
            "key_events": ["央行降准", "基建专项债发行提速"]
        }}

        ### 最终要求
        仅返回符合上述规则的 JSON 字符串，无任何其他内容！"""
        return prompt

    def _call_api(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']

    def _parse_response(self, response: str) -> Dict:
        try:
            # 尝试提取JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
        
        return self._simple_analyze([])

    def _simple_analyze(self, news_list: List[Dict]) -> Dict:
        """简单的关键词分析作为后备"""
        keywords_利好 = ['涨停', '突破', '大涨', '增长', '业绩', '订单', '合作', '获批', '增长', '扭亏', '回购']
        keywords_利空 = ['跌停', '大跌', '亏损', '减持', '风险', '调查', '处罚', '下修', '预警']
        
        hot_sectors = set()
        hot_stocks = set()
        sentiment_score = 0
        
        for news in news_list:
            title = news.get('title', '')
            stock_list = news.get('stock_list', [])
            
            # 情绪分析
            for kw in keywords_利好:
                if kw in title:
                    sentiment_score += 1
                    break
            for kw in keywords_利空:
                if kw in title:
                    sentiment_score -= 1
                    break
            
            # 提取热门股票
            for stock in stock_list[:3]:
                hot_stocks.add(stock)
        
        if sentiment_score > 3:
            sentiment = "利好"
        elif sentiment_score < -3:
            sentiment = "利空"
        else:
            sentiment = "中性"
        
        return {
            "summary": f"今日共{len(news_list)}条新闻，市场{sentiment}",
            "hot_sectors": list(hot_sectors)[:10],
            "hot_stocks": list(hot_stocks)[:10],
            "sentiment": sentiment,
            "tomorrow_strategy": {
                "direction": "震荡",
                "attention": "关注市场成交量和板块轮动",
                "risk": "控制仓位"
            },
            "key_events": []
        }
