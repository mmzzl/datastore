# 盘后数据分析服务

自动分析股票市场盘后数据并发送到钉钉机器人。

## 功能特性

- 📊 **市场概览分析**：统计上涨/下跌/平盘股票数量，计算涨跌幅分布
- 🚀 **涨幅榜**：显示涨幅前10的股票
- 📉 **跌幅榜**：显示跌幅前10的股票
- 💰 **成交额榜**：显示成交额前10的股票
- 🏭 **行业分析**：按行业统计平均涨跌幅（如果有行业分类数据）
- 🤖 **钉钉通知**：自动将分析报告发送到钉钉群
- ⏰ **定时任务**：支持在收盘后自动执行分析
- 🐧 **系统服务**：支持以systemd服务方式运行

## 安装依赖

```bash
pip install -r api/requirements.txt
```

需要额外安装的依赖：
```bash
pip install apscheduler pytz
```

## 配置说明

在 `api/config.yaml` 中添加或修改以下配置：

```yaml
# 盘后信息服务配置
after_market:
  # MongoDB配置（复用mongodb配置）
  dingtalk_webhook: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
  dingtalk_secret: "SECxxx"  # 可选，如果使用加签方式
  scheduler_time: "17:30"   # 定时执行时间
  scheduler_timezone: "Asia/Shanghai"
```

### 钉钉机器人配置

1. 在钉钉群中添加"自定义机器人"
2. 选择"加签"安全设置（推荐）
3. 获取 `webhook` 地址和 `secret`
4. 填入配置文件

## 使用方法

### 方式1: 手动执行分析

```bash
# 使用最新日期进行分析
python3 after_market_analysis.py

# 指定日期进行分析
python3 after_market_analysis.py 2024-03-10

# 使用自定义配置文件
python3 after_market_analysis.py 2024-03-10 /path/to/config.yaml
```

### 方式2: 定时调度器（前台运行）

```bash
# 启动调度器（前台运行，用于测试）
python3 after_market_scheduler.py

# 单次测试执行
python3 after_market_scheduler.py --once
```

### 方式3: 使用启动脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x start_scheduler.sh

# 以守护进程方式启动（systemd服务）
./start_scheduler.sh --daemon

# 停止服务
./start_scheduler.sh --stop

# 查看服务状态
./start_scheduler.sh --status

# 查看服务日志
./start_scheduler.sh --logs

# 单次测试执行
./start_scheduler.sh --test

# 手动执行指定日期的分析
./start_scheduler.sh --manual 2024-03-10
```

## 数据库要求

需要MongoDB中存储股票K线数据，数据结构应包含：

```python
{
    "code": "000001",        # 股票代码
    "name": "平安银行",      # 股票名称
    "date": "2024-03-10",    # 交易日期
    "open": 10.50,           # 开盘价
    "high": 10.80,           # 最高价
    "low": 10.40,            # 最低价
    "close": 10.75,          # 收盘价
    "volume": 1000000,       # 成交量
    "amount": 10750000,      # 成交额
    "pct_chg": 2.38,         # 涨跌幅(%)
    "industry": "银行"       # 行业（可选）
}
```

默认集合名称：`stock_kline`

如果使用其他集合名，需要在代码中修改配置或添加数据库集合映射。

## 报告示例

```
# 📊 盘后数据分析报告

**日期**: 2024-03-10
**生成时间**: 2024-03-10 17:35:00

## 📈 市场概览

- **股票总数**: 5000 只
- **上涨**: 2500 只
- **下跌**: 2000 只
- **平盘**: 500 只
- **涨停**: 30 只
- **跌停**: 10 只
- **平均涨跌幅**: 0.5%
- **中位数涨跌幅**: 0.3%
- **总成交额**: 5000 亿元
- **平均振幅**: 3.2%

**市场情绪**: 🟢 强势 （上涨占比 50.0%）

## 🚀 涨幅榜 TOP10

