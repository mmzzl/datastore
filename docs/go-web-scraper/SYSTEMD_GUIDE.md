# 爬虫服务管理指南

本文档介绍如何使用 systemd 管理 eastmoney_crawler 和 ssgs_crawler 服务。

## 快速开始

### 1. 安装 Chrome 浏览器

```bash
# 下载 Chrome 安装包
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# 安装 Chrome
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb

# 验证安装
google-chrome --version
```

### 2. 编译项目

```bash
# 编译所有爬虫
make

# 或使用 PowerShell 脚本（Windows）
.\build.ps1
```

### 3. 部署服务

```bash
# 给脚本执行权限
chmod +x deploy.sh
chmod +x manage_services.sh

# 运行部署脚本
sudo ./deploy.sh
```

部署脚本会自动完成以下操作：
- 创建服务用户 `crawler`
- 创建安装目录 `/opt/go-web-scraper`
- 复制可执行文件和配置文件
- 安装 systemd 服务文件
- 设置文件权限和日志文件

## 服务管理

### 使用管理脚本（推荐）

```bash
# 安装所有服务
sudo ./manage_services.sh install all

# 启动所有服务
sudo ./manage_services.sh start all

# 停止所有服务
sudo ./manage_services.sh stop all

# 重启所有服务
sudo ./manage_services.sh restart all

# 查看所有服务状态
sudo ./manage_services.sh status all

# 查看所有服务日志
sudo ./manage_services.sh logs all

# 设置开机自启
sudo ./manage_services.sh enable all

# 取消开机自启
sudo ./manage_services.sh disable all
```

### 单独管理服务

```bash
# 只管理 eastmoney 服务
sudo ./manage_services.sh start eastmoney
sudo ./manage_services.sh stop eastmoney
sudo ./manage_services.sh status eastmoney
sudo ./manage_services.sh logs eastmoney

# 只管理 ssgs 服务
sudo ./manage_services.sh start ssgs
sudo ./manage_services.sh stop ssgs
sudo ./manage_services.sh status ssgs
sudo ./manage_services.sh logs ssgs
```

### 使用 systemctl 命令

```bash
# 启动服务
sudo systemctl start eastmoney_crawler
sudo systemctl start ssgs_crawler

# 停止服务
sudo systemctl stop eastmoney_crawler
sudo systemctl stop ssgs_crawler

# 重启服务
sudo systemctl restart eastmoney_crawler
sudo systemctl restart ssgs_crawler

# 查看服务状态
sudo systemctl status eastmoney_crawler
sudo systemctl status ssgs_crawler

# 查看服务日志
sudo journalctl -u eastmoney_crawler -f
sudo journalctl -u ssgs_crawler -f

# 设置开机自启
sudo systemctl enable eastmoney_crawler
sudo systemctl enable ssgs_crawler

# 取消开机自启
sudo systemctl disable eastmoney_crawler
sudo systemctl disable ssgs_crawler
```

## 服务配置

### 服务文件位置

- eastmoney_crawler: `/etc/systemd/system/eastmoney_crawler.service`
- ssgs_crawler: `/etc/systemd/system/ssgs_crawler.service`

### 服务配置说明

```ini
[Unit]
Description=服务描述
After=network.target mongodb.service  # 依赖网络和 MongoDB
Wants=mongodb.service                # 期望 MongoDB 运行

[Service]
Type=simple                          # 服务类型
User=crawler                         # 运行用户
Group=crawler                        # 运行组
WorkingDirectory=/opt/go-web-scraper # 工作目录
ExecStart=/opt/go-web-scraper/bin/eastmoney_crawler  # 启动命令
Restart=always                       # 自动重启
RestartSec=10                        # 重启间隔（秒）
StandardOutput=append:/var/log/eastmoney_crawler.log  # 标准输出日志
StandardError=append:/var/log/eastmoney_crawler_error.log  # 错误日志
SyslogIdentifier=eastmoney_crawler   # 系统日志标识
Environment=CONFIG_FILE=/opt/go-web-scraper/configs/config.yaml  # 环境变量
Environment=HEADLESS=true            # 环境变量

[Install]
WantedBy=multi-user.target          # 启动目标
```

### 修改服务配置

```bash
# 编辑服务文件
sudo systemctl edit eastmoney_crawler

# 或直接编辑
sudo nano /etc/systemd/system/eastmoney_crawler.service

# 重新加载配置
sudo systemctl daemon-reload

# 重启服务
sudo systemctl restart eastmoney_crawler
```

## 日志管理

### 查看日志

