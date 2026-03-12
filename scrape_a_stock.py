from scrapling.fetchers import StealthyFetcher
import json
import re

# 配置
stock_code = "300274"  # 阳光电源
market = "0"  # 0=深圳, 1=上海

url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?cb=jQuery351&secid={market}.{stock_code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt=101&fqt=1&beg=0&end=20500101&smplmt=460&lmt=1000000"

headers = {
    "Host": "push2his.eastmoney.com",
    "Referer": f"https://quote.eastmoney.com/sz{stock_code}.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

try:
    page = StealthyFetcher.fetch(
        url,
        extra_headers={
            "Host": "push2his.eastmoney.com",
            "Referer": f"https://quote.eastmoney.com/sz{stock_code}.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        headless=True,
        network_idle=True,
        timeout=30000,
    )

    # 提取 JSON 响应
    text = page.text

    # 解析 JSONP 回调
    match = re.search(r"jQuery351\((.*)\)", text, re.DOTALL)
    if match:
        data = json.loads(match.group(1))

        if data.get("rc") == 0:
            stock_data = data["data"]
            print(f"股票代码: {stock_data['code']}")
            print(f"股票名称: {stock_data['name']}")
            print(f"数据条数: {stock_data['dktotal']}")
            print(
                "\nK线数据 (日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,换手率):"
            )

            klines = stock_data["klines"]
            for i, kline in enumerate(klines[:10]):  # 只显示前10条
                print(f"  {kline}")
            print(f"  ... 共 {len(klines)} 条")
        else:
            print(f"API错误: {data}")
    else:
        print("未找到JSONP响应")
        print(text[:500])

except Exception as e:
    print(f"Error: {e}")
