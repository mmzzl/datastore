# 盘后信息服务实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建盘后信息服务，自动获取baostock行情数据+新闻API数据，保存到MongoDB，发送钉钉通知，并提供Web界面查看

**Architecture:** Python FastAPI后端 + Vue3 Element Plus前端，定时任务采集数据并推送通知

**Tech Stack:** Python 3.10+, FastAPI, baostock, pymongo, APScheduler, Vue3, Element Plus

---

### Task 1: 创建项目基础结构

**Files:**
- Create: `case/apps/after-market-service/`

**Step 1: 创建项目目录**

```bash
mkdir -p case/apps/after-market-service
```

**Step 2: 创建基础配置文件**

Create: `case/apps/after-market-service/config.yaml`
```yaml
database:
  host: "localhost"
  port: 27017
  name: "after_market"

news_api:
  base_url: "http://life233.top"
  username: "admin"
  password: "admin"

dingtalk:
  webhook_url: ""
  secret: ""

scheduler:
  time: "20:00"
  timezone: "Asia/Shanghai"

app:
  host: "0.0.0.0"
  port: 8080
```

**Step 3: 创建 requirements.txt**

Create: `case/apps/after-market-service/requirements.txt`
```
fastapi==0.109.0
uvicorn==0.27.0
baostock==0.8.8
pymongo==4.6.1
apscheduler==3.10.4
requests==2.31.0
pydantic==2.5.3
python-dotenv==1.0.0
pyyaml==6.0.1
```

**Step 4: Commit**

```bash
git add case/apps/after-market-service/
git commit -m "feat: 创建盘后信息服务基础结构"
```

---

### Task 2: 创建数据采集模块

**Files:**
- Create: `case/apps/after-market-service/app/collector/__init__.py`
- Create: `case/apps/after-market-service/app/collector/baostock_client.py`
- Create: `case/apps/after-market-service/app/collector/news_client.py`

**Step 1: 创建 baostock_client.py**

```python
import baostock as bs
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

class BaoStockClient:
    def __init__(self):
        self._login()
    
    def _login(self):
        lg = bs.login()
        if lg.error_code != '0':
            raise Exception(f"baostock login failed: {lg.error_msg}")
    
    def _logout(self):
        bs.logout()
    
    def get_market_overview(self, date: str) -> Dict:
        """获取大盘概况"""
        # 获取上证指数
        rs = bs.query_history_k_data_plus(
            "sh.000001",
            "date,code,open,high,low,close,volume,amount,pctchg",
            start_date=date,
            end_date=date,
            frequency="d"
        )
        # 获取深证成指
        rs_sz = bs.query_history_k_data_plus(
            "sz.399001",
            "date,code,open,high,low,close,volume,amount,pctchg",
            start_date=date,
            end_date=date,
            frequency="d"
        )
        # 获取创业板指
        rs_cyb = bs.query_history_k_data_plus(
            "sz.399006",
            "date,code,open,high,low,close,volume,amount,pctchg",
            start_date=date,
            end_date=date,
            frequency="d"
        )
        # 处理数据...
        return {"indices": [], "stats": {}, "capital": {}}
    
    def get_stock_data(self, date: str, limit: int = 100) -> List[Dict]:
        """获取个股数据"""
        rs = bs.query_stock_basic()
        # 获取股票列表和行情...
        return []
    
    def get_sector_data(self, date: str) -> List[Dict]:
        """获取板块数据"""
        rs = bs.query_stock_sector()
        return []
    
    def get_capital_flow(self, date: str) -> Dict:
        """获取资金流向"""
        return {"main": 0, "super": 0, "large": 0}
```

**Step 2: 创建 news_client.py**

