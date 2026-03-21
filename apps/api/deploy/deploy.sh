#!/bin/bash

# 部署脚本

echo "=== News API 部署脚本 ==="

echo "1. 安装依赖"
pip install -r requirements.txt

echo "2. 启动API服务"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