| 排名 | 代码 | 名称 | 收盘价 | 涨跌幅 | 成交额(亿) |
|------|------|------|--------|--------|-----------|
| 1 | 000001 | 平安银行 | 10.75 | +10.02% | 50.5 |

## 📉 跌幅榜 TOP10

| 排名 | 代码 | 名称 | 收盘价 | 涨跌幅 | 成交额(亿) |
|------|------|------|--------|--------|-----------|
| 1 | 000002 | 万科A | 8.50 | -9.98% | 30.2 |

## 💰 成交额榜 TOP10

| 排名 | 代码 | 名称 | 收盘价 | 涨跌幅 | 成交额(亿) |
|------|------|------|--------|--------|-----------|
| 1 | 600000 | 浦发银行 | 9.80 | +2.08% | 100.5 |

---
*数据来源: MongoDB数据库 | 仅供参考，不构成投资建议*
```

## 系统服务配置

### systemd服务配置文件

服务配置文件已创建：`after-market-scheduler.service`

如需修改服务配置，编辑该文件后重新安装：

```bash
# 停止服务
systemctl stop after-market-scheduler.service

# 重新安装服务
cp after-market-scheduler.service /etc/systemd/system/
systemctl daemon-reload

# 启动服务
systemctl start after-market-scheduler.service
```

### 服务管理命令

```bash
# 查看服务状态
systemctl status after-market-scheduler.service

# 启动服务
systemctl start after-market-scheduler.service

# 停止服务
systemctl stop after-market-scheduler.service

# 重启服务
systemctl restart after-market-scheduler.service

# 查看实时日志
journalctl -u after-market-scheduler.service -f

# 查看最近日志
journalctl -u after-market-scheduler.service -n 100

# 设置开机自启
systemctl enable after-market-scheduler.service

# 取消开机自启
systemctl disable after-market-scheduler.service
```

## 故障排查

### 1. 数据库连接失败

检查 `api/config.yaml` 中的MongoDB配置是否正确：

```yaml
mongodb:
  host: "121.37.47.63"
  port: 27017
  username: "admin"
  password: "your_password"
  database: "eastmoney_news"
```

### 2. 钉钉消息发送失败

- 检查 webhook 地址是否正确
- 检查 secret 是否配置正确（如果使用加签）
- 检查钉钉机器人是否被禁用
- 查看服务日志获取详细错误信息

### 3. 定时任务未执行

- 检查调度时间配置是否正确
- 检查系统时区是否正确
- 查看服务日志确认任务是否被触发
- 确认当天是否为工作日（周一到周五）

### 4. 没有分析数据

- 检查数据库中是否有指定日期的K线数据
- 检查数据集合名称是否正确（默认 `stock_kline`）
- 检查数据字段是否包含所需字段

## 日志

日志会输出到标准输出，通过systemd服务管理时会记录到journalctl。

查看实时日志：
```bash
journalctl -u after-market-scheduler.service -f
```

## 开发和扩展

### 添加新的分析指标

在 `after_market_analysis.py` 的 `StockAnalyzer` 类中添加新的分析方法：

```python
def custom_analysis(self, date: str = None) -> Dict:
    """自定义分析"""
    # 实现你的分析逻辑
    return {}
```

然后在 `AfterMarketAnalysisService.run_analysis()` 中调用新方法。

### 修改报告格式

在 `AfterMarketAnalysisService._generate_report()` 方法中修改报告生成逻辑。

### 支持更多通知方式

创建新的通知类（如微信、飞书等），参考 `DingTalkNotifier` 的实现。

## 注意事项

1. **数据准确性**：确保数据库中的K线数据准确、完整
2. **涨跌幅计算**：确保 `pct_chg` 字段已正确计算（可使用 `fix_change_pct.py` 修复）
3. **定时执行**：建议在收盘后15-30分钟执行，确保数据已更新
4. **市场情绪判断**：根据实际需求调整市场情绪判断阈值
5. **钉钉频率限制**：注意钉钉机器人的消息频率限制，避免被限流

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request。
