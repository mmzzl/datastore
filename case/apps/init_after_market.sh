#!/bin/bash

# 盘后分析服务快速初始化脚本

set -e

PROJECT_DIR="/root/apps"
cd "$PROJECT_DIR" || exit 1

echo "=========================================="
echo "盘后分析服务 - 快速初始化"
echo "=========================================="
echo ""

# 1. 检查Python
echo "[1/5] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3"
    echo "   请先安装 Python 3.8 或更高版本"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION"
echo ""

# 2. 安装依赖
echo "[2/5] 安装Python依赖..."
echo "   安装主项目依赖..."
pip3 install -r api/requirements.txt -q

echo "   安装盘后分析依赖..."
pip3 install -r after_market_requirements.txt -q
echo "✅ 依赖安装完成"
echo ""

# 3. 检查配置文件
echo "[3/5] 检查配置文件..."
if [ ! -f "api/config.yaml" ]; then
    echo "❌ 错误: 配置文件 api/config.yaml 不存在"
    exit 1
fi

# 检查关键配置
if grep -q "dingtalk_webhook:" api/config.yaml; then
    echo "✅ 钉钉webhook已配置"
else
    echo "⚠️  警告: 未配置钉钉webhook"
    echo "   请在 api/config.yaml 中添加以下配置："
    echo ""
    echo "   after_market:"
    echo "     dingtalk_webhook: \"https://oapi.dingtalk.com/robot/send?access_token=xxx\""
    echo "     dingtalk_secret: \"SECxxx\""
    echo ""
fi
echo ""

# 4. 运行测试
echo "[4/5] 运行功能测试..."
python3 test_after_market.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 所有测试通过"
else
    echo "⚠️  部分测试失败，请运行以下命令查看详情："
    echo "   python3 test_after_market.py"
fi
echo ""

# 5. 设置权限
echo "[5/5] 设置脚本权限..."
chmod +x start_scheduler.sh
echo "✅ 权限设置完成"
echo ""

echo "=========================================="
echo "初始化完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 手动测试一次分析："
echo "   python3 after_market_analysis.py"
echo ""
echo "2. 启动定时服务（守护进程）："
echo "   ./start_scheduler.sh --daemon"
echo ""
echo "3. 查看服务状态："
echo "   ./start_scheduler.sh --status"
echo ""
echo "4. 查看服务日志："
echo "   ./start_scheduler.sh --logs"
echo ""
echo "查看完整文档："
echo "   cat README_AFTER_MARKET.md"
echo "   cat SETUP_GUIDE.md"
echo ""
