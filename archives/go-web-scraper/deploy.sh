#!/bin/bash

# 爬虫服务部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
INSTALL_DIR="/opt/go-web-scraper"
SERVICE_USER="crawler"
SERVICE_GROUP="crawler"

echo -e "${GREEN}=== 爬虫服务部署脚本 ===${NC}"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用 root 权限运行此脚本${NC}"
    echo "使用: sudo $0"
    exit 1
fi

# 1. 创建用户和组
echo -e "${YELLOW}1. 创建服务用户和组...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false "$SERVICE_USER"
    echo -e "${GREEN}✓ 用户 $SERVICE_USER 已创建${NC}"
else
    echo -e "${GREEN}✓ 用户 $SERVICE_USER 已存在${NC}"
fi

# 2. 创建安装目录
echo -e "${YELLOW}2. 创建安装目录...${NC}"
mkdir -p "$INSTALL_DIR/bin"
mkdir -p "$INSTALL_DIR/configs"
mkdir -p "$INSTALL_DIR/data"
echo -e "${GREEN}✓ 安装目录已创建${NC}"

# 3. 复制文件
echo -e "${YELLOW}3. 复制文件...${NC}"
if [ -f "bin/eastmoney_crawler" ] || [ -f "bin/eastmoney_crawler.exe" ]; then
    cp bin/eastmoney_crawler* "$INSTALL_DIR/bin/"
    chmod +x "$INSTALL_DIR/bin/eastmoney_crawler"
    echo -e "${GREEN}✓ eastmoney_crawler 已复制${NC}"
else
    echo -e "${RED}✗ 未找到 eastmoney_crawler 可执行文件${NC}"
    echo "请先运行: make build"
    exit 1
fi

if [ -f "bin/ssgs_crawler" ] || [ -f "bin/ssgs_crawler.exe" ]; then
    cp bin/ssgs_crawler* "$INSTALL_DIR/bin/"
    chmod +x "$INSTALL_DIR/bin/ssgs_crawler"
    echo -e "${GREEN}✓ ssgs_crawler 已复制${NC}"
else
    echo -e "${RED}✗ 未找到 ssgs_crawler 可执行文件${NC}"
    echo "请先运行: make build"
    exit 1
fi

if [ -f "configs/config.yaml" ]; then
    cp configs/config.yaml "$INSTALL_DIR/configs/"
    echo -e "${GREEN}✓ 配置文件已复制${NC}"
else
    echo -e "${YELLOW}⚠ 未找到配置文件，请手动配置${NC}"
fi

# 4. 设置权限
echo -e "${YELLOW}4. 设置文件权限...${NC}"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR/bin"/*
echo -e "${GREEN}✓ 权限已设置${NC}"

# 5. 创建日志目录
echo -e "${YELLOW}5. 创建日志目录...${NC}"
mkdir -p /var/log
touch /var/log/eastmoney_crawler.log
touch /var/log/eastmoney_crawler_error.log
touch /var/log/ssgs_crawler.log
touch /var/log/ssgs_crawler_error.log
chown "$SERVICE_USER:$SERVICE_GROUP" /var/log/eastmoney_crawler*.log
chown "$SERVICE_USER:$SERVICE_GROUP" /var/log/ssgs_crawler*.log
echo -e "${GREEN}✓ 日志文件已创建${NC}"

# 6. 安装服务
echo -e "${YELLOW}6. 安装 systemd 服务...${NC}"
if [ -f "eastmoney_crawler.service" ]; then
    cp eastmoney_crawler.service /etc/systemd/system/
    echo -e "${GREEN}✓ eastmoney_crawler 服务已安装${NC}"
fi

if [ -f "ssgs_crawler.service" ]; then
    cp ssgs_crawler.service /etc/systemd/system/
    echo -e "${GREEN}✓ ssgs_crawler 服务已安装${NC}"
fi

systemctl daemon-reload
echo -e "${GREEN}✓ systemd 已重新加载${NC}"

# 7. 设置开机自启
echo -e "${YELLOW}7. 设置开机自启...${NC}"
read -p "是否设置开机自启? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl enable eastmoney_crawler
    systemctl enable ssgs_crawler
    echo -e "${GREEN}✓ 开机自启已设置${NC}"
fi

# 8. 完成提示
echo ""
echo -e "${GREEN}=== 部署完成 ===${NC}"
echo ""
echo "安装目录: $INSTALL_DIR"
echo "服务用户: $SERVICE_USER"
echo ""
echo "服务管理命令:"
echo "  启动服务: sudo systemctl start eastmoney_crawler ssgs_crawler"
echo "  停止服务: sudo systemctl stop eastmoney_crawler ssgs_crawler"
echo "  查看状态: sudo systemctl status eastmoney_crawler ssgs_crawler"
echo "  查看日志: sudo journalctl -u eastmoney_crawler -f"
echo ""
echo "或使用管理脚本:"
echo "  ./manage_services.sh start all"
echo "  ./manage_services.sh status all"
echo "  ./manage_services.sh logs all"
echo ""
echo -e "${YELLOW}注意: 请确保已安装 Chrome 浏览器${NC}"
echo "  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
echo "  sudo apt-get install -y ./google-chrome-stable_current_amd64.deb"
