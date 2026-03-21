# 分笔记录卖出功能实现计划

> **Goal:** 支持完整的买入/卖出记录，每笔交易独立追踪，自动计算实际盈亏

> **Architecture:** 
> - 交易记录表（transactions）：存储每笔买入/卖出交易
> - 持仓计算：基于交易记录实时计算当前持仓
> - FIFO成本：卖出时按先进先出计算成本

> **Tech Stack:** Python (FastAPI + MongoDB), Vue3 + TypeScript

---

## Chunk 1: 后端 - 交易记录模型

**Files:**
- Modify: `D:\work\datastore\apps\api\app\data_source\adapters\mongodb_adapter.py`

- [ ] **Step 1: 添加交易记录集合**

在 `_init_storage` 方法中添加 `transactions_collection`：

```python
# 第 31 行后添加
self.transactions_collection = self.db.get_collection("transactions")
```

- [ ] **Step 2: 添加 `add_transaction` 方法**

在 `MongoDBAdapter` 类中添加（第 362 行后）：

```python
def add_transaction(
    self, user_id: str, code: str, quantity: float, price: float, transaction_type: str
) -> Optional[str]:
    """添加交易记录（buy/sell）"""
    if not self.storage:
        return None
    try:
        coll = getattr(self.storage, "transactions_collection", None)
        if coll is None:
            coll = self.storage.db.get_collection("transactions")
        now = __import__("datetime").datetime.now()
        doc = {
            "user_id": user_id,
            "code": code,
            "quantity": abs(quantity),
            "price": float(price),
            "type": transaction_type,  # "buy" or "sell"
            "created_at": now,
        }
        res = coll.insert_one(doc)
        return str(res.inserted_id)
    except Exception as e:
        logger.error(f"添加交易记录失败: {e}")
        return None
```

- [ ] **Step 3: 添加 `get_transactions` 方法**

```python
def get_transactions(self, user_id: str, code: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取交易历史"""
    if not self.storage:
        return []
    try:
        coll = getattr(self.storage, "transactions_collection", None)
        if coll is None:
            coll = self.storage.db.get_collection("transactions")
        query = {"user_id": user_id}
        if code:
            query["code"] = code
        cursor = coll.find(query).sort("created_at", -1)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc.get("_id"))
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"获取交易历史失败: {e}")
        return []
```

- [ ] **Step 4: 修改 `upsert_holding` 方法**

替换现有的 `upsert_holding` 方法（第 173-231 行）：

```python
def upsert_holding(
    self, user_id: str, code: str, quantity: float, average_cost: float
) -> Optional[str]:
    """买入/卖出持仓处理"""
    if not self.storage:
        return None
    try:
        # 记录交易
        tx_type = "buy" if quantity > 0 else "sell"
        self.add_transaction(user_id, code, quantity, average_cost, tx_type)
        
        # 计算当前持仓（基于交易记录）
        transactions = self.get_transactions(user_id, code)
        total_buy_qty = sum(t["quantity"] for t in transactions if t["type"] == "buy")
        total_sell_qty = sum(t["quantity"] for t in transactions if t["type"] == "sell")
        current_qty = total_buy_qty - total_sell_qty
        
        coll = getattr(self.storage, "holdings_collection", None)
        if coll is None:
            return None
            
        now = __import__("datetime").datetime.now()
        existing = coll.find_one({"user_id": user_id, "code": code})
        
        if existing:
            coll.update_one(
                {"_id": existing.get("_id")},
                {
                    "$set": {
                        "quantity": current_qty,
                        "average_cost": average_cost,
                        "updated_at": now,
                    }
                },
            )
            return str(existing.get("_id"))
        else:
            doc = {
                "user_id": user_id,
                "code": code,
                "quantity": current_qty,
                "average_cost": float(average_cost),
                "created_at": now,
                "updated_at": now,
            }
            res = coll.insert_one(doc)
            return str(res.inserted_id)
    except Exception as e:
        logger.error(f"Upsert 持仓失败: {e}")
        return None
```

- [ ] **Step 5: 修改 `get_holdings` 方法**

更新查询逻辑（第 137-153 行）：

```python
def get_holdings(self, user_id: str) -> List[Dict[str, Any]]:
    """获取某用户的当前持仓（quantity > 0）"""
    if not self.storage:
        return []
    try:
        coll = getattr(self.storage, "holdings_collection", None)
        if coll is None:
            return []
        cursor = coll.find({"user_id": user_id, "quantity": {"$gt": 0}})
        results = []
        for doc in cursor:
            doc["_id"] = str(doc.get("_id"))
            # 计算成本总额
            doc["total_cost"] = doc.get("quantity", 0) * doc.get("average_cost", 0)
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        return []
```

- [ ] **Step 6: 添加 `calculate_realized_pnl` 方法**

