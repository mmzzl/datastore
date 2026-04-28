# Celery Qlib Training System

## 问题

Qlib 训练任务在 API 进程内的 threading.Thread 中运行，无法持久化进度、不支持取消/重跑，API 重启导致训练中断。

## 方案

引入 Celery + Redis broker + MongoDB backend，将 Qlib 训练迁移到独立 worker 进程。

## Scope

仅 Qlib 模型训练任务。APScheduler 其他任务不动。

## 主要改动

1. 新增 `celery_app.py` — Celery 应用实例
2. 新增 `train_task.py` — 训练任务定义
3. 修改 `api/endpoints/qlib.py` — 加 tasks/revoke/rerun 接口
4. 修改 `QlibTopStocks.vue` + `qlib store` — 任务列表+进度+取消+重跑
5. `requirements.txt` 加 celery
6. systemd 服务文件

**详细设计**: `docs/superpowers/specs/2026-04-27-celery-training-system-design.md`