```python
import requests
from typing import List, Dict, Optional
from datetime import datetime

class NewsClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.token = self._get_token(username, password)
    
    def _get_token(self, username: str, password: str) -> str:
        resp = requests.post(
            f"{self.base_url}/api/auth/token",
            json={"username": username, "password": password}
        )
        return resp.json()["access_token"]
    
    def get_daily_news(self, date: Optional[str] = None, limit: int = 10, offset: int = 0) -> Dict:
        """获取日新闻"""
        resp = requests.get(
            f"{self.base_url}/api/news/daily",
            params={"date": date, "limit": limit, "offset": offset},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return resp.json()
    
    def get_weekly_news(self, date: Optional[str] = None, limit: int = 10, offset: int = 0) -> Dict:
        """获取周新闻"""
        resp = requests.get(
            f"{self.base_url}/api/news/weekly",
            params={"date": date, "limit": limit, "offset": offset},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return resp.json()
    
    def get_monthly_news(self, date: Optional[str] = None, limit: int = 10, offset: int = 0) -> Dict:
        """获取月新闻"""
        resp = requests.get(
            f"{self.base_url}/api/news/monthly",
            params={"date": date, "limit": limit, "offset": offset},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return resp.json()
```

**Step 3: 创建 __init__.py**

```python
from .baostock_client import BaoStockClient
from .news_client import NewsClient

__all__ = ["BaoStockClient", "NewsClient"]
```

**Step 4: Commit**

```bash
git add case/apps/after-market-service/app/collector/
git commit -m "feat: 添加数据采集模块(baostock + news API)"
```

---

### Task 3: 创建存储模块

**Files:**
- Create: `case/apps/after-market-service/app/storage/__init__.py`
- Create: `case/apps/after-market-service/app/storage/mongo_client.py`
- Create: `case/apps/after-market-service/app/storage/models.py`

**Step 1: 创建 models.py**

```python
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class IndexData(BaseModel):
    code: str
    name: str
    close: float
    change: float
    pct_chg: float
    volume: float

class MarketOverview(BaseModel):
    date: str
    indices: List[IndexData]
    up_count: int
    down_count: int
    limit_up: int
    limit_down: int
    break_board: int

class StockData(BaseModel):
    code: str
    name: str
    open: float
    high: float
    low: float
    close: float
    pct_chg: float
    turnover: float
    amplitude: float

class CapitalFlow(BaseModel):
    main: float
    super_large: float
    large: float

class SectorData(BaseModel):
    code: str
    name: str
    pct_chg: float

class NewsItem(BaseModel):
    code: str
    title: str
    summary: str
    show_time: str
    stock_list: List[str]
    sentiment: str  # 利好/利空/中性

class Recommendation(BaseModel):
    market: Dict  # 趋势/仓位/风险
    sectors: Dict  # 主线/规避/轮动
    stocks: Dict  # 持仓/关注/避雷

class AfterMarketData(BaseModel):
    date: str
    created_at: datetime
    market_overview: MarketOverview
    stocks: List[StockData]
    capital_flow: CapitalFlow
    sectors: List[SectorData]
    news: List[NewsItem]
    recommendations: Recommendation
```

**Step 2: 创建 mongo_client.py**

```python
from pymongo import MongoClient
from typing import Optional, List
from datetime import datetime
from .models import AfterMarketData

class MongoStorage:
    def __init__(self, host: str, port: int, db_name: str):
        self.client = MongoClient(host, port)
        self.db = self.client[db_name]
        self.collection = self.db["after_market"]
    
    def save(self, data: AfterMarketData) -> str:
        result = self.collection.insert_one(data.model_dump())
        return str(result.inserted_id)
    
    def get_by_date(self, date: str) -> Optional[dict]:
        return self.collection.find_one({"date": date})
    
    def get_all(self, limit: int = 50) -> List[dict]:
        return list(self.collection.find().sort("date", -1).limit(limit))
    
    def delete(self, date: str) -> int:
        result = self.collection.delete_one({"date": date})
        return result.deleted_count
```

**Step 3: 创建 __init__.py**

