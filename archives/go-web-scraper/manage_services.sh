#!/bin/bash

# 爬虫服务管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 服务名称
EASTMONEY_SERVICE="eastmoney_crawler"
SSGS_SERVICE="ssgs_crawler"

# 日志目录
LOG_DIR="/var/log"
INSTALL_DIR="/opt/go-web-scraper"

# 检查是否以 root 权限运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}请使用 root 权限运行此脚本${NC}"
        echo "使用: sudo $0 $1"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "爬虫服务管理脚本"
    echo ""
    echo "用法: $0 [命令] [服务]"
    echo ""
    echo "命令:"
    echo "  install     安装服务"
    echo "  uninstall   卸载服务"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      查看服务状态"
    echo "  logs        查看服务日志"
    echo "  enable      开机自启"
    echo "  disable     取消开机自启"
    echo ""
    echo "服务:"
    echo "  eastmoney   EastMoney 快讯爬虫"
    echo "  ssgs        上市公司新闻爬虫"
    echo "  all         所有爬虫（默认）"
    echo ""
    echo "示例:"
    echo "  $0 install all          # 安装所有服务"
    echo "  $0 start eastmoney      # 启动 eastmoney 服务"
    echo "  $0 status all           # 查看所有服务状态"
    echo "  $0 logs ssgs           # 查看 ssgs 服务日志"
}

# 安装服务
install_service() {
    check_root "install $1"
    
    local service=$1
    local service_file=""
    
    if [ "$service" = "eastmoney" ] || [ "$service" = "all" ]; then
        service_file="eastmoney_crawler.service"
        if [ -f "$service_file" ]; then
            echo -e "${GREEN}安装 eastmoney_crawler 服务...${NC}"
            cp "$service_file" "/etc/systemd/system/"
            systemctl daemon-reload
            echo -e "${GREEN}✓ eastmoney_crawler 服务已安装${NC}"
        else
            echo -e "${RED}✗ 未找到 $service_file${NC}"
        fi
    fi
    
    if [ "$service" = "ssgs" ] || [ "$service" = "all" ]; then
        service_file="ssgs_crawler.service"
        if [ -f "$service_file" ]; then
            echo -e "${GREEN}安装 ssgs_crawler 服务...${NC}"
            cp "$service_file" "/etc/systemd/system/"
            systemctl daemon-reload
            echo -e "${GREEN}✓ ssgs_crawler 服务已安装${NC}"
        else
            echo -e "${RED}✗ 未找到 $service_file${NC}"
        fi
    fi
}

# 卸载服务
uninstall_service() {
    check_root "uninstall $1"
    
    local service=$1
    
    if [ "$service" = "eastmoney" ] || [ "$service" = "all" ]; then
        echo -e "${YELLOW}卸载 eastmoney_crawler 服务...${NC}"
        systemctl stop "$EASTMONEY_SERVICE" 2>/dev/null || true
        systemctl disable "$EASTMONEY_SERVICE" 2>/dev/null || true
        rm -f "/etc/systemd/system/$EASTMONEY_SERVICE.service"
        systemctl daemon-reload
        echo -e "${GREEN}✓ eastmoney_crawler 服务已卸载${NC}"
    fi
    
    if [ "$service" = "ssgs" ] || [ "$service" = "all" ]; then
        echo -e "${YELLOW}卸载 ssgs_crawler 服务...${NC}"
        systemctl stop "$SSGS_SERVICE" 2>/dev/null || true
        systemctl disable "$SSGS_SERVICE" 2>/dev/null || true
        rm -f "/etc/systemd/system/$SSGS_SERVICE.service"
        systemctl daemon-reload
        echo -e "${GREEN}✓ ssgs_crawler 服务已卸载${NC}"
    fi
}

# 启动服务
start_service() {
    check_root "start $1"
    
    local service=$1
    
    if [ "$service" = "eastmoney" ] || [ "$service" = "all" ]; then
        echo -e "${GREEN}启动 eastmoney_crawler 服务...${NC}"
        systemctl start "$EASTMONEY_SERVICE"
        systemctl status "$EASTMONEY_SERVICE" --no-pager
    fi
    
    if [ "$service" = "ssgs" ] || [ "$service" = "all" ]; then
        echo -e "${GREEN}启动 ssgs_crawler 服务...${NC}"
        systemctl start "$SSGS_SERVICE"
        systemctl status "$SSGS_SERVICE" --no-pager
    fi
}

