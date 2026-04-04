# Bug跟踪系统

## 概述

本项目使用GitHub Issues进行bug跟踪，配合本文档目录进行详细bug分析记录。

## Bug生命周期

1. **New**: 新发现，待确认
2. **Confirmed**: 已确认，待分配
3. **Assigned**: 已分配，处理中
4. **In Progress**: 正在修复
5. **Fixed**: 已修复，待验证
6. **Verified**: 已验证，可关闭
7. **Closed**: 已关闭

## 优先级定义

- P0-Critical: 系统崩溃、数据丢失、安全漏洞
- P1-High: 核心功能不可用
- P2-Medium: 功能异常但有替代方案
- P3-Low: UI问题、优化建议

## Bug报告规范

使用 `template.md` 填写详细bug报告，或在GitHub上直接提交Issue。

## 统计指标

- Bug发现率 = 新增Bug数 / 迭代周期
- Bug修复率 = 已修复Bug数 / 总Bug数
- Bug重开率 = 重开Bug数 / 已修复Bug数
