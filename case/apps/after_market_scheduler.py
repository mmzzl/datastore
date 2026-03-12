"""
盘后分析定时任务调度器
在指定时间自动执行盘后数据分析
"""

import logging
import sys
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import yaml
import pytz

from after_market_analysis import AfterMarketAnalysisService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class AfterMarketScheduler:
    """盘后分析调度器"""

    def __init__(self, config_path: str = None):
        """
        初始化调度器

        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'api', 'config.yaml')

        self.config = self._load_config(config_path)
        self.scheduler = BlockingScheduler(timezone='Asia/Shanghai')
        self.config_path = config_path

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            else:
                logger.error(f"配置文件不存在: {config_path}")
                return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def run_analysis_job(self):
        """执行盘后分析任务"""
        try:
            logger.info("=" * 60)
            logger.info("定时任务触发：开始盘后数据分析")
            logger.info("=" * 60)

            # 创建分析服务实例
            service = AfterMarketAnalysisService(self.config_path)

            # 执行分析（使用最新日期）
            service.run_analysis()

            logger.info("=" * 60)
            logger.info("定时任务执行完成")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"执行分析任务失败: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """启动调度器"""
        try:
            # 获取调度时间配置
            after_market_config = self.config.get('after_market', {})
            scheduler_time = after_market_config.get('scheduler_time', '17:30')

            # 解析时间
            hour, minute = map(int, scheduler_time.split(':'))

            logger.info("=" * 60)
            logger.info("盘后分析调度器启动")
            logger.info("=" * 60)
            logger.info(f"调度时间: 每天 {scheduler_time} (Asia/Shanghai)")
            logger.info(f"时区: Asia/Shanghai")
            logger.info("=" * 60)

            # 添加定时任务
            # 工作日执行（周一到周五）
            self.scheduler.add_job(
                self.run_analysis_job,
                trigger=CronTrigger(
                    hour=hour,
                    minute=minute,
                    day_of_week='mon-fri',
                    timezone='Asia/Shanghai'
                ),
                id='after_market_analysis',
                name='盘后数据分析',
                max_instances=1,
                coalesce=True  # 如果错过执行时间，合并到下一次执行
            )

            # 打印即将执行的任务
            self.scheduler.print_jobs()

            # 启动调度器
            logger.info("调度器已启动，等待定时任务...")
            self.scheduler.start()

        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            import traceback
            traceback.print_exc()

    def stop(self):
        """停止调度器"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("调度器已停止")


def main():
    """主函数"""
    import sys

    # 解析命令行参数
    config_path = None
    run_once = False

    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            run_once = True
        else:
            config_path = sys.argv[1]

    if len(sys.argv) > 2:
        if sys.argv[2] == '--once':
            run_once = True

    # 创建调度器实例
    scheduler = AfterMarketScheduler(config_path)

    if run_once:
        # 只执行一次
        logger.info("单次执行模式")
        scheduler.run_analysis_job()
    else:
        # 启动定时调度
        scheduler.start()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n收到退出信号，正在关闭调度器...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"调度器异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