# 停止服务
stop_service() {
    check_root "stop $1"
    
    local service=$1
    
    if [ "$service" = "eastmoney" ] || [ "$service" = "all" ]; then
        echo -e "${YELLOW}停止 eastmoney_crawler 服务...${NC}"
        systemctl stop "$EASTMONEY_SERVICE"
    fi
    
    if [ "$service" = "ssgs" ] || [ "$service" = "all" ]; then
        echo -e "${YELLOW}停止 ssgs_crawler 服务...${NC}"
        systemctl stop "$SSGS_SERVICE"
    fi
}

# 重启服务
restart_service() {
    check_root "restart $1"
    
    local service=$1
    
    if [ "$service" = "eastmoney" ] || [ "$service" = "all" ]; then
        echo -e "${YELLOW}重启 eastmoney_crawler 服务...${NC}"
        systemctl restart "$EASTMONEY_SERVICE"
        systemctl status "$EASTMONEY_SERVICE" --no-pager
    fi
    
    if [ "$service" = "ssgs" ] || [ "$service" = "all" ]; then
        echo -e "${YELLOW}重启 ssgs_crawler 服务...${NC}"
        systemctl restart "$SSGS_SERVICE"
        systemctl status "$SSGS_SERVICE" --no-pager
    fi
}

# 查看服务状态
status_service() {
    local service=$1
    
    if [ "$service" = "eastmoney" ] || [ "$service" = "all" ]; then
        echo -e "${GREEN}=== eastmoney_crawler 服务状态 ===${NC}"
        systemctl status "$EASTMONEY_SERVICE" --no-pager || echo -e "${RED}服务未安装${NC}"
        echo ""
    fi
    
    if [ "$service" = "ssgs" ] || [ "$service" = "all" ]; then
        echo -e "${GREEN}=== ssgs_crawler 服务状态 ===${NC}"
        systemctl status "$SSGS_SERVICE" --no-pager || echo -e "${RED}服务未安装${NC}"
        echo ""
    fi
}

# 查看服务日志
logs_service() {
    local service=$1
    
    if [ "$service" = "eastmoney" ]; then
        echo -e "${GREEN}=== eastmoney_crawler 服务日志 ===${NC}"
        journalctl -u "$EASTMONEY_SERVICE" -f
    elif [ "$service" = "ssgs" ]; then
        echo -e "${GREEN}=== ssgs_crawler 服务日志 ===${NC}"
        journalctl -u "$SSGS_SERVICE" -f
    elif [ "$service" = "all" ]; then
        echo -e "${GREEN}=== 所有爬虫服务日志 ===${NC}"
        journalctl -u "$EASTMONEY_SERVICE" -u "$SSGS_SERVICE" -f
    fi
}

# 开机自启
enable_service() {
    check_root "enable $1"
    
    local service=$1
    
    if [ "$service" = "eastmoney" ] || [ "$service" = "all" ]; then
        echo -e "${GREEN}设置 eastmoney_crawler 开机自启...${NC}"
        systemctl enable "$EASTMONEY_SERVICE"
        echo -e "${GREEN}✓ eastmoney_crawler 已设置开机自启${NC}"
    fi
    
    if [ "$service" = "ssgs" ] || [ "$service" = "all" ]; then
        echo -e "${GREEN}设置 ssgs_crawler 开机自启...${NC}"
        systemctl enable "$SSGS_SERVICE"
        echo -e "${GREEN}✓ ssgs_crawler 已设置开机自启${NC}"
    fi
}

# 取消开机自启
disable_service() {
    check_root "disable $1"
    
    local service=$1
    
    if [ "$service" = "eastmoney" ] || [ "$service" = "all" ]; then
        echo -e "${YELLOW}取消 eastmoney_crawler 开机自启...${NC}"
        systemctl disable "$EASTMONEY_SERVICE"
        echo -e "${GREEN}✓ eastmoney_crawler 已取消开机自启${NC}"
    fi
    
    if [ "$service" = "ssgs" ] || [ "$service" = "all" ]; then
        echo -e "${YELLOW}取消 ssgs_crawler 开机自启...${NC}"
        systemctl disable "$SSGS_SERVICE"
        echo -e "${GREEN}✓ ssgs_crawler 已取消开机自启${NC}"
    fi
}

# 主函数
main() {
    local command=$1
    local service=${2:-all}
    
    case "$command" in
        install)
            install_service "$service"
            ;;
        uninstall)
            uninstall_service "$service"
            ;;
        start)
            start_service "$service"
            ;;
        stop)
            stop_service "$service"
            ;;
        restart)
            restart_service "$service"
            ;;
        status)
            status_service "$service"
            ;;
        logs)
            logs_service "$service"
            ;;
        enable)
            enable_service "$service"
            ;;
        disable)
            disable_service "$service"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

main "$@"
