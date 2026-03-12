#!/bin/bash

# 盘后分析服务启动脚本

PROJECT_DIR="/root/apps"
SCHEDULER_SCRIPT="$PROJECT_DIR/after_market_scheduler.py"
LOG_DIR="$PROJECT_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "盘后分析调度器启动脚本"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3，请先安装Python3"
    exit 1
fi

echo "Python版本: $(python3 --version)"

# 检查依赖
cd "$PROJECT_DIR" || exit 1

echo "检查Python依赖..."
python3 -c "import yaml, pymongo, requests, apscheduler" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装Python依赖..."
    pip3 install -r api/requirements.txt
fi

# 检查配置文件
if [ ! -f "api/config.yaml" ]; then
    echo "错误: 配置文件 api/config.yaml 不存在"
    exit 1
fi

echo "配置文件检查通过"

# 显示调度时间
echo "调度时间配置: $(grep 'scheduler_time:' api/config.yaml)"

# 选择启动方式
if [ "$1" == "--daemon" ] || [ "$1" == "-d" ]; then
    echo "以后台守护进程方式启动..."

    # 检查是否已安装为systemd服务
    if systemctl is-active --quiet after-market-scheduler.service; then
        echo "服务已在运行，先停止服务..."
        systemctl stop after-market-scheduler.service
    fi

    # 安装服务
    echo "安装systemd服务..."
    cp after-market-scheduler.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable after-market-scheduler.service

    # 启动服务
    echo "启动服务..."
    systemctl start after-market-scheduler.service

    # 查看状态
    sleep 2
    systemctl status after-market-scheduler.service

    echo ""
    echo "服务已启动为守护进程"
    echo "查看日志: journalctl -u after-market-scheduler.service -f"
    echo "停止服务: systemctl stop after-market-scheduler.service"
    echo "禁用开机启动: systemctl disable after-market-scheduler.service"

elif [ "$1" == "--stop" ]; then
    echo "停止服务..."
    systemctl stop after-market-scheduler.service
    echo "服务已停止"

elif [ "$1" == "--status" ]; then
    echo "查看服务状态..."
    systemctl status after-market-scheduler.service

elif [ "$1" == "--logs" ]; then
    echo "查看服务日志..."
    journalctl -u after-market-scheduler.service -f

elif [ "$1" == "--test" ]; then
    echo "单次执行测试..."
    python3 after_market_scheduler.py --once

elif [ "$1" == "--manual" ]; then
    echo "手动执行盘后分析..."
    python3 after_market_analysis.py "$2"

else
    echo ""
    echo "使用方法:"
    echo "  $0 --daemon     以守护进程方式启动"
    echo "  $0 --stop       停止服务"
    echo "  $0 --status     查看服务状态"
    echo "  $0 --logs       查看服务日志"
    echo "  $0 --test       单次测试执行"
    echo "  $0 --manual [YYYY-MM-DD]  手动执行指定日期的分析"
    echo ""
    echo "前台运行（测试用）:"
    echo "  python3 after_market_scheduler.py"
    echo ""
fi