```python
def calculate_realized_pnl(self, user_id: str, code: Optional[str] = None) -> Dict[str, float]:
    """计算已实现盈亏（FIFO）"""
    if not self.storage:
        return {"realized_pnl": 0.0, "total_sell_value": 0.0, "total_sell_cost": 0.0}
    try:
        transactions = self.get_transactions(user_id, code)
        buy_queue = []  # [(quantity, price)]
        
        total_sell_value = 0.0
        total_sell_cost = 0.0
        
        for tx in sorted(transactions, key=lambda x: x["created_at"]):
            if tx["type"] == "buy":
                buy_queue.append((tx["quantity"], tx["price"]))
            else:  # sell
                sell_qty = tx["quantity"]
                sell_price = tx["price"]
                total_sell_value += sell_qty * sell_price
                
                while sell_qty > 0 and buy_queue:
                    buy_qty, buy_price = buy_queue[0]
                    if buy_qty <= sell_qty:
                        # 全部卖出
                        total_sell_cost += buy_qty * buy_price
                        sell_qty -= buy_qty
                        buy_queue.pop(0)
                    else:
                        # 部分卖出
                        total_sell_cost += sell_qty * buy_price
                        buy_queue[0] = (buy_qty - sell_qty, buy_price)
                        sell_qty = 0
        
        realized_pnl = total_sell_value - total_sell_cost
        return {
            "realized_pnl": realized_pnl,
            "total_sell_value": total_sell_value,
            "total_sell_cost": total_sell_cost,
        }
    except Exception as e:
        logger.error(f"计算已实现盈亏失败: {e}")
        return {"realized_pnl": 0.0, "total_sell_value": 0.0, "total_sell_cost": 0.0}
```

---

## Chunk 2: 后端 - API 路由

**Files:**
- Modify: `D:\work\datastore\apps\api\app\api_holdings.py`
- Modify: `D:\work\datastore\apps\api\app\data_source\interface.py`
- Modify: `D:\work\datastore\apps\api\app\data_source\manager.py`

- [ ] **Step 1: 添加交易历史 API**

在 `api_holdings.py` 第 51 行后添加：

```python
@router.get("/transactions/{user_id}")
def get_transactions(
    user_id: str, 
    code: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问"
        )
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")
    return adapter.get_transactions(user_id, code)
```

- [ ] **Step 2: 添加已实现盈亏 API**

```python
@router.get("/pnl/{user_id}")
def get_realized_pnl(
    user_id: str,
    code: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问"
        )
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        raise HTTPException(status_code=500, detail="MongoDB adapter not available")
    return adapter.calculate_realized_pnl(user_id, code)
```

- [ ] **Step 3: 修改 `upsert_holding` API 支持交易类型**

更新 `api_holdings.py` 第 54-76 行：

```python
@router.post("/holdings/{user_id}")
def upsert_holding(
    user_id: str, item: HoldingInput, current_user: str = Depends(get_current_user)
):
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    adapter = _data_manager.get_adapter("mongodb")
    if not adapter:
        return {"holding_id": None, "success": False}
    
    holding_data = {
        "code": item.code,
        "quantity": item.quantity,
        "average_cost": item.average_cost,
    }
    if item.name:
        holding_data["name"] = item.name
    
    holding_id = adapter.upsert_holding(
        user_id, 
        item.code, 
        item.quantity, 
        item.average_cost
    )
    
    return {
        "holding_id": holding_id,
        "success": holding_id is not None,
        "type": "buy" if item.quantity > 0 else "sell",
        "code": item.code,
        "quantity": abs(item.quantity)
    }
```

- [ ] **Step 4: 更新 portfolio API 添加已实现盈亏**

修改 `api_holdings.py` 第 99-113 行：

```python
@router.get("/portfolio/{user_id}")
def portfolio(
    user_id: str,
    _req: Optional[PortfolioRequest] = None,
    current_user: str = Depends(get_current_user),
):
    def price_fetcher(code: str) -> float:
        data = _data_manager.get_realtime_data(code)
        if isinstance(data, dict):
            return float(data.get("price", 0.0) or 0.0)
        return 0.0

    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此持仓"
        )
    
    summary = _data_manager.get_portfolio_summary(user_id, price_fetcher)
    
    # 添加已实现盈亏
    mongodb_adapter = _data_manager.get_adapter("mongodb")
    if mongodb_adapter:
        pnl_data = mongodb_adapter.calculate_realized_pnl(user_id)
        summary["realized_pnl"] = pnl_data.get("realized_pnl", 0.0)
        summary["total_sell_value"] = pnl_data.get("total_sell_value", 0.0)
    
    return summary
```

---

## Chunk 3: 前端 - API 服务

**Files:**
- Modify: `D:\work\datastore\frontend\vue-admin\src\services\api.ts`

- [ ] **Step 1: 添加交易相关 API**

在 `apiHoldings` 对象中添加（第 92 行后）：

```typescript
async getTransactions(userId: string, code?: string) {
  const params = code ? { params: { code } } : {}
  const res = await api.get(`/transactions/${userId}`, params)
  return res.data
},
async getRealizedPnL(userId: string, code?: string) {
  const params = code ? { params: { code } } : {}
  const res = await api.get(`/pnl/${userId}`, params)
  return res.data
}
```

---

## Chunk 4: 前端 - 持仓页面

**Files:**
- Modify: `D:\work\datastore\frontend\vue-admin\src\views\HoldingsView.vue`

