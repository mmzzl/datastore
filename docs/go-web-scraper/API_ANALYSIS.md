# 东方财富上市公司新闻 API 分析

## 页面分析

### 当前页面结构
- URL: https://kuaixun.eastmoney.com/ssgs.html
- 加载方式：动态 JavaScript 加载
- 初始显示：50 条新闻
- 加载更多：点击"加载更多"按钮

## 可能的 API 接口

### 1. 东方财富快讯 API（推荐）

```
https://np-listapi.eastmoney.com/comm/wap/getListInfo
```

**参数示例：**
```javascript
{
  "cb": "jQuery",
  "ClientType": "web",
  "Filter": "SSGS",
  "pagesize": 50,
  "pageIndex": 0,
  "Po": "1a2f3e0-4c4d-4e8d-9c1e-1a2f3e04c4d",
  "ut": "fa5fdedd-d3d0-4e6b-a6a3-fa5fdedd0d30"
}
```

### 2. 上市公司公告 API

```
https://np-anotice-stock.eastmoney.com/api/security/ann
```

**参数示例：**
```javascript
{
  "ann_type": "SSGS",
  "client_type": "web",
  "f_node": "0",
  "page_size": 50,
  "page_index": 0
}
```

### 3. 快讯推送 API

```
https://push2.eastmoney.com/api/qt/stock/get
```

**参数示例：**
```javascript
{
  "ut": "fa5fdedd-d3d0-4e6b-a6a3-fa5fdedd0d30",
  "fltt": "2",
  "invt": "2",
  "secid": "0.000001",
  "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26",
  "pos": "-0",
  "cb": "jsonp"
}
```

## 如何找到正确的 API 接口

### 步骤 1：打开浏览器开发者工具

1. 访问 https://kuaixun.eastmoney.com/ssgs.html
2. 按 F12 打开开发者工具
3. 切换到 "Network"（网络）标签

### 步骤 2：点击"加载更多"按钮

1. 在页面上点击"加载更多"按钮
2. 观察 Network 标签中的新请求
3. 找到返回 JSON 数据的请求

### 步骤 3：分析 API 请求

1. 找到返回新闻数据的 API 请求
2. 查看请求 URL 和参数
3. 分析返回的数据格式

## API 接口特征

### 常见特征

1. **返回 JSON 数据**：API 通常返回 JSON 格式的数据
2. **包含分页参数**：如 `pageIndex`, `page_size`, `page_index`
3. **包含过滤参数**：如 `Filter`, `ann_type`, `secid`
4. **包含时间戳**：如 `ut`, `Po`, `cb`

### 可能的 API 响应格式

```json
{
  "data": {
    "list": [
      {
        "id": "123456",
        "title": "新闻标题",
        "content": "新闻内容",
        "publish_time": "2026-02-16 17:46",
        "source": "东方财富",
        "stocks": [
          {
            "name": "股票名称",
            "change": 4.74
          }
        ]
      }
    ],
    "total": 1000,
    "has_more": true
  },
  "rc": 0,
  "rt": 1234567890
}
```

## 实现方案

### 方案 1：使用已知 API 接口

如果找到 API 接口，可以直接调用：

```go
func (c *SSGSCrawler) fetchWithAPI(pageIndex int) ([]model.EastMoneyNews, error) {
    apiURL := "https://np-listapi.eastmoney.com/comm/wap/getListInfo"

    params := map[string]string{
        "cb": "jQuery",
        "ClientType": "web",
        "Filter": "SSGS",
        "pagesize": "50",
        "pageIndex": strconv.Itoa(pageIndex),
    }

    resp, err := http.Get(apiURL + "?" + buildQueryString(params))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result APIResponse
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }

    return result.Data.List, nil
}
```

### 方案 2：分页加载

如果 API 支持分页，可以循环加载：

```go
func (c *SSGSCrawler) fetchAllNews() ([]model.EastMoneyNews, error) {
    var allNews []model.EastMoneyNews
    pageIndex := 0

    for {
        news, err := c.fetchWithAPI(pageIndex)
        if err != nil {
            break
        }

        if len(news) == 0 {
            break
        }

        allNews = append(allNews, news...)
        pageIndex++

        if len(allNews) >= c.config.MaxNewsItems {
            break
        }
    }

    return allNews, nil
}
```

### 方案 3：混合方案

结合页面抓取和 API 调用：

1. 首次加载使用页面抓取
2. 后续加载使用 API 接口
3. 两者结合获取更多数据

## 测试 API 接口

### 使用 curl 测试

```bash
# 测试快讯 API
curl "https://np-listapi.eastmoney.com/comm/wap/getListInfo?cb=jQuery&ClientType=web&Filter=SSGS&pagesize=50&pageIndex=0"

# 测试公告 API
curl "https://np-anotice-stock.eastmoney.com/api/security/ann?ann_type=SSGS&client_type=web&page_size=50&page_index=0"
```

### 使用 Postman 测试

1. 创建新的 POST 请求
2. 设置 URL 为 API 地址
3. 添加必要的参数
4. 发送请求并查看响应

## 建议

### 立即行动

1. **打开开发者工具**：按 F12 打开浏览器开发者工具
2. **点击加载更多**：观察网络请求
3. **找到 API 接口**：记录 API URL 和参数
4. **测试 API**：使用 curl 或 Postman 测试
5. **实现代码**：根据 API 响应格式修改代码

### 长期方案

如果找不到 API 接口：

1. **接受当前限制**：使用 50 条新闻的限制
2. **增加抓取频率**：减少抓取间隔
3. **定期清理数据**：保持数据新鲜度
4. **使用代理**：避免 IP 被封禁

## 注意事项

1. **反爬虫机制**：网站可能有反爬虫机制
2. **API 限制**：API 可能有调用频率限制
3. **数据格式**：API 返回的数据格式可能变化
4. **认证信息**：某些 API 需要认证信息
5. **User-Agent**：需要设置正确的 User-Agent

## 总结

从页面结构来看，**很可能有 API 接口**可以加载更多新闻。建议：

1. 使用浏览器开发者工具分析网络请求
2. 找到正确的 API 接口和参数
3. 实现 API 调用代码替代页面抓取
4. 这样可以获取更多数据，提高效率

如果需要帮助实现 API 调用代码，请提供找到的 API 接口信息。