```python
from .mongo_client import MongoStorage
from .models import AfterMarketData

__all__ = ["MongoStorage", "AfterMarketData"]
```

**Step 4: Commit**

```bash
git add case/apps/after-market-service/app/storage/
git commit -m "feat: 添加MongoDB存储模块"
```

---

### Task 4: 创建通知模块

**Files:**
- Create: `case/apps/after-market-service/app/notify/__init__.py`
- Create: `case/apps/after-market-service/app/notify/dingtalk.py`

**Step 1: 创建 dingtalk.py**

```python
import requests
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import Dict

class DingTalkNotifier:
    def __init__(self, webhook_url: str, secret: str = ""):
        self.webhook_url = webhook_url
        self.secret = secret
    
    def _sign(self, timestamp: int) -> str:
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
    
    def send(self, data: Dict) -> bool:
        timestamp = int(datetime.now().timestamp() * 1000)
        
        # 构建消息内容
        msg = self._build_message(data)
        
        params = {"timestamp": timestamp, "sign": self._sign(timestamp)} if self.secret else {}
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"盘后信息 {data.get('date', '')}",
                "text": msg
            }
        }
        
        resp = requests.post(self.webhook_url, json=payload, params=params)
        return resp.status_code == 200
    
    def _build_message(self, data: Dict) -> str:
        # 构建markdown消息...
        msg = f"## 📊 盘后信息 {data.get('date', '')}\n\n"
        # 添加各个部分...
        return msg
```

**Step 2: 创建 __init__.py**

```python
from .dingtalk import DingTalkNotifier

__all__ = ["DingTalkNotifier"]
```

**Step 3: Commit**

```bash
git add case/apps/after-market-service/app/notify/
git commit -m "feat: 添加钉钉通知模块"
```

---

### Task 5: 创建定时任务模块

**Files:**
- Create: `case/apps/after-market-service/app/scheduler/__init__.py`
- Create: `case/apps/after-market-service/app/scheduler/job.py`

**Step 1: 创建 job.py**

```python
from datetime import datetime, date
from typing import Dict
from ..collector import BaoStockClient, NewsClient
from ..storage import MongoStorage, AfterMarketData
from ..notify import DingTalkNotifier

class AfterMarketJob:
    def __init__(self, config: Dict):
        self.config = config
        self.bs_client = BaoStockClient()
        self.news_client = NewsClient(
            config["news_api"]["base_url"],
            config["news_api"]["username"],
            config["news_api"]["password"]
        )
        self.storage = MongoStorage(
            config["database"]["host"],
            config["database"]["port"],
            config["database"]["name"]
        )
        self.notifier = DingTalkNotifier(
            config["dingtalk"]["webhook_url"],
            config["dingtalk"].get("secret", "")
        )
    
    def run(self):
        """执行盘后数据采集任务"""
        today = date.today().strftime("%Y-%m-%d")
        
        # 1. 获取大盘概况
        market_overview = self.bs_client.get_market_overview(today)
        
        # 2. 获取个股数据
        stocks = self.bs_client.get_stock_data(today)
        
        # 3. 获取资金流向
        capital_flow = self.bs_client.get_capital_flow(today)
        
        # 4. 获取板块数据
        sectors = self.bs_client.get_sector_data(today)
        
        # 5. 获取新闻
        news = self.news_client.get_daily_news(today, limit=20)
        
        # 6. 生成操作建议
        recommendations = self._generate_recommendations(
            market_overview, sectors, news
        )
        
        # 7. 保存到MongoDB
        data = AfterMarketData(
            date=today,
            created_at=datetime.now(),
            market_overview=market_overview,
            stocks=stocks,
            capital_flow=capital_flow,
            sectors=sectors,
            news=news,
            recommendations=recommendations
        )
        self.storage.save(data)
        
        # 8. 发送钉钉通知
        self.notifier.send(data.model_dump())
        
        return f"盘后信息已生成: {today}"
    
    def _generate_recommendations(self, market: Dict, sectors: List, news: Dict) -> Dict:
        """生成明日操作建议"""
        # 基于数据生成建议...
        return {
            "market": {
                "trend": "震荡",
                "position": "5成",
                "risk": "无"
            },
            "sectors": {
                "main": [],
                "avoid": [],
                "rotation": ""
            },
            "stocks": {
                "hold": [],
                "watch": [],
                "avoid": []
            }
        }
```

