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

        prompt = f"""你是一位专业、严谨的A股市场分析师。分析以下新闻，输出中文JSON。

### 核心规则
1. 立场客观，基于事实分析
2. 不推荐个股买卖，只做板块与情绪判断
3. 仅返回JSON，无多余文字

### 输出JSON字段说明
- summary: 今日市场要点总结（50字内）
- news_count: 新闻总数
- hot_sectors_detail: 热点板块数组，每项包含 name(板块名) 和 heat(热度分0-500，根据新闻提及频率和重要性)
- hot_stocks_detail: 热点股票数组，每项包含 name(股票名)、sector(所属板块)、heat(热度分0-500)
- news_by_category: 对象，key为分类名(如"重磅政策""国际动态""科技前沿""财报业绩""市场动态""风险警示")，value为该分类下的新闻标题数组
- hot_sectors: 数组，仅板块名称（兼容旧版）
- hot_stocks: 数组，仅股票名称（兼容旧版）
- sentiment: 仅可选「利好」「利空」「中性」
- market_analysis: 对象，包含:
  - overall: 市场整体态势（80字内）
  - sector_rotation: 板块轮动分析（80字内）
  - opportunities: 数组，投资机会（每项30字内，最多3条）
  - risks: 数组，风险提示（每项30字内，最多3条）
  - outlook: 次日展望（60字内）
  - core_focus: 数组，今日核心关注事件（每项30字内，最多3条）
- tomorrow_strategy: 对象，含 direction(看多/看空/震荡)、attention(重点关注)、risk(风险提示)
- key_events: 数组，最多3个关键事件
- hot_concepts: 数组，热门概念（兼容旧版）

### 待分析新闻
{news_text}

### 输出示例（格式参考，数据替换为真实分析结果）
{{{{
    "summary": "昨日A股缩量调整，热点轮动加速。美联储维持利率不变，鲍威尔卸任进入倒计时。",
    "news_count": 32,
    "hot_sectors_detail": [
        {{"name": "人工智能", "heat": 384}},
        {{"name": "存储芯片", "heat": 311}}
    ],
    "hot_stocks_detail": [
        {{"name": "南方路机", "sector": "人工智能", "heat": 384}},
        {{"name": "浪潮软件", "sector": "人工智能", "heat": 384}}
    ],
    "news_by_category": {{
        "重磅政策": ["深圳楼市五一前放大招", "中国证监会迎70后副主席"],
        "国际动态": ["美联储维持利率不变", "霍尔木兹海峡航运受阻"]
    }},
    "hot_sectors": ["人工智能", "存储芯片"],
    "hot_stocks": ["南方路机", "浪潮软件"],
    "sentiment": "中性",
    "market_analysis": {{
        "overall": "AI板块延续强势，但市场分化明显，业绩+景气度才是核心逻辑。",
        "sector_rotation": "AI算力持续走强；存储受益AI超级周期；房地产政策博弈。",
        "opportunities": ["AI算力龙头", "存储周期机会", "政策放松地产链"],
        "risks": ["业绩变脸股风险", "ST股扩散风险", "节前避险情绪"],
        "outlook": "五一小长假前避险情绪升温，关注美股科技巨头财报影响。",
        "core_focus": ["源杰科技登顶新股王", "芯原股份AI算力订单爆发", "深圳楼市新政"]
    }},
    "tomorrow_strategy": {{
        "direction": "震荡",
        "attention": "关注AI算力和存储板块持续性",
        "risk": "控制仓位，规避ST风险股"
    }},
    "key_events": ["美联储换帅倒计时", "AI存儲超级周期", "深圳楼市新政"],
    "hot_concepts": ["AI算力", "存储芯片"]
}}}}

仅返回JSON，无任何其他内容。"""
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

        hot_sectors_list = list(hot_sectors)[:10]
        hot_stocks_list = list(hot_stocks)[:10]

        return {
            "summary": f"今日共{len(news_list)}条新闻，市场{sentiment}",
            "news_count": len(news_list),
            "hot_sectors_detail": [{"name": s, "heat": 100} for s in hot_sectors_list],
            "hot_stocks_detail": [{"name": s, "sector": "", "heat": 100} for s in hot_stocks_list],
            "news_by_category": {"市场动态": [n.get("title", "") for n in news_list if n.get("title")]},
            "hot_sectors": hot_sectors_list,
            "hot_stocks": hot_stocks_list,
            "sentiment": sentiment,
            "market_analysis": {
                "overall": f"市场{sentiment}，共{len(news_list)}条新闻",
                "sector_rotation": "关注热点板块轮动",
                "opportunities": [] if sentiment == "利空" else ["关注热点板块"],
                "risks": ["控制仓位"] if sentiment == "利空" else [],
                "outlook": "关注市场成交量和板块轮动",
                "core_focus": []
            },
            "tomorrow_strategy": {
                "direction": "震荡",
                "attention": "关注市场成交量和板块轮动",
                "risk": "控制仓位"
            },
            "key_events": [],
            "hot_concepts": []
        }
