import requests

url = "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery112306436439534527604_1773561490090&fid=f62&po=1&pz=100&pn=1&np=1&fltt=2&invt=2&ut=8dec03ba335b81bf4ebdf7b29ec27d15&fs=m%3A0%2Bt%3A6%2Bf%3A%212%2Cm%3A0%2Bt%3A13%2Bf%3A%212%2Cm%3A0%2Bt%3A80%2Bf%3A%212%2Cm%3A1%2Bt%3A2%2Bf%3A%212%2Cm%3A1%2Bt%3A23%2Bf%3A%212%2Cm%3A0%2Bt%3A7%2Bf%3A%212%2Cm%3A1%2Bt%3A3%2Bf%3A%212&fields=f12%2Cf14%2Cf2%2Cf3%2Cf62%2Cf184%2Cf66%2Cf69%2Cf72%2Cf75%2Cf78%2Cf81%2Cf84%2Cf87%2Cf204%2Cf205%2Cf124%2Cf1%2Cf13"
headers = {
    "Host": "push2.eastmoney.com",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
    "ReReferer":"https://data.eastmoney.com/zjlx/detail.html"
        }

#url = "http://httpbin.org/ip"
#url = "http://httpbin.org/get"
#url = "https://push2.eastmoney.com/api/qt/client/get?"
res = requests.get(url, headers=headers, timeout=10,verify=False)
print(res.text)