- [ ] **Step 1: 添加卖出表单**

在 `add-form-card` 后面添加卖出表单：

```html
<div class="sell-form-card" v-if="showSellForm">
  <h3>卖出持仓</h3>
  <form @submit.prevent="onSellHolding">
    <div class="form-row">
      <div class="input-group">
        <label>股票代码</label>
        <input v-model="sellHolding.code" readonly class="input-code" />
      </div>
      <div class="input-group">
        <label>股票名称</label>
        <input v-model="sellHolding.name" readonly />
      </div>
      <div class="input-group">
        <label>可卖数量</label>
        <input :value="sellHolding.availableQty" readonly />
      </div>
      <div class="input-group">
        <label>卖出数量</label>
        <input 
          v-model.number="sellHolding.quantity" 
          type="number" 
          :max="sellHolding.availableQty"
          min="1"
          required 
          class="input-quantity"
        />
      </div>
      <div class="input-group">
        <label>卖出价格</label>
        <input 
          v-model.number="sellHolding.price" 
          type="number" 
          step="0.01" 
          required 
          class="input-cost"
        />
      </div>
      <button type="submit" :disabled="store.state.loading" class="btn btn-danger">
        确认卖出
      </button>
      <button type="button" @click="showSellForm = false" class="btn btn-secondary">
        取消
      </button>
    </div>
  </form>
</div>
```

- [ ] **Step 2: 添加卖出按钮**

修改表格操作列（第 139-143 行）：

```html
<td>
  <button @click="openSellForm(h)" class="btn btn-warning btn-sm">
    卖出
  </button>
  <button @click="removeHolding(h.code)" class="btn btn-danger btn-sm">
    删除
  </button>
</td>
```

- [ ] **Step 3: 添加卖出表单状态和方法**

在 script 部分添加：

```typescript
const showSellForm = ref(false)
const sellHolding = ref({
  code: '',
  name: '',
  availableQty: 0,
  quantity: 0,
  price: 0
})

function openSellForm(holding: any) {
  sellHolding.value = {
    code: holding.code,
    name: holding.name || holding.code,
    availableQty: holding.quantity,
    quantity: holding.quantity,
    price: holding.average_cost
  }
  showSellForm.value = true
}

async function onSellHolding() {
  if (!sellHolding.value.code || sellHolding.value.quantity <= 0) {
    alert('请填写完整的卖出信息')
    return
  }
  if (sellHolding.value.quantity > sellHolding.value.availableQty) {
    alert('卖出数量不能超过可卖数量')
    return
  }
  try {
    await store.saveHolding(
      userId.value,
      sellHolding.value.code,
      sellHolding.value.name,
      -sellHolding.value.quantity,  // 负数表示卖出
      sellHolding.value.price
    )
    showSellForm.value = false
    alert('卖出成功')
    await fetchHoldings()
  } catch (e: any) {
    alert(e.message || '卖出失败')
  }
}
```

- [ ] **Step 4: 添加卖出表单样式**

在 style 部分添加：

```css
.sell-form-card {
  background: #fef3c7;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.sell-form-card h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #92400e;
}
.btn-warning {
  background: #f59e0b;
  color: white;
}
.btn-warning:hover:not(:disabled) {
  background: #d97706;
}
```

- [ ] **Step 5: 添加已实现盈亏显示**

在组合概览中添加（第 170-175 行后）：

```html
<div class="stat-item">
  <span class="label">已实现盈亏</span>
  <span class="value" :class="portfolioData?.realized_pnl >= 0 ? 'profit' : 'loss'">
    {{ portfolioData?.realized_pnl >= 0 ? '+' : '' }}¥{{ (portfolioData?.realized_pnl || 0).toFixed(2) }}
  </span>
</div>
```

同时修改 `fetchPortfolio` 方法：

```typescript
async function fetchPortfolio() {
  portfolio.value = true
  await store.refreshPortfolio(userId.value)
  // 获取已实现盈亏
  try {
    const pnl = await apiHoldings.getRealizedPnL(userId.value)
    portfolioData.value = { ...store.state, ...pnl }
  } catch (e) {
    portfolioData.value = store.state
  }
}
```

添加 `portfolioData` ref：

```typescript
const portfolioData = ref<any>(null)
```

---

## Chunk 5: 测试验证

- [ ] **Step 1: 测试买入操作**

1. 买入 100 股 SH600000，价格 10.00
2. 验证持仓显示 100 股

- [ ] **Step 2: 测试卖出操作**

1. 卖出 60 股 SH600000，价格 12.00
2. 验证持仓显示 40 股
3. 验证已实现盈亏 = 60 * (12 - 10) = 120

- [ ] **Step 3: 测试全部卖出**

1. 卖出 40 股 SH600000，价格 15.00
2. 验证持仓显示 0 股
3. 验证已实现盈亏 = 120 + 40 * (15 - 10) = 320

---

## 预期结果

- ✅ 买入操作正常
- ✅ 卖出操作正常（部分卖出）
- ✅ 持仓数量正确计算
- ✅ 已实现盈亏正确计算
- ✅ 交易历史可查看
