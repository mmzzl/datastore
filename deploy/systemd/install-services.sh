#!/bin/bash
# Systemd 服务安装脚本
# 用法: sudo bash install-services.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="/etc/systemd/system"
APP_DIR="/home/fantom/datastore/apps/api"

echo "=== 安装 Systemd 服务 ==="

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo "请使用 root 权限运行此脚本"
    exit 1
fi

# 检查应用目录是否存在
if [ ! -d "$APP_DIR" ]; then
    echo "警告: 应用目录 $APP_DIR 不存在"
    echo "请修改服务配置中的 WorkingDirectory 路径"
fi

# 复制服务文件
echo "复制服务文件到 $SYSTEMD_DIR ..."
cp "$SCRIPT_DIR/scheduler-service.service" "$SYSTEMD_DIR/"
cp "$SCRIPT_DIR/kline-scraper.service" "$SYSTEMD_DIR/"

# 设置权限
chmod 644 "$SYSTEMD_DIR/scheduler-service.service"
chmod 644 "$SYSTEMD_DIR/kline-scraper.service"

# 重新加载 systemd
echo "重新加载 systemd daemon ..."
systemctl daemon-reload

# 启用服务（开机自启）
echo "启用服务开机自启 ..."
systemctl enable scheduler-service.service
systemctl enable kline-scraper.service

echo ""
echo "=== 安装完成 ==="
echo ""
echo "可用命令:"
echo "  启动服务:"
echo "    sudo systemctl start scheduler-service"
echo "    sudo systemctl start kline-scraper"
echo ""
echo "  停止服务:"
echo "    sudo systemctl stop scheduler-service"
echo "    sudo systemctl stop kline-scraper"
echo ""
echo "  查看状态:"
echo "    sudo systemctl status scheduler-service"
echo "    sudo systemctl status kline-scraper"
echo ""
echo "  查看日志:"
echo "    sudo journalctl -u scheduler-service -f"
echo "    sudo journalctl -u kline-scraper -f"
echo ""
