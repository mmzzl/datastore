# Scrapy settings for python_web_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging

BOT_NAME = "python_web_scraper"

SPIDER_MODULES = ["internal.spider"]
NEWSPIDER_MODULE = "internal.spider"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# 日志设置
LOG_LEVEL = "WARNING"  # 只输出 WARNING 及以上级别的日志
LOG_FILE = None  # 不输出到文件，避免写入 syslog

# 配置特定组件的日志级别（只输出重要信息）
logging.getLogger("scrapy.core.scraper").setLevel(logging.WARNING)
logging.getLogger("scrapy.core.engine").setLevel(logging.WARNING)
logging.getLogger("scrapy.extensions.logstats").setLevel(logging.WARNING)
logging.getLogger("scrapy.core.downloader").setLevel(logging.WARNING)
logging.getLogger("scrapy.core.downloader.handlers").setLevel(logging.WARNING)
logging.getLogger("scrapy.core.downloader.middleware").setLevel(logging.WARNING)
logging.getLogger("scrapy.core.scraper").setLevel(logging.WARNING)
logging.getLogger("scrapy.core.spidermw").setLevel(logging.WARNING)

# 配置最大并发请求（默认: 16）
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4

# 配置同一网站的请求延迟（默认: 0）
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# 禁用 cookies（默认启用）
# COOKIES_ENABLED = False

# 禁用 Telnet 控制台（默认启用）
# TELNETCONSOLE_ENABLED = False

# 覆盖默认请求头：
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# 启用或禁用爬虫中间件
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'python_web_scraper.middlewares.PythonWebScraperSpiderMiddleware': 543,
# }

# 启用或禁用下载器中间件
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'python_web_scraper.middlewares.PythonWebScraperDownloaderMiddleware': 543,
# }

# 启用或禁用扩展
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# 配置项目管道
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "internal.pipeline.mongo_pipeline.MongoPipeline": 300,
}

# 启用并配置 AutoThrottle 扩展（默认禁用）
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# 下载超时设置
DOWNLOAD_TIMEOUT = 30
