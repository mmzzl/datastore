# Supervisor 配置说明

## 安装 Supervisor

```bash
pip install supervisor
```

## 使用方法

### 1. 启动 Supervisor

```bash
# 启动 supervisord 守护进程
supervisord -c d:/work/datastore/case/supervisord.conf
```

### 2. 管理进程

```bash
# 查看所有进程状态
supervisorctl -c d:/work/datastore/case/supervisord.conf status

# 启动进程
supervisorctl -c d:/work/datastore/case/supervisord.conf start daily_close_brief

# 停止进程
supervisorctl -c d:/work/datastore/case/supervisord.conf stop daily_close_brief

# 重启进程
supervisorctl -c d:/work/datastore/case/supervisord.conf restart daily_close_brief

# 查看进程日志
supervisorctl -c d:/work/datastore/case/supervisord.conf tail -f daily_close_brief

# 重新加载配置
supervisorctl -c d:/work/datastore/case/supervisord.conf reread
supervisorctl -c d:/work/datastore/case/supervisord.conf update
```

### 3. 停止 Supervisor

```bash
# 停止所有进程并退出
supervisorctl -c d:/work/datastore/case/supervisord.conf shutdown

# 或者直接杀掉进程
kill -9 $(cat /tmp/supervisord.pid)
```

## 配置说明

### [program:daily_close_brief] 配置项

- **command**: 启动命令，`python daily_close_brief.py --scheduled`
- **directory**: 工作目录
- **autostart**: 随 supervisor 自动启动
- **autorestart**: 自动重启（异常退出时）
- **startretries**: 启动失败重试次数
- **stdout_logfile**: 进程标准输出日志文件
- **environment**: 环境变量设置

## 日志文件位置

- Supervisor 日志: `/tmp/supervisord.log`
- 进程日志: `d:/work/datastore/case/logs/supervisor/daily_close_brief.log`
- 应用日志: `d:/work/datastore/case/logs/daily_close_brief_YYYY-MM-DD.log`

## 注意事项

1. Windows 环境下，建议使用 `supervisord-win` 或 `supervisor-win` 替代
2. 确保日志目录存在：`logs/supervisor/`
3. 如果需要修改启动时间，请修改 `daily_close_brief.py` 中的 `SCHEDULED_TIME` 常量

## Windows 替代方案

如果在 Windows 上遇到问题，可以考虑以下替代方案：

### 方案1：使用 NSSM (Non-Sucking Service Manager)

```bash
# 下载 NSSM: https://nssm.cc/download

# 安装为 Windows 服务
nssm install DailyCloseBrief "C:\Python39\python.exe" "d:\work\datastore\case\daily_close_brief.py" "--scheduled"
nssm set DailyCloseBrief AppDirectory "d:\work\datastore\case"
nssm start DailyCloseBrief
```

### 方案2：使用 Windows 任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器：每天 20:00
4. 操作：启动程序 `python.exe`
5. 参数：`d:\work\datastore\case\daily_close_brief.py --scheduled`
6. 起始于：`d:\work\datastore\case`
