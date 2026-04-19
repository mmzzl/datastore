#!/bin/bash
set -e

SERVICE_NAME="scheduler"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SOURCE_FILE="$(cd "$(dirname "$0")" && pwd)/scheduler.service"

echo "==> Installing ${SERVICE_NAME} service..."

cp "${SOURCE_FILE}" "${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}

echo "==> Service installed and enabled."
echo ""
echo "Usage:"
echo "  systemctl start ${SERVICE_NAME}     # 启动"
echo "  systemctl stop ${SERVICE_NAME}      # 停止"
echo "  systemctl restart ${SERVICE_NAME}   # 重启"
echo "  systemctl status ${SERVICE_NAME}    # 查看状态"
echo "  journalctl -u ${SERVICE_NAME} -f    # 查看实时日志"
