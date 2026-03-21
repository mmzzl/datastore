import requests
import json
import re

stock_code = "300274"
market = "0"

url = (
    f"https://push2his.eastmoney.com/api/qt/stock/kline/get?"
    f"cb=jQuery351&secid={market}.{stock_code}&"
    f"ut=fa5fd1943c7b386f172d6893dbfba10b&"
    f"fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&"
    f"fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&"
    f"klt=101&fqt=1&beg=0&end=20500101&smplmt=460&lmt=1000000"
)

headers = {
    "Host": "push2his.eastmoney.com",
    "Referer": f"https://quote.eastmoney.com/sz{stock_code}.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

try:
    resp = requests.get(url, headers=headers, timeout=30)
    text = resp.text

    match = re.search(r"jQuery351\((.*)\)", text, re.DOTALL)

    if match:
        data = json.loads(match.group(1))

        if data.get("rc") == 0:
            stock = data["data"]
            print(f"股票: {stock['name']} ({stock['code']})")
            print(f"总数据条数: {stock['dktotal']}")
            print("\nK线数据 (前5条):")
            print("日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,换手率")

            for kline in stock["klines"][:5]:
                print(kline)
        else:
            print(f"API错误: {data}")
    else:
        print("解析失败")
        print(text[:300])

except Exception as e:
    print(f"Error: {e}")