```bash
# 实时查看服务日志
sudo journalctl -u eastmoney_crawler -f
sudo journalctl -u ssgs_crawler -f

# 查看最近 100 行日志
sudo journalctl -u eastmoney_crawler -n 100

# 查看今天的日志
sudo journalctl -u eastmoney_crawler --since today

# 查看错误日志
sudo journalctl -u eastmoney_crawler -p err

# 查看文件日志
sudo tail -f /var/log/eastmoney_crawler.log
sudo tail -f /var/log/eastmoney_crawler_error.log
```

### 清理日志

```bash
# 清理旧日志
sudo journalctl --vacuum-time=7d  # 保留最近 7 天的日志
sudo journalctl --vacuum-size=100M  # 限制日志大小为 100MB

# 清理文件日志
sudo truncate -s 0 /var/log/eastmoney_crawler.log
sudo truncate -s 0 /var/log/eastmoney_crawler_error.log
```

## 故障排查

### 服务无法启动

```bash
# 查看服务状态
sudo systemctl status eastmoney_crawler

# 查看详细日志
sudo journalctl -u eastmoney_crawler -n 50 --no-pager

# 检查 Chrome 是否安装
google-chrome --version

# 检查配置文件
cat /opt/go-web-scraper/configs/config.yaml

# 手动运行测试
sudo -u crawler /opt/go-web-scraper/bin/eastmoney_crawler
```

### 服务频繁重启

```bash
# 查看重启次数
sudo systemctl show eastmoney_crawler -p NRestarts

# 查看重启原因
sudo journalctl -u eastmoney_crawler --since "1 hour ago" | grep "Restarting"

# 检查资源使用
sudo systemctl status eastmoney_crawler
```

### MongoDB 连接问题

```bash
# 检查 MongoDB 状态
sudo systemctl status mongodb

# 测试 MongoDB 连接
mongo mongodb://121.37.47.63:27017/crawler --eval "db.stats()"

# 检查防火墙
sudo ufw status
```

## 卸载服务

```bash
# 停止服务
sudo ./manage_services.sh stop all

# 卸载服务
sudo ./manage_services.sh uninstall all

# 删除文件
sudo rm -rf /opt/go-web-scraper
sudo rm -rf /var/log/eastmoney_crawler*.log
sudo rm -rf /var/log/ssgs_crawler*.log

# 删除用户
sudo userdel crawler
```

## 高级配置

### 自定义抓取间隔

编辑配置文件 `/opt/go-web-scraper/configs/config.yaml`：

```yaml
eastmoney:
  interval: 10m  # 修改抓取间隔
```

### 修改日志级别

编辑服务文件，添加环境变量：

```ini
[Service]
Environment=LOG_LEVEL=debug
```

### 限制资源使用

编辑服务文件：

```ini
[Service]
MemoryLimit=512M
CPUQuota=50%
```

## 监控和告警

### 使用 systemd 监控

```bash
# 查看服务运行时间
systemctl show eastmoney_crawler -p ActiveEnterTimestamp

# 查看服务进程 ID
systemctl show eastmoney_crawler -p MainPID
```

### 集成监控工具

可以集成以下监控工具：
- Prometheus + Grafana
- Zabbix
- Nagios
- 自定义监控脚本

## 常见问题

**Q: 服务启动失败，提示 Chrome 找不到？**

A: 确保已安装 Chrome 浏览器：
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
```

**Q: 如何修改 MongoDB 连接配置？**

A: 编辑配置文件 `/opt/go-web-scraper/configs/config.yaml`，然后重启服务：
```bash
sudo nano /opt/go-web-scraper/configs/config.yaml
sudo ./manage_services.sh restart all
```

**Q: 服务会自动重启吗？**

A: 是的，服务配置了 `Restart=always`，会自动重启。可以通过以下命令查看重启次数：
```bash
sudo systemctl show eastmoney_crawler -p NRestarts
```

**Q: 如何查看服务运行了多少时间？**

A: 使用以下命令：
```bash
sudo systemctl show eastmoney_crawler -p ActiveEnterTimestamp
systemctl status eastmoney_crawler
```

## 联系支持

如有问题，请查看日志文件：
- `/var/log/eastmoney_crawler.log`
- `/var/log/eastmoney_crawler_error.log`
- `/var/log/ssgs_crawler.log`
- `/var/log/ssgs_crawler_error.log`

或使用 journalctl 查看系统日志：
```bash
sudo journalctl -u eastmoney_crawler -f
sudo journalctl -u ssgs_crawler -f
```
