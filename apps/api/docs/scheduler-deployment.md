# 独立定时任务部署指南

## 概述

API 服务 (`main.py`) 和定时任务 (`scheduler_standalone.py`) 已拆分为独立进程运行。定时任务不会阻塞 API 请求响应。

## 架构

```
┌─────────────────┐     ┌─────────────────────────┐
│   API 进程       │     │   定时任务进程           │
│   main.py       │     │   scheduler_standalone.py│
│   uvicorn       │     │   BlockingScheduler     │
│   port: 8000    │     │   - 预缓存任务 17:00     │
│                 │     │   - 盘后任务 20:00       │
│                 │     │   - 盯盘任务 每5分钟     │
└─────────────────┘     └─────────────────────────┘
```

## 启动方式

### 方式一：命令行手动启动（开发/调试用）

**终端 1 - API 服务**

```bash
cd apps/api
uvicorn main:app --host 0.0.0.0 --port 8000
```

**终端 2 - 定时任务**

```bash
cd apps/api
python scheduler_standalone.py
```

### 方式二：systemd 服务（Linux 生产环境推荐）

创建 `/etc/systemd/system/scheduler.service`

```ini
[Unit]
Description=Stock Scheduler Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/datastore/apps/api
ExecStart=/path/to/venv/bin/python scheduler_standalone.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

然后：

```bash
sudo systemctl daemon-reload
sudo systemctl enable scheduler
sudo systemctl start scheduler
```

### 方式三：PM2（跨平台生产环境）

```bash
# 安装 PM2
npm install -g pm2

# 启动 API
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name api

# 启动定时任务
pm2 start scheduler_standalone.py --name scheduler

# 保存进程列表，开机自启
pm2 save
pm2 startup
```

### 方式四：supervisor（Linux）

创建 `/etc/supervisor/conf.d/scheduler.conf`

```ini
[program:scheduler]
command=/path/to/venv/bin/python scheduler_standalone.py
directory=/path/to/datastore/apps/api
autostart=true
autorestart=true
stderr_logfile=/var/log/scheduler.err.log
stdout_logfile=/var/log/scheduler.out.log
```

```bash
supervisorctl reread
supervisorctl update
supervisorctl start scheduler
```

## 定时任务配置

修改 `config/config.yaml` 中的相关配置：

```yaml
# 预缓存任务执行时间（建议在收盘后、盘后任务前）
after_market:
  pre_cache_scheduler_time: "17:00"

# 盘后任务执行时间（建议在收盘后）
  scheduler_time: "20:00"
  scheduler_timezone: "Asia/Shanghai"

# 盯盘任务
monitor:
  enabled: true
  interval: 300        # 盯盘间隔（秒），默认 5 分钟
  scheduler_time: "09:30"
  stocks:
    - code: "600519"
      name: "贵州茅台"
      hold: false
      buy_threshold: 0.05
      sell_threshold: 0.03
      cost_price: 0.0
      profit_target: 0.1
      stop_loss: 0.05
```

## 日志

日志文件位于 `logs/app.log`，按日期自动分割，保留 30 天。

查看实时日志：

```bash
tail -f logs/app.log
```

## 管理命令

### 查看任务状态

```bash
# systemd
sudo systemctl status scheduler

# PM2
pm2 list
pm2 logs scheduler
```

### 重启任务

```bash
# systemd
sudo systemctl restart scheduler

# PM2
pm2 restart scheduler
```

### 手动触发任务

```bash
# 进入 Python 环境
cd apps/api
python -c "
from scheduler_standalone import run_scheduled_job, run_pre_cache_job, run_monitor_job
# 选择要执行的任务
run_pre_cache_job()
"
```

## 注意事项

1. 定时任务和 API 服务**共用同一份配置**（`config/config.yaml`）
2. 定时任务使用 `BlockingScheduler`，会阻塞当前进程
3. 盯盘任务在非交易时间（周末、节假日）仍然会运行，但会跳过实际监控逻辑
4. 如果服务器重启，需要确保定时任务服务设置了自启动
