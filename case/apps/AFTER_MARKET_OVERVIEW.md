# 盘后数据分析服务 - 项目总览

## 项目文件清单

本项目包含以下文件：

### 核心程序文件

1. **after_market_analysis.py** - 盘后数据分析主程序
   - 功能：执行市场分析、生成报告、发送钉钉通知
   - 包含类：
     - `DingTalkNotifier`: 钉钉机器人通知类
     - `StockAnalyzer`: 股票数据分析类
     - `AfterMarketAnalysisService`: 盘后分析服务类

2. **after_market_scheduler.py** - 定时任务调度器
   - 功能：在指定时间自动触发盘后分析
   - 使用 APScheduler 实现定时调度
   - 支持工作日（周一到周五）定时执行

### 测试和初始化

3. **test_after_market.py** - 功能测试套件
   - 测试数据库连接
   - 测试市场分析功能
   - 测试钉钉通知
   - 测试完整流程
   - 测试报告生成

4. **init_after_market.sh** - 快速初始化脚本
   - 自动安装依赖
   - 检查配置
   - 运行测试
   - 设置权限

5. **start_scheduler.sh** - 服务管理脚本
   - 启动守护进程
   - 停止服务
   - 查看状态
   - 查看日志
   - 手动执行

### 系统服务配置

6. **after-market-scheduler.service** - systemd 服务配置
   - Linux 系统服务配置文件
   - 支持开机自启
   - 自动重启

### 依赖文件

7. **after_market_requirements.txt** - 额外依赖
   - apscheduler: 定时任务调度
   - pytz: 时区支持

### 文档文件

8. **README_AFTER_MARKET.md** - 完整使用文档
   - 功能介绍
   - 安装说明
   - 配置方法
   - 使用指南
   - 故障排查
   - 开发扩展

9. **SETUP_GUIDE.md** - 快速部署指南
   - 快速开始步骤
   - 常用命令
   - 调度时间说明
   - 故障排查

10. **AFTER_MARKET_OVERVIEW.md** - 本文件
    - 项目总览
    - 文件清单
    - 快速参考

## 快速参考

### 安装步骤

```bash
# 1. 快速初始化
chmod +x init_after_market.sh
./init_after_market.sh

# 2. 测试功能
python3 test_after_market.py

# 3. 手动执行一次分析
python3 after_market_analysis.py

# 4. 启动定时服务
./start_scheduler.sh --daemon
```

### 常用命令

```bash
# 手动分析
python3 after_market_analysis.py [日期]

# 前台运行调度器
python3 after_market_scheduler.py

# 单次测试
python3 after_market_scheduler.py --once

# 服务管理
./start_scheduler.sh --daemon   # 启动守护进程
./start_scheduler.sh --stop     # 停止服务
./start_scheduler.sh --status   # 查看状态
./start_scheduler.sh --logs     # 查看日志
./start_scheduler.sh --test     # 单次测试

# 测试套件
python3 test_after_market.py

# systemd 命令
systemctl start after-market-scheduler.service
systemctl stop after-market-scheduler.service
systemctl status after-market-scheduler.service
journalctl -u after-market-scheduler.service -f
```

### 配置文件

主配置文件：`api/config.yaml`

```yaml
after_market:
  dingtalk_webhook: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
  dingtalk_secret: "SECxxx"  # 可选
  scheduler_time: "17:30"
  scheduler_timezone: "Asia/Shanghai"

mongodb:
  kline_collection: "stock_kline"  # K线数据集合名
```

## 功能特性

### 1. 市场概览分析
- 股票总数统计
- 涨/跌/平盘数量
- 涨跌停统计
- 平均涨跌幅
- 总成交额
- 平均振幅
- 市场情绪判断

### 2. 排行榜
- 涨幅榜 TOP10
- 跌幅榜 TOP10
- 成交额榜 TOP10

### 3. 行业分析
- 按行业统计平均涨跌幅
- 行业股票数量
- 行业总成交额

### 4. 钉钉通知
- Markdown 格式报告
- 支持加签安全
- 美观的表格展示

