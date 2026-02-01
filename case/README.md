# 每日收盘简报 - 使用说明

## 功能介绍

每日收盘简报系统可以自动分析股票市场数据，生成包含以下维度的简报：

1. **大盘与市场环境** - 总股票数、涨跌家数、平均涨跌幅、涨停跌停、市场情绪
2. **板块热点与轮动** - 行业板块涨跌幅排行
3. **个股表现与活跃度** - 涨跌幅榜、振幅榜
4. **技术信号与趋势** - MA金叉、RSI超买超卖

## 安装依赖

```bash
pip install pandas numpy requests baostock
```

## 使用方法

### 1. 基本使用（仅生成简报）

```bash
# 自动分析最新交易日
py daily_close_brief.py

# 分析指定日期
py daily_close_brief.py --analyze_date 2026-01-29
```

### 2. 发送到钉钉机器人

#### 方法一：使用命令行参数

```bash
py daily_close_brief.py --analyze_date 2026-01-29 --dingtalk_webhook "https://oapi.dingtalk.com/robot/send?access_token=xxx" --dingtalk_secret "SECxxx"
```

#### 方法二：使用配置文件

1. 创建配置文件 `scripts/dingtalk_config.txt`：

```
webhook=https://oapi.dingtalk.com/robot/send?access_token=xxx
secret=SECxxx
```

2. 运行命令：

```bash
py daily_close_brief.py --analyze_date 2026-01-29
```

#### 方法三：使用环境变量

```bash
# Windows
set DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
set DINGTALK_SECRET=SECxxx
py daily_close_brief.py --analyze_date 2026-01-29

# Linux/Mac
export DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
export DINGTALK_SECRET=SECxxx
py daily_close_brief.py --analyze_date 2026-01-29
```

## 钉钉机器人配置

### 获取 Webhook URL 和 Secret

1. 在钉钉群中添加自定义机器人
2. 安全设置选择"加签"
3. 复制 Webhook URL 和 Secret

### 配置优先级

1. 命令行参数（最高优先级）
2. 环境变量
3. 配置文件（最低优先级）

## 简报格式

### 控制台输出

```
================================================================================
每日收盘简报 - 2026-01-29
================================================================================

【维度1: 大盘与市场环境】
  总股票数: 5185
  上涨: 1717 | 下跌: 3363 | 平盘: 104
  平均涨跌幅: -0.72%
  涨停: 101 | 跌停: 22
  市场情绪: 分化
...
```

### 钉钉 Markdown 格式

```
## 📊 每日收盘简报 - 2026-01-29

### 📈 大盘与市场环境

- 总股票数: **5185**
- 上涨: **1717** | 下跌: **3363** | 平盘: **104**
- 平均涨跌幅: 🔴 **-0.72%**
- 涨停: **101** | 跌停: **22**
- 市场情绪: **⚖️ 分化**

### 🏢 板块热点与轮动

**行业板块数: 83**

**📈 涨幅榜 TOP5**
1. B11开采专业及辅助性活动 🟢 **6.55%** (14只)
2. C15酒、饮料和精制茶制造业 🟢 **6.14%** (48只)
...
```

## 命令行参数

| 参数 | 说明 | 是否必填 | 示例 |
|------|------|---------|------|
| --analyze_date | 要分析的日期（格式：YYYY-MM-DD） | 否 | 2026-01-29 |
| --dingtalk_webhook | 钉钉机器人 Webhook URL | 否 | https://oapi.dingtalk.com/... |
| --dingtalk_secret | 钉钉机器人加签密钥 | 否 | SECxxx |

## 注意事项

1. **数据来源**：baostock（免费股票数据接口）
2. **数据更新**：首次运行会自动下载最新交易日数据
3. **数据存储**：`~/.qlib/stock_data/source/all_1d_original/`
4. **发送频率**：建议每天收盘后发送一次

## 常见问题

### Q: 钉钉发送失败怎么办？
A: 检查以下几点：
1. Webhook URL 是否正确
2. Secret 是否正确（如果启用了加签）
3. 网络连接是否正常
4. 钉钉群是否禁用了机器人

### Q: 数据为空怎么办？
A: 检查以下几点：
1. 指定的日期是否是交易日
2. 数据目录是否有数据
3. 重新下载数据

### Q: 如何自动定时发送？
A: 可以使用系统的定时任务：
- Windows: 任务计划程序
- Linux/Mac: cron
