# 新闻智能分析实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 通过关键词+LLM(DeepSeek)对新闻进行深度分析，提取重点和明日操作建议

**Architecture:** 新闻先进行关键词预处理，再调用LLM进行深度分析，输出结构化分析结果

**Tech Stack:** Python, DeepSeek API, 关键词规则引擎

---

### Task 1: 添加LLM配置

**Files:**
- Modify: `case/apps/api/app/core/config.py`
- Modify: `case/apps/api/config.yaml`

**Step 1: 修改 config.py 添加LLM配置**

```python
# 添加配置
llm_provider: str = "deepseek"
llm_api_key: str = ""
llm_model: str = "deepseek-chat"
llm_base_url: str = "https://api.deepseek.com"
```

**Step 2: 修改 config.yaml**

```yaml
llm:
  provider: "deepseek"
  api_key: ""
  model: "deepseek-chat"
  base_url: "https://api.deepseek.com"
```

**Step 3: Commit**

```bash
git add case/apps/api/app/core/config.py case/apps/api/config.yaml
git commit -m "feat: 添加LLM配置"
```

---

### Task 2: 创建LLM客户端

**Files:**
- Create: `case/apps/api/app/collector/llm_client.py`

**Step 1: 创建 llm_client.py**

实现完整的LLM客户端，支持：
- DeepSeek API调用
- 构建新闻分析prompt
- 解析JSON响应
- 关键词分析后备方案

**Step 2: Commit**

```bash
git add case/apps/api/app/collector/llm_client.py
git commit -m "feat: 添加LLM客户端"
```

---

### Task 3: 更新调度任务集成新闻分析

**Files:**
- Modify: `case/apps/api/app/scheduler/job.py`

**Step 1: 更新 job.py 集成新闻分析**

```python
from ..collector import AkshareClient, NewsClient, LLMClient

# 在采集流程中加入新闻分析
news = self._fetch_news(date_str)
news_analysis = self._analyze_news(news)
```

**Step 2: Commit**

```bash
git add case/apps/api/app/scheduler/job.py
git commit -m "feat: 集成新闻智能分析"
```

---

**Plan complete and saved to `docs/plans/2026-02-28-news-analysis.md`**

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