### 5. 定时任务
- 指定时间自动执行
- 只在工作日执行（周一到周五）
- 支持重试机制

### 6. 系统服务
- systemd 守护进程
- 开机自启
- 自动重启
- 日志管理

## 技术栈

- **Python 3.8+**
- **MongoDB** - 数据存储
- **APScheduler** - 定时任务
- **PyYAML** - 配置文件
- **Requests** - HTTP请求（钉钉通知）
- **Pandas** - 数据分析

## 数据要求

### MongoDB 数据结构

```javascript
{
    "code": "000001",        // 股票代码
    "name": "平安银行",      // 股票名称
    "date": "2024-03-10",    // 交易日期
    "open": 10.50,           // 开盘价
    "high": 10.80,           // 最高价
    "low": 10.40,            // 最低价
    "close": 10.75,          // 收盘价
    "volume": 1000000,       // 成交量
    "amount": 10750000,      // 成交额
    "pct_chg": 2.38,         // 涨跌幅(%)
    "industry": "银行"       // 行业（可选）
}
```

### 必需字段
- `code` - 股票代码
- `name` - 股票名称
- `date` - 交易日期
- `close` - 收盘价
- `pct_chg` - 涨跌幅
- `amount` - 成交额（用于成交额榜）

### 可选字段
- `volume` - 成交量
- `high` - 最高价
- `low` - 最低价
- `industry` / `sector` - 行业分类

## 部署架构

```
┌─────────────────────────────────────────┐
│         定时触发 (17:30)                 │
│    (APScheduler / systemd)               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    after_market_scheduler.py             │
│    定时任务调度器                        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    after_market_analysis.py             │
│    盘后分析服务                          │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐      │
│  │StockAnalyzer│  │DingTalk     │      │
│  │  数据分析    │  │  通知器     │      │
│  └──────┬──────┘  └──────┬──────┘      │
└─────────┼────────────────┼────────────┘
          │                │
          ▼                ▼
    ┌──────────┐    ┌──────────┐
    │ MongoDB  │    │ 钉钉API   │
    │  数据库   │    │  Webhook │
    └──────────┘    └──────────┘
```

## 日志流程

```
数据采集 → 市场分析 → 排行榜 → 报告生成 → 钉钉通知
    ↓           ↓          ↓          ↓          ↓
  MongoDB    概览统计    涨跌排序   Markdown   发送消息
```

## 扩展建议

### 1. 技术指标分析
添加更多技术指标分析：
- MA均线系统
- RSI强弱指标
- MACD
- KDJ
- 布林带

### 2. 板块分析
- 概念板块分析
- 地域板块分析
- 龙头股识别

### 3. 资金流向
- 主力资金净流入
- 北向资金流向
- 机构资金动向

### 4. 多渠道通知
- 微信公众号通知
- 企业微信机器人
- 邮件通知
- 短信通知

### 5. 数据可视化
- 生成图表
- K线图
- 走势图
- 热力图

### 6. 历史回测
- 历史数据统计
- 策略回测
- 效果评估

## 注意事项

1. **数据时效性**：确保收盘后数据已更新到数据库
2. **网络稳定性**：钉钉API依赖网络，注意处理异常
3. **消息频率**：钉钉机器人有频率限制，避免过度发送
4. **数据准确性**：定期检查涨跌幅计算是否正确
5. **服务监控**：定期检查服务运行状态

## 支持和反馈

如有问题或建议，请：
1. 查阅详细文档：`README_AFTER_MARKET.md`
2. 查看部署指南：`SETUP_GUIDE.md`
3. 运行测试套件：`python3 test_after_market.py`
4. 查看日志：`journalctl -u after-market-scheduler.service -f`

## 版本历史

### v1.0.0 (2024-03-10)
- 初始版本发布
- 市场概览分析
- 涨跌幅排行榜
- 成交额排行榜
- 钉钉通知功能
- 定时任务调度
- systemd 服务支持
- 完整的测试套件

## 许可证

MIT License
