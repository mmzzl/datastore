#!/bin/bash

# Linux 环境测试脚本

set -e

echo "=== Linux 环境测试脚本 ==="
echo ""

# 检查 Chrome 是否安装
echo "1. 检查 Chrome 安装状态..."
if command -v google-chrome &> /dev/null; then
    echo "✓ Google Chrome 已安装: $(google-chrome --version)"
elif command -v chromium-browser &> /dev/null; then
    echo "✓ Chromium 已安装: $(chromium-browser --version)"
else
    echo "✗ 未找到 Chrome 或 Chromium"
    echo ""
    echo "请安装 Chrome:"
    echo "  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    echo "  sudo apt-get install -y ./google-chrome-stable_current_amd64.deb"
    echo ""
    echo "或安装 Chromium:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y chromium-browser"
    exit 1
fi
echo ""

# 检查 Go 环境
echo "2. 检查 Go 环境..."
if command -v go &> /dev/null; then
    echo "✓ Go 已安装: $(go version)"
else
    echo "✗ 未找到 Go"
    exit 1
fi
echo ""

# 编译项目
echo "3. 编译项目..."
make clean
make build
echo ""

# 检查编译结果
echo "4. 检查编译结果..."
if [ -f "bin/eastmoney_crawler" ]; then
    echo "✓ eastmoney_crawler 编译成功"
else
    echo "✗ eastmoney_crawler 编译失败"
    exit 1
fi

if [ -f "bin/ssgs_crawler" ]; then
    echo "✓ ssgs_crawler 编译成功"
else
    echo "✗ ssgs_crawler 编译失败"
    exit 1
fi
echo ""

# 测试运行（单次抓取）
echo "5. 测试运行 eastmoney 爬虫..."
echo "注意：这将启动一次抓取，按 Ctrl+C 停止"
read -p "是否继续测试? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    timeout 30 ./bin/eastmoney_crawler || echo "测试完成或超时"
fi

echo ""
echo "=== 测试完成 ==="
echo ""
echo "如需后台运行爬虫，请使用:"
echo "  nohup ./bin/eastmoney_crawler > eastmoney.log 2>&1 &"
echo "  nohup ./bin/ssgs_crawler > ssgs.log 2>&1 &"