**Step 2: 创建 __init__.py**

```python
from .job import AfterMarketJob

__all__ = ["AfterMarketJob"]
```

**Step 3: Commit**

```bash
git add case/apps/after-market-service/app/scheduler/
git commit -m "feat: 添加定时任务模块"
```

---

### Task 6: 创建FastAPI Web服务

**Files:**
- Create: `case/apps/after-market-service/app/api/__init__.py`
- Create: `case/apps/after-market-service/app/api/main.py`
- Create: `case/apps/after-market-service/app/api/routes.py`

**Step 1: 创建 main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
import yaml

app = FastAPI(title="盘后信息服务", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Step 2: 创建 routes.py**

```python
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

router = APIRouter()

# 实际从storage获取数据
from ..storage import MongoStorage
from ..config import settings

storage = MongoStorage(
    settings.database.host,
    settings.database.port,
    settings.database.name
)

@router.get("/after-market")
def get_after_market_list(limit: int = 50):
    """获取盘后信息列表"""
    return storage.get_all(limit)

@router.get("/after-market/{date}")
def get_after_market_by_date(date: str):
    """根据日期获取盘后信息"""
    data = storage.get_by_date(date)
    if not data:
        raise HTTPException(status_code=404, detail="Not found")
    return data

@router.delete("/after-market/{date}")
def delete_after_market(date: str):
    """删除盘后信息"""
    count = storage.delete(date)
    if count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": count}

@router.post("/after-market/trigger")
def trigger_job():
    """手动触发采集任务"""
    from ..scheduler import AfterMarketJob
    from ..config import settings
    job = AfterMarketJob(settings.dict())
    return {"result": job.run()}
```

**Step 3: 创建 config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache
import yaml

class Settings(BaseSettings):
    database: dict
    news_api: dict
    dingtalk: dict
    scheduler: dict
    app: dict

@lru_cache()
def get_settings():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    return Settings(**config)

settings = get_settings()
```

**Step 4: Commit**

```bash
git add case/apps/after-market-service/app/api/
git commit -m "feat: 添加FastAPI Web服务"
```

---

### Task 7: 创建Vue3前端

**Files:**
- Create: `case/apps/after-market-service/frontend/`

**Step 1: 创建 package.json**

```json
{
  "name": "after-market-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "axios": "^1.6.0",
    "element-plus": "^2.5.0",
    "@element-plus/icons-vue": "^2.3.0",
    "dayjs": "^1.11.10"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

**Step 2: 创建 vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
```

**Step 3: 创建 src/main.js**

```javascript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.mount('#app')
```

**Step 4: 创建 src/App.vue**

```vue
<template>
  <el-config-provider>
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { ElConfigProvider } from 'element-plus'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>
```

**Step 5: 创建 src/router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import List from '../views/List.vue'
import Detail from '../views/Detail.vue'

const routes = [
  { path: '/', name: 'List', component: List },
  { path: '/detail/:date', name: 'Detail', component: Detail }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

**Step 6: 创建 src/views/List.vue**

```vue
<template>
  <div class="list-page">
    <el-card>
      <template #header>
        <div class="header">
          <h2>盘后信息列表</h2>
          <el-button type="primary" @click="triggerJob">
            <el-icon><Refresh /></el-icon>
            手动采集
          </el-button>
        </div>
      </template>
      
      <el-table :data="list" stripe>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column label="大盘">
          <template #default="{ row }">
            {{ row.market_overview?.indices?.length || 0 }}个指数
          </template>
        </el-table-column>
        <el-table-column label="涨停数" width="100">
          <template #default="{ row }">
            {{ row.market_overview?.limit_up || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.date)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const list = ref([])

const fetchList = async () => {
  const res = await axios.get('/api/after-market')
  list.value = res.data
}

const triggerJob = async () => {
  try {
    await axios.post('/api/after-market/trigger')
    ElMessage.success('采集任务已触发')
    fetchList()
  } catch (e) {
    ElMessage.error('触发失败')
  }
}

const viewDetail = (date) => {
  router.push(`/detail/${date}`)
}

onMounted(fetchList)
</script>

<style scoped>
.list-page {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

**Step 7: 创建 src/views/Detail.vue**

```vue
<template>
  <div class="detail-page">
    <el-page-header @back="goBack" :title="'盘后信息 ' + date" />
    
    <el-tabs v-model="activeTab" class="tabs">
      <el-tab-pane label="大盘概况" name="market">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="上涨家数">
            {{ data.market_overview?.up_count }}
          </el-descriptions-item>
          <el-descriptions-item label="下跌家数">
            {{ data.market_overview?.down_count }}
          </el-descriptions-item>
          <el-descriptions-item label="涨停数">
            {{ data.market_overview?.limit_up }}
          </el-descriptions-item>
          <el-descriptions-item label="跌停数">
            {{ data.market_overview?.limit_down }}
          </el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>
      
      <el-tab-pane label="操作建议" name="recommend">
        <el-card>
          <h3>大盘层面</h3>
          <p>趋势: {{ data.recommendations?.market?.trend }}</p>
          <p>仓位: {{ data.recommendations?.market?.position }}</p>
          <p>风险: {{ data.recommendations?.market?.risk }}</p>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="新闻" name="news">
        <el-table :data="data.news || []">
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="show_time" label="时间" width="180" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const date = route.params.date
const activeTab = ref('market')
const data = ref({})

const fetchDetail = async () => {
  const res = await axios.get(`/api/after-market/${date}`)
  data.value = res.data
}

const goBack = () => router.push('/')

onMounted(fetchDetail)
</script>

<style scoped>
.detail-page {
  padding: 20px;
}
.tabs {
  margin-top: 20px;
}
</style>
```

**Step 8: Commit**

```bash
git add case/apps/after-market-service/frontend/
git commit -m "feat: 添加Vue3前端"
```

---

### Task 8: 创建Docker配置

**Files:**
- Create: `case/apps/after-market-service/Dockerfile`
- Create: `case/apps/after-market-service/docker-compose.yml`

**Step 1: 创建 Dockerfile**

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Step 2: 创建 docker-compose.yml**

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./config.yaml:/app/config.yaml
    environment:
      - PYTHONUNBUFFERED=1

  frontend:
    image: node:20-alpine
    working_dir: /app
    command: sh -c "npm install && npm run dev"
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
```

**Step 3: Commit**

```bash
git add case/apps/after-market-service/Dockerfile
git add case/apps/after-market-service/docker-compose.yml
git commit -m "feat: 添加Docker配置"
```

---

### Task 9: 验证项目

**Step 1: 安装依赖**

```bash
cd case/apps/after-market-service
pip install -r requirements.txt
```

**Step 2: 运行测试**

```bash
cd case/apps/after-market-service
python -c "from app.collector import BaoStockClient; print('collector OK')"
python -c "from app.storage import MongoStorage; print('storage OK')"
python -c "from app.notify import DingTalkNotifier; print('notify OK')"
python -c "from app.api.main import app; print('api OK')"
```

**Step 3: Commit**

```bash
git add .
git commit -m "feat: 完成盘后信息服务项目"
```

---

**Plan complete and saved to `docs/plans/2026-02-26-after-market-service.md`**

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
