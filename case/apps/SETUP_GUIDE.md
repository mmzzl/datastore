# 盘后分析服务快速部署指南

## 前提条件

1. Python 3.8+
2. MongoDB 数据库
3. 钉钉机器人 Webhook

## 快速开始

### 1. 安装依赖

```bash
cd /root/apps

# 安装主项目依赖
pip install -r api/requirements.txt

# 安装盘后分析额外依赖
pip install -r after_market_requirements.txt
```

### 2. 配置钉钉机器人

1. 在钉钉群中添加"自定义机器人"
2. 安全设置选择"加签"
3. 复制 Webhook 地址和 Secret
4. 编辑 `api/config.yaml`，添加配置：

```yaml
after_market:
  dingtalk_webhook: "https://oapi.dingtalk.com/robot/send?access_token=你的token"
  dingtalk_secret: "SEC你的密钥"
  scheduler_time: "17:30"
  scheduler_timezone: "Asia/Shanghai"
```

### 3. 测试功能

```bash
# 运行测试套件
python3 test_after_market.py
```

测试套件会依次测试：
- 数据库连接
- 市场分析功能
- 钉钉通知功能
- 完整分析流程
- 报告生成

### 4. 手动执行一次分析

```bash
# 使用最新日期
python3 after_market_analysis.py

# 指定日期
python3 after_market_analysis.py 2024-03-10
```

### 5. 启动定时服务

#### 方式A: 使用启动脚本（推荐）

```bash
# 添加执行权限
chmod +x start_scheduler.sh

# 以守护进程方式启动
./start_scheduler.sh --daemon

# 查看服务状态
./start_scheduler.sh --status

# 查看实时日志
./start_scheduler.sh --logs

# 停止服务
./start_scheduler.sh --stop
```

#### 方式B: 手动配置 systemd 服务

```bash
# 复制服务文件
cp after-market-scheduler.service /etc/systemd/system/

# 重载 systemd
systemctl daemon-reload

# 启用开机自启
systemctl enable after-market-scheduler.service

# 启动服务
systemctl start after-market-scheduler.service

# 查看状态
systemctl status after-market-scheduler.service

# 查看日志
journalctl -u after-market-scheduler.service -f
```

#### 方式C: 前台运行（测试用）

```bash
# 前台运行调度器（方便调试）
python3 after_market_scheduler.py

# 单次测试执行
python3 after_market_scheduler.py --once
```

## 常用命令

```bash
# 手动执行分析
python3 after_market_analysis.py [日期]

# 单次测试执行
python3 after_market_scheduler.py --once

# 启动守护进程服务
./start_scheduler.sh --daemon

# 停止服务
./start_scheduler.sh --stop

# 查看服务状态
./start_scheduler.sh --status

# 查看服务日志
./start_scheduler.sh --logs

# 运行完整测试
python3 test_after_market.py
```

## 调度时间说明

默认配置为每天 17:30（北京时间）执行分析。

修改时间：
编辑 `api/config.yaml` 文件：
```yaml
after_market:
  scheduler_time: "17:30"  # 修改为你的期望时间
```

修改后重启服务：
```bash
./start_scheduler.sh --stop
./start_scheduler.sh --daemon
```

## 数据库集合说明

默认从 `stock_kline` 集合读取数据。

如果你的数据在其他集合，有两种方式修改：

### 方式1: 修改配置文件

在 `api/config.yaml` 中添加：
```yaml
mongodb:
  kline_collection: "your_collection_name"  # 添加这一行
```

### 方式2: 修改代码

编辑 `after_market_analysis.py`，找到以下行：
```python
self.kline_collection = self.db.get('stock_kline', self.db.get('kline', self.db['stocks']))
```

修改为你的集合名称。

## 故障排查

### 数据库连接失败

1. 检查 MongoDB 是否运行：
```bash
systemctl status mongod
```

2. 检查配置文件中的连接信息：
```bash
grep -A 10 "mongodb:" api/config.yaml
```

3. 测试连接：
```bash
python3 -c "from pymongo import MongoClient; client = MongoClient('你的连接地址'); print(client.server_info())"
```

### 钉钉消息发送失败

1. 检查 Webhook 地址是否正确
2. 检查 Secret 是否配置
3. 查看服务日志获取详细错误：
```bash
journalctl -u after-market-scheduler.service -n 100
```

### 定时任务未执行

1. 检查服务状态：
```bash
./start_scheduler.sh --status
```

2. 查看日志确认任务是否被触发：
```bash
./start_scheduler.sh --logs
```

3. 手动触发测试：
```bash
python3 after_market_scheduler.py --once
```

### 没有分析数据

1. 检查数据库中是否有数据：
```bash
python3 -c "from pymongo import MongoClient; client = MongoClient('你的连接地址'); db = client['eastmoney_news']; print(db['stock_kline'].count_documents({}))"
```

2. 检查最新日期：
```bash
python3 -c "from pymongo import MongoClient; client = MongoClient('你的连接地址'); db = client['eastmoney_news']; print(db['stock_kline'].find_one({}, sort=[('date', -1)])['date'])"
```

3. 确认数据字段完整（需要 code, name, date, close, pct_chg, amount 等）

## 日志位置

- systemd 服务日志：`journalctl -u after-market-scheduler.service`
- 实时日志：`journalctl -u after-market-scheduler.service -f`
- 最近100条：`journalctl -u after-market-scheduler.service -n 100`

## 卸载

```bash
# 停止并禁用服务
./start_scheduler.sh --stop
systemctl disable after-market-scheduler.service

# 删除服务文件
rm /etc/systemd/system/after-market-scheduler.service
systemctl daemon-reload

# 可选：删除相关文件
rm -f after_market_analysis.py
rm -f after_market_scheduler.py
rm -f test_after_market.py
rm -f start_scheduler.sh
rm -f after-market-scheduler.service
```

## 更新日志

- 2024-03-10: 初始版本发布
  - 市场概览分析
  - 涨跌幅榜
  - 成交额榜
  - 钉钉通知
  - 定时任务调度
  - systemd 服务支持

## 获取帮助

如遇问题，请：
1. 查看详细日志
2. 运行测试套件诊断问题
3. 查阅 README_AFTER_MARKET.md 获取完整文档
