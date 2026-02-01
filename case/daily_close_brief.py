# -*- coding: utf-8 -*-
# 每日收盘简报
import argparse
from pathlib import Path
from scripts.data_collector.baostock_5min.collector import BaostockCollectorALL1d
from scripts.daily_brief_analyzer import DailyBriefAnalyzer
from scripts.dingtalk_bot import DingTalkBot
from scripts.config import Config
from datetime import datetime, timedelta
import time
import baostock as bs
import pandas as pd
import os
import schedule
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# 使用日期命名日志文件
current_date = datetime.now().strftime("%Y-%m-%d")
log_file = log_dir / f"daily_close_brief_{current_date}.log"

# 创建日志记录器
logger = logging.getLogger("daily_close_brief")
logger.setLevel(logging.INFO)

# 创建文件处理器（自动轮转，每个文件最大10MB，保留5个备份）
file_handler = RotatingFileHandler(
    log_file, 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class DailyCloseBrief:
    def __init__(self):
        self.csv_dir = Path('~/.qlib/stock_data/source/all_1d_original').expanduser()
        self.scheduled_run_time = "20:00"
    
    def get_trade_calendar(self, start_date: str = None, end_date: str = None) -> list:
        """获取交易日历"""
        try:
            _format = "%Y-%m-%d"
            if start_date is None:
                start_date = datetime.now().strftime(_format)
            if end_date is None:
                end_date = (datetime.now() + timedelta(days=7)).strftime(_format)
            
            rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
            calendar_list = []
            while (rs.error_code == "0") & rs.next():
                calendar_list.append(rs.get_row_data())
            
            calendar_df = pd.DataFrame(calendar_list, columns=rs.fields)
            trade_calendar_df = calendar_df[~calendar_df["is_trading_day"].isin(["0"])]
            return trade_calendar_df["calendar_date"].values.tolist()
        except Exception as e:
            logger.error(f"获取交易日历时出错: {e}")
            return []
    
    def is_trading_day(self, date: str = None) -> bool:
        """判断指定日期是否为交易日"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        trade_calendar = self.get_trade_calendar(start_date=date, end_date=date)
        return date in trade_calendar
    
    def should_run_today(self) -> bool:
        """判断今天是否应该运行（交易日且当前时间超过20:00）"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if not self.is_trading_day(today):
            logger.info(f"今天 {today} 不是交易日，跳过运行")
            return False
        
        current_time = datetime.now().strftime("%H:%M")
        if current_time < self.scheduled_run_time:
            logger.info(f"当前时间 {current_time} 未到运行时间 {self.scheduled_run_time}，等待中...")
            return False
        
        logger.info(f"今天 {today} 是交易日，当前时间 {current_time} 已超过 {self.scheduled_run_time}，准备运行")
        return True
    
    def get_latest_trade_date(self) -> str:
        """从本地数据中获取最新交易日"""
        try:
            # 检查是否有 CSV 文件
            csv_files = list(self.csv_dir.glob("*.csv"))
            if len(csv_files) == 0:
                return None
            
            # 读取所有日期
            all_dates = set()
            for csv_file in csv_files[:50]:  # 检查前50个文件
                try:
                    df = pd.read_csv(csv_file)
                    if 'date' in df.columns:
                        dates = df['date'].astype(str).str[:10].unique()
                        all_dates.update(dates)
                except:
                    continue
            
            if len(all_dates) > 0:
                latest_date = sorted(all_dates)[-1]
                return latest_date
            
            return None
        except Exception as e:
            logger.error(f"获取最新交易日时出错: {e}")
            return None
    
    def check_data_exists(self, date: str) -> bool:
        """检查指定日期的数据是否存在"""
        try:
            # 检查是否有 CSV 文件
            csv_files = list(self.csv_dir.glob("*.csv"))
            if len(csv_files) == 0:
                return False
            
            # 检查是否有该日期的数据
            for csv_file in csv_files[:20]:  # 检查前20个文件
                try:
                    df = pd.read_csv(csv_file)
                    if 'date' in df.columns:
                        # 转换日期格式，匹配 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
                        dates = df['date'].astype(str).str[:10].values
                        if date in dates:
                            return True
                except:
                    continue
            
            return False
        except Exception as e:
            logger.error(f"检查数据时出错: {e}")
            return False
    
    def analyze_data(self, date: str):
        """步骤2: 分析数据并生成简报"""
        logger.info("【步骤2】开始分析数据...")
        analyzer = DailyBriefAnalyzer(str(self.csv_dir))
        logger.info(f"分析日期: {date}")
        analyzer.print_brief(date)
        logger.info("【步骤2】数据分析完成！\n")
    
    def run_scheduled(self):
        """定时运行模式：每天20:00检查是否为交易日，如果是则运行"""
        def job():
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"定时任务检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}\n")
                
                if self.should_run_today():
                    today = datetime.now().strftime("%Y-%m-%d")
                    logger.info(f"开始执行每日收盘简报任务（日期: {today}）")
                    
                    # 检查数据是否存在
                    if self.check_data_exists(today):
                        logger.info(f"【步骤1】数据已存在，跳过下载（日期: {today}）")
                    else:
                        logger.info(f"【步骤1】数据不存在，开始下载最新交易日数据（日期: {today}）...")
                        collector = BaostockCollectorALL1d(
                            save_dir=str(self.csv_dir), 
                            start=today,
                            end=today,
                            interval="1d",
                            max_workers=4,
                            max_collector_count=4,
                            delay=0.1,
                            region="ALL"
                        )
                        collector.collector_data()
                        logger.info("【步骤1】数据下载完成！\n")
                    
                    # 分析数据
                    self.analyze_data(today)
                    
                    # 发送到钉钉
                    dingtalk_webhook, dingtalk_secret = Config.get_dingtalk_config()
                    if dingtalk_webhook:
                        self.send_to_dingtalk(
                            date=today,
                            webhook_url=dingtalk_webhook,
                            secret=dingtalk_secret
                        )
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"任务完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"{'='*60}\n")
                else:
                    logger.info(f"今天不满足运行条件，跳过\n")
            except Exception as e:
                logger.error(f"定时任务执行出错: {e}\n")
        
        # 设置定时任务：每天20:00执行
        schedule.every().day.at(self.scheduled_run_time).do(job)
        
        logger.info(f"定时任务已启动，将在每天 {self.scheduled_run_time} 检查是否为交易日并运行")
        logger.info("按 Ctrl+C 退出\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("\n定时任务已停止")
    
    def run(self, analyze_date: str = None):
        """执行完整流程"""
        # 如果没有指定日期，自动获取最新交易日
        if analyze_date is None:
            analyze_date = self.get_latest_trade_date()
            if analyze_date is None:
                logger.error("错误：无法获取最新交易日")
                return
            logger.info(f"自动获取最新交易日: {analyze_date}")
        
        # 检查最新交易日的数据是否存在
        if self.check_data_exists(analyze_date):
            logger.info(f"【步骤1】数据已存在，跳过下载（日期: {analyze_date}）")
        else:
            logger.info(f"【步骤1】数据不存在，开始下载最新交易日数据（日期: {analyze_date}）...")
            # 只下载最新交易日这一天的数据
            collector = BaostockCollectorALL1d(
                save_dir=str(self.csv_dir), 
                start=analyze_date,
                end=analyze_date,
                interval="1d",
                max_workers=4,
                max_collector_count=4,
                delay=0.1,
                region="ALL"
            )
            collector.collector_data()
            logger.info("【步骤1】数据下载完成！\n")
        
        # 分析最新交易日
        self.analyze_data(analyze_date)
    
    def send_to_dingtalk(self, date: str = None, webhook_url: str = None, secret: str = None):
        """发送简报到钉钉机器人"""
        # 如果没有传入配置，从配置文件读取
        if not webhook_url:
            webhook_url, secret = Config.get_dingtalk_config()
        
        if not webhook_url:
            logger.warning("未配置钉钉机器人 Webhook URL，跳过发送")
            logger.info("提示：可以通过以下方式配置钉钉机器人：")
            logger.info("  1. 设置环境变量 DINGTALK_WEBHOOK 和 DINGTALK_SECRET")
            logger.info("  2. 使用命令行参数 --dingtalk_webhook 和 --dingtalk_secret")
            return
        
        logger.info("【步骤3】发送简报到钉钉机器人...")
        
        # 生成 Markdown 格式的简报
        analyzer = DailyBriefAnalyzer(str(self.csv_dir))
        markdown_text = analyzer.format_brief_for_dingtalk(date)
        
        # 发送到钉钉
        bot = DingTalkBot(webhook_url, secret)
        success = bot.send_markdown(markdown_text, title=f"每日收盘简报 - {date}")
        
        if success:
            logger.info("【步骤3】简报发送成功！\n")
        else:
            logger.error("【步骤3】简报发送失败！\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="每日收盘简报")
    parser.add_argument("--analyze_date", type=str, required=False, help="要分析的日期（格式：YYYY-MM-DD），默认为最新交易日")
    parser.add_argument("--scheduled", action="store_true", help="启用定时运行模式（每天20:00检查交易日并运行）")
    # parser.add_argument("--dingtalk_webhook", type=str, required=False, help="钉钉机器人 Webhook URL")
    # parser.add_argument("--dingtalk_secret", type=str, required=False, help="钉钉机器人加签密钥")
    args = parser.parse_args()
    
    daily_close_brief = DailyCloseBrief()
    
    if args.scheduled:
        daily_close_brief.run_scheduled()
    else:
        daily_close_brief.run(args.analyze_date)
        dingtalk_webhook, dingtalk_secret = Config.get_dingtalk_config()
        # 如果配置了钉钉机器人，发送简报
        if dingtalk_webhook:
            daily_close_brief.send_to_dingtalk(
                date=args.analyze_date,
                webhook_url=dingtalk_webhook,
                secret=dingtalk_secret
            )